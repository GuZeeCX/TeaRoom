from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.room_service import RoomService
from utils.response import success_response, error_response, unauthorized_response
from utils.helpers import validate_request_params, error_handler

room_bp = Blueprint('room', __name__, url_prefix='/api/rooms')

@room_bp.route('/', methods=['GET'])
@error_handler
def list_rooms():
    """获取房间列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search')
    status = request.args.get('status')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    floor = request.args.get('floor', type=int)
    
    return RoomService.list_rooms(page, per_page, search, status, min_price, max_price, floor)

@room_bp.route('/<int:room_id>', methods=['GET'])
@error_handler
def get_room_detail(room_id):
    """获取房间详情"""
    return RoomService.get_room_detail(room_id)

@room_bp.route('/', methods=['POST'])
@error_handler
@jwt_required()
def create_room():
    """创建房间"""
    data = request.get_json()
    return RoomService.create_room(data)

@room_bp.route('/<int:room_id>', methods=['PUT'])
@error_handler
@jwt_required()
def update_room(room_id):
    """更新房间信息"""
    data = request.get_json()
    return RoomService.update_room(room_id, data)

@room_bp.route('/<int:room_id>', methods=['DELETE'])
@error_handler
@jwt_required()
def delete_room(room_id):
    """删除房间"""
    return RoomService.delete_room(room_id)

@room_bp.route('/<int:room_id>/status', methods=['PUT'])
@error_handler
@jwt_required()
def update_room_status(room_id):
    """更新房间状态"""
    data = request.get_json()
    if 'status' not in data:
        return error_response(400, '缺少状态参数')
    return RoomService.update_room_status(room_id, data['status'])

@room_bp.route('/<int:room_id>/status', methods=['GET'])
@error_handler
def get_room_status(room_id):
    """获取房间状态"""
    return RoomService.get_room_status(room_id)

@room_bp.route('/<int:room_id>/availability', methods=['POST'])
@error_handler
@validate_request_params(['start_time', 'end_time'])
def check_room_availability(room_id):
    """检查房间可用性"""
    data = request.get_json()
    try:
        from datetime import datetime
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
    except:
        return error_response(400, '时间格式错误')
    
    exclude_order_id = data.get('exclude_order_id')
    return RoomService.check_room_availability(room_id, start_time, end_time, exclude_order_id)

@room_bp.route('/available', methods=['POST'])
@error_handler
@validate_request_params(['start_time', 'end_time'])
def get_available_rooms():
    """获取指定时间段内可用的房间"""
    data = request.get_json()
    try:
        from datetime import datetime
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
    except:
        return error_response(400, '时间格式错误')
    
    return RoomService.get_available_rooms(start_time, end_time)

@room_bp.route('/statistics', methods=['GET'])
@error_handler
def get_room_statistics():
    """获取房间统计信息"""
    return RoomService.get_room_statistics()