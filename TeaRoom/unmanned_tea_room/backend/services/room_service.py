from models import db, Room, Order
from utils.helpers import is_room_available
from utils.response import success_response, error_response, not_found_response
from datetime import datetime

class RoomService:
    @staticmethod
    def list_rooms(page=1, per_page=10, search=None, status=None, min_price=None, max_price=None, floor=None):
        """获取房间列表"""
        query = Room.query
        
        # 搜索
        if search:
            query = query.filter(
                (Room.name.like(f'%{search}%')) |
                (Room.description.like(f'%{search}%')) |
                (Room.facilities.like(f'%{search}%'))
            )
        
        # 状态筛选
        if status:
            query = query.filter(Room.status == status)
        
        # 价格范围
        if min_price is not None:
            query = query.filter(Room.price_per_hour >= min_price)
        if max_price is not None:
            query = query.filter(Room.price_per_hour <= max_price)
        
        # 楼层筛选
        if floor:
            query = query.filter(Room.floor == floor)
        
        pagination = query.order_by(Room.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        rooms = [room.to_dict() for room in pagination.items]
        
        return success_response({
            'rooms': rooms,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        })
    
    @staticmethod
    def get_room_detail(room_id):
        """获取房间详情"""
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('房间不存在')
        
        # 获取房间的设施列表
        if room.facilities:
            room_dict = room.to_dict()
            room_dict['facilities'] = [f.strip() for f in room.facilities.split(',')]
            return success_response(room_dict)
        
        return success_response(room.to_dict())
    
    @staticmethod
    def create_room(data):
        """创建房间"""
        # 检查房间名称是否已存在
        if Room.query.filter_by(name=data['name']).first():
            return error_response(400, '房间名称已存在')
        
        room = Room(
            name=data['name'],
            description=data.get('description'),
            capacity=data.get('capacity', 4),
            price_per_hour=data['price_per_hour'],
            image_url=data.get('image_url'),
            facilities=data.get('facilities'),
            status=data.get('status', 'available'),
            floor=data.get('floor', 1)
        )
        
        try:
            db.session.add(room)
            db.session.commit()
            return success_response(room.to_dict(), '房间创建成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'房间创建失败: {str(e)}')
    
    @staticmethod
    def update_room(room_id, data):
        """更新房间信息"""
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('房间不存在')
        
        # 检查房间名称是否已被其他房间使用
        if 'name' in data:
            existing_room = Room.query.filter(
                Room.name == data['name'],
                Room.id != room_id
            ).first()
            if existing_room:
                return error_response(400, '房间名称已存在')
            room.name = data['name']
        
        # 更新其他信息
        if 'description' in data:
            room.description = data['description']
        if 'capacity' in data:
            room.capacity = data['capacity']
        if 'price_per_hour' in data:
            room.price_per_hour = data['price_per_hour']
        if 'image_url' in data:
            room.image_url = data['image_url']
        if 'facilities' in data:
            room.facilities = data['facilities']
        if 'status' in data:
            room.status = data['status']
        if 'floor' in data:
            room.floor = data['floor']
        
        try:
            db.session.commit()
            return success_response(room.to_dict(), '房间更新成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'房间更新失败: {str(e)}')
    
    @staticmethod
    def delete_room(room_id):
        """删除房间"""
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('房间不存在')
        
        # 检查是否有未完成的订单
        active_orders = Order.query.filter(
            Order.room_id == room_id,
            Order.status.in_(['pending', 'confirmed', 'in_use'])
        ).count()
        
        if active_orders > 0:
            return error_response(400, '该房间有未完成的订单，无法删除')
        
        try:
            db.session.delete(room)
            db.session.commit()
            return success_response(None, '房间删除成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'房间删除失败: {str(e)}')
    
    @staticmethod
    def update_room_status(room_id, status):
        """更新房间状态"""
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('房间不存在')
        
        if status not in ['available', 'occupied', 'maintenance']:
            return error_response(400, '无效的房间状态')
        
        room.status = status
        
        try:
            db.session.commit()
            return success_response({'status': status}, '房间状态更新成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'房间状态更新失败: {str(e)}')
    
    @staticmethod
    def check_room_availability(room_id, start_time, end_time, exclude_order_id=None):
        """检查房间可用性"""
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('房间不存在')
        
        if room.status != 'available':
            return error_response(400, '房间当前不可用')
        
        available = is_room_available(room_id, start_time, end_time, exclude_order_id)
        if not available:
            return error_response(400, '该时间段房间已被预约')
        
        return success_response({'available': True}, '房间可用')
    
    @staticmethod
    def get_room_status(room_id):
        """获取房间状态"""
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('房间不存在')
        
        return success_response({'status': room.status, 'name': room.name})
    
    @staticmethod
    def get_available_rooms(start_time, end_time):
        """获取指定时间段内可用的房间"""
        all_rooms = Room.query.filter_by(status='available').all()
        available_rooms = []
        
        for room in all_rooms:
            if is_room_available(room.id, start_time, end_time):
                available_rooms.append(room.to_dict())
        
        return success_response({'rooms': available_rooms})
    
    @staticmethod
    def get_room_statistics():
        """获取房间统计信息"""
        total_rooms = Room.query.count()
        available_rooms = Room.query.filter_by(status='available').count()
        occupied_rooms = Room.query.filter_by(status='occupied').count()
        maintenance_rooms = Room.query.filter_by(status='maintenance').count()
        
        return success_response({
            'total': total_rooms,
            'available': available_rooms,
            'occupied': occupied_rooms,
            'maintenance': maintenance_rooms
        })