from models import db, Booking, Room, User, Order
from utils.helpers import generate_booking_no, generate_order_no, calculate_order_amount, validate_time_range
from utils.response import success_response, error_response, not_found_response
from datetime import datetime, timedelta

class BookingService:
    # 茶叶价格配置 - 9种精选茶叶 + 自带茶叶选项
    TEA_PRICES = {
        '自带茶叶': 0.0,           # 用户自带茶叶，不收费
        '西湖龙井': 15.0,          # 中国十大名茶之首，清香甘醇
        '安溪铁观音': 12.0,        # 乌龙茶代表，兰花香气
        '武夷大红袍': 18.0,        # 岩茶之王，醇厚回甘
        '云南普洱': 16.0,          # 后发酵茶，陈香浓郁
        '洞庭碧螺春': 14.0,        # 绿茶珍品，花果香气
        '黄山毛峰': 13.0,          # 徽茶代表，清香持久
        '君山银针': 20.0,          # 黄茶极品，金镶玉色
        '福鼎白茶': 10.0,          # 微发酵茶，清淡甘甜
        '正山小种': 17.0           # 红茶鼻祖，松烟香气
    }
    
    # 套餐配置
    PACKAGE_CONFIG = {
        '2小时特惠': {'hours': 2, 'discount': 0.8},
        '4小时畅饮': {'hours': 4, 'discount': 0.7},
        '全天套餐': {'fixed_price': 298.0}
    }
    
    @staticmethod
    def create_booking(user_id, data):
        """创建预约"""
        # 验证参数
        room_id = data.get('room_id')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        duration_hours = data.get('duration_hours')
        tea_type = data.get('tea_type', '默认免费茶')  # 茶叶类型，默认为默认免费茶
        package_type = data.get('package_type', '按小时计费')  # 套餐类型，默认为按小时计费
        
        if not room_id or not start_time or not end_time:
            return error_response(400, '缺少必要参数')
        
        # 转换时间格式
        try:
            start_time = datetime.fromisoformat(start_time)
            end_time = datetime.fromisoformat(end_time)
        except:
            return error_response(400, '时间格式错误')
        
        # 验证时间范围
        if not validate_time_range(start_time, end_time):
            return error_response(400, '时间范围无效')
        
        # 验证房间是否存在
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('房间不存在')
        
        # 验证房间是否可用
        if room.status != 'available':
            return error_response(400, '房间当前不可用')
        
        # 检查是否有冲突的预约
        conflicting_bookings = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.status == 'confirmed',
            Booking.start_time < end_time,
            Booking.end_time > start_time
        ).count()
        
        if conflicting_bookings > 0:
            return error_response(400, '该时间段已被预约')
        
        # 计算时长
        if not duration_hours:
            duration_hours = (end_time - start_time).total_seconds() / 3600
        duration_hours = round(duration_hours, 2)
        
        # 计算茶叶加价
        tea_price = BookingService.TEA_PRICES.get(tea_type, 0.0)
        
        # 计算套餐价格
        if package_type == '按小时计费':
            # 按小时计费
            base_amount = calculate_order_amount(room.price_per_hour, duration_hours)
        else:
            # 套餐计费
            package_config = BookingService.PACKAGE_CONFIG.get(package_type)
            if not package_config:
                return error_response(400, '无效的套餐类型')
            
            if 'fixed_price' in package_config:
                # 固定价格套餐
                base_amount = package_config['fixed_price']
            else:
                # 折扣套餐
                package_hours = package_config['hours']
                discount = package_config['discount']
                if duration_hours != package_hours:
                    return error_response(400, f'{package_type}必须预约{package_hours}小时')
                base_amount = calculate_order_amount(room.price_per_hour, package_hours) * discount
        
        # 计算总金额
        estimated_amount = base_amount + tea_price
        
        # 获取用户信息
        user = User.query.get(user_id)
        if not user:
            return not_found_response('用户不存在')
        
        # 检查余额
        if user.balance < estimated_amount:
            return error_response(400, '余额不足，请先充值')
        
        # 开始事务
        try:
            # 创建预约
            booking = Booking(
                booking_no=generate_booking_no(),
                user_id=user_id,
                room_id=room_id,
                booking_date=start_time.date(),
                start_time=start_time,
                end_time=end_time,
                duration_hours=duration_hours,
                estimated_amount=estimated_amount,
                status='confirmed',
                tea_type=tea_type,
                tea_price=tea_price,
                package_type=package_type
            )
            
            # 创建订单
            order = Order(
                order_no=generate_order_no(),
                user_id=user_id,
                room_id=room_id,
                start_time=start_time,
                end_time=end_time,
                duration_hours=duration_hours,
                total_amount=estimated_amount,
                status='completed',
                payment_status='paid',
                tea_type=tea_type,
                tea_price=tea_price,
                package_type=package_type
            )
            
            # 扣减用户余额
            user.balance -= estimated_amount
            
            # 添加到数据库
            db.session.add(booking)
            db.session.add(order)
            db.session.commit()
            
            return success_response(booking.to_dict(), '预约成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'预约失败: {str(e)}')
    
    @staticmethod
    def cancel_booking(booking_id, user_id):
        """取消预约"""
        booking = Booking.query.get(booking_id)
        if not booking:
            return not_found_response('预约不存在')
        
        # 验证预约所属用户
        if booking.user_id != user_id:
            return error_response(403, '无权操作此预约')
        
        # 验证预约状态
        if booking.status != 'confirmed':
            return error_response(400, '只能取消已确认的预约')
        
        # 验证是否可以取消（距离开始时间至少1小时）
        if datetime.now() >= booking.start_time - timedelta(hours=1):
            return error_response(400, '距离预约开始时间不足1小时，无法取消')
        
        # 获取用户信息
        user = User.query.get(user_id)
        if not user:
            return not_found_response('用户不存在')
        
        # 开始事务
        try:
            # 更新预约状态
            booking.status = 'cancelled'
            
            # 恢复用户余额
            user.balance += booking.estimated_amount
            
            # 提交事务
            db.session.commit()
            
            return success_response({
                'refund_amount': booking.estimated_amount
            }, '预约取消成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'预约取消失败: {str(e)}')
    
    @staticmethod
    def get_booking_detail(booking_id, user_id):
        """获取预约详情"""
        booking = Booking.query.get(booking_id)
        if not booking:
            return not_found_response('预约不存在')
        
        # 验证预约所属用户
        if booking.user_id != user_id:
            return error_response(403, '无权查看此预约')
        
        return success_response(booking.to_dict())
    
    @staticmethod
    def get_user_bookings(user_id, status=None, page=1, per_page=10):
        """获取用户的预约列表"""
        query = Booking.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        pagination = query.order_by(Booking.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        bookings = [booking.to_dict() for booking in pagination.items]
        
        return success_response({
            'bookings': bookings,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        })
    
    @staticmethod
    def get_room_bookings(room_id, date=None):
        """获取房间的预约列表"""
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('房间不存在')
        
        query = Booking.query.filter_by(room_id=room_id, status='confirmed')
        
        if date:
            try:
                date = datetime.fromisoformat(date).date()
                query = query.filter_by(booking_date=date)
            except:
                return error_response(400, '日期格式错误')
        
        bookings = [booking.to_dict() for booking in query.all()]
        
        return success_response({'bookings': bookings})
    
    @staticmethod
    def verify_booking(booking_id):
        """验证预约"""
        booking = Booking.query.get(booking_id)
        if not booking:
            return not_found_response('预约不存在')
        
        # 验证预约状态
        if booking.status != 'confirmed':
            return error_response(400, '预约状态无效')
        
        # 验证预约时间
        now = datetime.now()
        if now < booking.start_time - datetime.timedelta(minutes=15):
            return error_response(400, '预约尚未开始')
        if now > booking.end_time:
            return error_response(400, '预约已结束')
        
        return success_response({
            'booking': booking.to_dict(),
            'valid': True
        }, '预约验证成功')
    
    @staticmethod
    def update_booking_status(booking_id, status):
        """更新预约状态"""
        booking = Booking.query.get(booking_id)
        if not booking:
            return not_found_response('预约不存在')
        
        if status not in ['confirmed', 'cancelled', 'completed']:
            return error_response(400, '无效的预约状态')
        
        booking.status = status
        
        try:
            db.session.commit()
            return success_response({'status': status}, '预约状态更新成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'预约状态更新失败: {str(e)}')
    
    @staticmethod
    def get_booking_statistics(start_date=None, end_date=None):
        """获取预约统计信息"""
        query = Booking.query.filter_by(status='confirmed')
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date)
                query = query.filter(Booking.created_at >= start_date)
            except:
                return error_response(400, '开始日期格式错误')
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date)
                query = query.filter(Booking.created_at <= end_date)
            except:
                return error_response(400, '结束日期格式错误')
        
        total_bookings = query.count()
        total_amount = db.session.query(
            db.func.sum(Booking.estimated_amount)
        ).filter(
            Booking.status == 'confirmed'
        ).scalar() or 0
        
        return success_response({
            'total_bookings': total_bookings,
            'total_amount': total_amount
        })