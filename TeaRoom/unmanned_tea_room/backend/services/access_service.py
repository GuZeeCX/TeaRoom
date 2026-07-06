from models import db, Order, Room, User
from utils.helpers import generate_secure_token, format_datetime
from utils.response import success_response, error_response, not_found_response
from datetime import datetime

class AccessService:
    @staticmethod
    def verify_qr_code(qr_code_content):
        """验证二维码"""
        # 解析二维码内容
        # 格式: tearoom://open?order_id=1&room_id=2
        try:
            if not qr_code_content.startswith('tearoom://open?'):
                return error_response(400, '无效的二维码')
            
            # 解析参数
            params = qr_code_content.split('?')[1].split('&')
            params_dict = {}
            for param in params:
                key, value = param.split('=')
                params_dict[key] = value
            
            order_id = params_dict.get('order_id')
            room_id = params_dict.get('room_id')
            
            if not order_id or not room_id:
                return error_response(400, '二维码参数不完整')
            
            # 验证订单
            order = Order.query.get(order_id)
            if not order:
                return not_found_response('订单不存在')
            
            # 验证房间
            room = Room.query.get(room_id)
            if not room:
                return not_found_response('房间不存在')
            
            # 验证订单与房间的关系
            if order.room_id != int(room_id):
                return error_response(400, '订单与房间不匹配')
            
            # 验证订单状态
            if order.status not in ['confirmed', 'in_use']:
                return error_response(400, '订单状态无效')
            
            # 验证时间
            now = datetime.now()
            if now < order.start_time - datetime.timedelta(minutes=15):
                return error_response(400, '订单尚未开始')
            if now > order.end_time:
                return error_response(400, '订单已结束')
            
            # 生成开门令牌
            access_token = generate_secure_token()
            
            # 记录开门记录（这里可以创建一个开门记录表）
            # 简化处理，直接返回成功
            
            return success_response({
                'order': order.to_dict(),
                'room': room.to_dict(),
                'access_token': access_token
            }, '二维码验证成功')
            
        except Exception as e:
            return error_response(400, f'二维码解析失败: {str(e)}')
    
    @staticmethod
    def open_door(order_id, room_id, access_token):
        """开门"""
        # 验证订单
        order = Order.query.get(order_id)
        if not order:
            return not_found_response('订单不存在')
        
        # 验证房间
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('房间不存在')
        
        # 验证订单与房间的关系
        if order.room_id != room_id:
            return error_response(400, '订单与房间不匹配')
        
        # 验证订单状态
        if order.status not in ['confirmed', 'in_use']:
            return error_response(400, '订单状态无效')
        
        # 验证时间
        now = datetime.now()
        if now < order.start_time - datetime.timedelta(minutes=15):
            return error_response(400, '订单尚未开始')
        if now > order.end_time:
            return error_response(400, '订单已结束')
        
        # 验证访问令牌
        # 实际项目中应该验证令牌的有效性
        
        # 如果订单状态是confirmed，更新为in_use
        if order.status == 'confirmed':
            order.status = 'in_use'
            order.check_in_time = now
            room.status = 'occupied'
        
        # 记录开门记录
        # 这里可以创建一个开门记录表
        open_record = {
            'order_id': order_id,
            'room_id': room_id,
            'user_id': order.user_id,
            'open_time': now,
            'status': 'success'
        }
        
        try:
            db.session.commit()
            return success_response({
                'open_record': open_record,
                'message': '开门成功'
            }, '开门成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'开门失败: {str(e)}')
    
    @staticmethod
    def get_open_records(user_id, page=1, per_page=10):
        """获取用户的开门记录"""
        # 这里应该从开门记录表中查询
        # 简化处理，返回模拟数据
        records = []
        
        # 获取用户的订单
        orders = Order.query.filter_by(user_id=user_id).all()
        
        for order in orders:
            if order.check_in_time:
                records.append({
                    'id': len(records) + 1,
                    'order_id': order.id,
                    'order_no': order.order_no,
                    'room_id': order.room_id,
                    'room_name': order.room.name if order.room else '未知房间',
                    'open_time': format_datetime(order.check_in_time),
                    'status': 'success'
                })
        
        # 分页
        start = (page - 1) * per_page
        end = start + per_page
        paginated_records = records[start:end]
        
        return success_response({
            'records': paginated_records,
            'total': len(records),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(records) + per_page - 1) // per_page
        })
    
    @staticmethod
    def get_room_open_records(room_id, start_date=None, end_date=None):
        """获取房间的开门记录"""
        # 验证房间
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('房间不存在')
        
        # 这里应该从开门记录表中查询
        # 简化处理，返回模拟数据
        records = []
        
        # 获取房间的订单
        orders = Order.query.filter_by(room_id=room_id).all()
        
        for order in orders:
            if order.check_in_time:
                # 筛选日期
                if start_date:
                    start_date = datetime.fromisoformat(start_date)
                    if order.check_in_time.date() < start_date.date():
                        continue
                if end_date:
                    end_date = datetime.fromisoformat(end_date)
                    if order.check_in_time.date() > end_date.date():
                        continue
                
                records.append({
                    'id': len(records) + 1,
                    'order_id': order.id,
                    'order_no': order.order_no,
                    'user_id': order.user_id,
                    'user_name': order.user.real_name if order.user else '未知用户',
                    'open_time': format_datetime(order.check_in_time),
                    'status': 'success'
                })
        
        return success_response({'records': records})
    
    @staticmethod
    def close_door(order_id, room_id):
        """关门"""
        # 验证订单
        order = Order.query.get(order_id)
        if not order:
            return not_found_response('订单不存在')
        
        # 验证房间
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('房间不存在')
        
        # 验证订单与房间的关系
        if order.room_id != room_id:
            return error_response(400, '订单与房间不匹配')
        
        # 验证订单状态
        if order.status != 'in_use':
            return error_response(400, '订单状态无效')
        
        # 更新房间状态
        room.status = 'available'
        
        # 记录关门时间
        order.check_out_time = datetime.now()
        order.status = 'completed'
        
        try:
            db.session.commit()
            return success_response(None, '关门成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'关门失败: {str(e)}')