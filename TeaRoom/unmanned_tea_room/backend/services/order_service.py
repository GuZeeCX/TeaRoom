from models import db, Order, Room, User
from utils.helpers import generate_order_no, calculate_order_amount, validate_time_range, is_room_available
from utils.response import success_response, error_response, not_found_response
from datetime import datetime, timedelta

class OrderService:
    @staticmethod
    def create_order(user_id, data):
        """创建订单"""
        # 验证参数
        room_id = data.get('room_id')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        duration_hours = data.get('duration_hours')
        payment_method = data.get('payment_method', 'wechat')
        
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
        
        # 检查是否有冲突的订单
        if not is_room_available(room_id, start_time, end_time):
            return error_response(400, '该时间段房间已被预约')
        
        # 验证用户是否存在
        user = User.query.get(user_id)
        if not user:
            return not_found_response('用户不存在')
        
        # 计算订单金额
        if not duration_hours:
            duration_hours = (end_time - start_time).total_seconds() / 3600
        total_amount = calculate_order_amount(room.price_per_hour, duration_hours)
        
        # 验证用户余额
        if user.balance < total_amount:
            return error_response(400, '用户余额不足')
        
        # 创建订单
        order = Order(
            order_no=generate_order_no(),
            user_id=user_id,
            room_id=room_id,
            start_time=start_time,
            end_time=end_time,
            duration_hours=round(duration_hours, 2),
            total_amount=total_amount,
            status='pending',
            payment_status='unpaid',
            payment_method=payment_method
        )
        
        try:
            db.session.add(order)
            db.session.commit()
            return success_response(order.to_dict(), '订单创建成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'订单创建失败: {str(e)}')
    
    @staticmethod
    def pay_order(order_id, user_id, payment_data):
        """支付订单"""
        order = Order.query.get(order_id)
        if not order:
            return not_found_response('订单不存在')
        
        # 验证订单所属用户
        if order.user_id != user_id:
            return error_response(403, '无权操作此订单')
        
        # 验证订单状态
        if order.status != 'pending':
            return error_response(400, '订单状态无效')
        
        # 验证支付状态
        if order.payment_status != 'unpaid':
            return error_response(400, '订单已支付')
        
        # 模拟支付
        # 实际项目中应该调用支付API
        
        # 扣除用户余额
        user = User.query.get(user_id)
        if user.balance < order.total_amount:
            return error_response(400, '用户余额不足')
        
        user.balance -= order.total_amount
        order.payment_status = 'paid'
        order.status = 'confirmed'
        
        try:
            db.session.commit()
            return success_response(order.to_dict(), '支付成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'支付失败: {str(e)}')
    
    @staticmethod
    def settle_order(order_id, user_id):
        """结算订单"""
        order = Order.query.get(order_id)
        if not order:
            return not_found_response('订单不存在')
        
        # 验证订单所属用户
        if order.user_id != user_id:
            return error_response(403, '无权操作此订单')
        
        # 验证订单状态
        if order.status != 'in_use':
            return error_response(400, '订单状态无效')
        
        # 更新订单状态
        order.status = 'completed'
        order.check_out_time = datetime.now()
        
        # 更新房间状态
        room = Room.query.get(order.room_id)
        room.status = 'available'
        
        try:
            db.session.commit()
            return success_response(order.to_dict(), '结算成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'结算失败: {str(e)}')
    
    @staticmethod
    def renew_order(order_id, user_id, extra_hours):
        """续费订单"""
        order = Order.query.get(order_id)
        if not order:
            return not_found_response('订单不存在')
        
        # 验证订单所属用户
        if order.user_id != user_id:
            return error_response(403, '无权操作此订单')
        
        # 验证订单状态
        if order.status != 'in_use':
            return error_response(400, '订单状态无效')
        
        # 验证续费时长
        if extra_hours <= 0:
            return error_response(400, '续费时长必须大于0')
        
        # 获取房间信息
        room = Room.query.get(order.room_id)
        if not room:
            return not_found_response('房间不存在')
        
        # 计算续费金额
        extra_amount = calculate_order_amount(room.price_per_hour, extra_hours)
        
        # 验证用户余额
        user = User.query.get(user_id)
        if user.balance < extra_amount:
            return error_response(400, '用户余额不足')
        
        # 更新订单信息
        original_end_time = order.end_time
        new_end_time = original_end_time + timedelta(hours=extra_hours)
        
        # 检查续费时间段是否可用
        if not is_room_available(order.room_id, original_end_time, new_end_time, order.id):
            return error_response(400, '续费时间段房间已被预约')
        
        order.end_time = new_end_time
        order.duration_hours += extra_hours
        order.total_amount += extra_amount
        
        # 扣除用户余额
        user.balance -= extra_amount
        
        try:
            db.session.commit()
            return success_response(order.to_dict(), '续费成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'续费失败: {str(e)}')
    
    @staticmethod
    def get_order_detail(order_id, user_id):
        """获取订单详情"""
        order = Order.query.get(order_id)
        if not order:
            return not_found_response('订单不存在')
        
        # 验证订单所属用户
        if order.user_id != user_id:
            return error_response(403, '无权查看此订单')
        
        return success_response(order.to_dict())
    
    @staticmethod
    def get_user_orders(user_id, status=None, page=1, per_page=10):
        """获取用户的订单列表"""
        query = Order.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        pagination = query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        orders = [order.to_dict() for order in pagination.items]
        
        return success_response({
            'orders': orders,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        })
    
    @staticmethod
    def get_room_orders(room_id, status=None, start_date=None, end_date=None):
        """获取房间的订单列表"""
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('房间不存在')
        
        query = Order.query.filter_by(room_id=room_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date)
                query = query.filter(Order.start_time >= start_date)
            except:
                return error_response(400, '开始日期格式错误')
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date)
                query = query.filter(Order.end_time <= end_date)
            except:
                return error_response(400, '结束日期格式错误')
        
        orders = [order.to_dict() for order in query.order_by(Order.created_at.desc()).all()]
        
        return success_response({'orders': orders})
    
    @staticmethod
    def cancel_order(order_id, user_id):
        """取消订单"""
        order = Order.query.get(order_id)
        if not order:
            return not_found_response('订单不存在')
        
        # 验证订单所属用户
        if order.user_id != user_id:
            return error_response(403, '无权操作此订单')
        
        # 验证订单状态
        if order.status not in ['pending', 'confirmed']:
            return error_response(400, '订单状态无效')
        
        # 验证是否可以取消
        if order.status == 'confirmed' and datetime.now() >= order.start_time:
            return error_response(400, '订单已开始，无法取消')
        
        # 退还用户余额
        if order.payment_status == 'paid':
            user = User.query.get(user_id)
            user.balance += order.total_amount
        
        order.status = 'cancelled'
        
        try:
            db.session.commit()
            return success_response(None, '订单取消成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'订单取消失败: {str(e)}')
    
    @staticmethod
    def update_order_status(order_id, status):
        """更新订单状态"""
        order = Order.query.get(order_id)
        if not order:
            return not_found_response('订单不存在')
        
        if status not in ['pending', 'confirmed', 'in_use', 'completed', 'cancelled']:
            return error_response(400, '无效的订单状态')
        
        # 如果状态变为in_use，记录入住时间
        if status == 'in_use' and order.status != 'in_use':
            order.check_in_time = datetime.now()
            # 更新房间状态为occupied
            room = Room.query.get(order.room_id)
            room.status = 'occupied'
        
        # 如果状态变为completed，记录退房时间
        if status == 'completed' and order.status != 'completed':
            order.check_out_time = datetime.now()
            # 更新房间状态为available
            room = Room.query.get(order.room_id)
            room.status = 'available'
        
        order.status = status
        
        try:
            db.session.commit()
            return success_response({'status': status}, '订单状态更新成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'订单状态更新失败: {str(e)}')