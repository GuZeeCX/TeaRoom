from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.booking_service import BookingService
from utils.response import success_response, error_response, unauthorized_response
from utils.helpers import validate_request_params, error_handler

booking_bp = Blueprint('booking', __name__, url_prefix='/api/bookings')

@booking_bp.route('/', methods=['POST'])
@error_handler
@jwt_required()
@validate_request_params(['room_id', 'start_time', 'end_time'])
def create_booking():
    """创建预约"""
    user_id = get_jwt_identity()
    data = request.get_json()
    return BookingService.create_booking(user_id, data)

@booking_bp.route('/<int:booking_id>', methods=['DELETE'])
@error_handler
@jwt_required()
def cancel_booking(booking_id):
    """取消预约"""
    user_id = get_jwt_identity()
    return BookingService.cancel_booking(booking_id, user_id)

@booking_bp.route('/<int:booking_id>', methods=['GET'])
@error_handler
@jwt_required()
def get_booking_detail(booking_id):
    """获取预约详情"""
    user_id = get_jwt_identity()
    return BookingService.get_booking_detail(booking_id, user_id)

@booking_bp.route('/my', methods=['GET'])
@error_handler
@jwt_required()
def get_user_bookings():
    """获取用户的预约列表"""
    user_id = get_jwt_identity()
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    return BookingService.get_user_bookings(user_id, status, page, per_page)

@booking_bp.route('/room/<int:room_id>', methods=['GET'])
@error_handler
def get_room_bookings(room_id):
    """获取房间的预约列表"""
    date = request.args.get('date')
    return BookingService.get_room_bookings(room_id, date)

@booking_bp.route('/<int:booking_id>/verify', methods=['GET'])
@error_handler
def verify_booking(booking_id):
    """验证预约"""
    return BookingService.verify_booking(booking_id)

@booking_bp.route('/<int:booking_id>/status', methods=['PUT'])
@error_handler
@jwt_required()
def update_booking_status(booking_id):
    """更新预约状态"""
    data = request.get_json()
    if 'status' not in data:
        return error_response(400, '缺少状态参数')
    return BookingService.update_booking_status(booking_id, data['status'])

@booking_bp.route('/statistics', methods=['GET'])
@error_handler
def get_booking_statistics():
    """获取预约统计信息"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    return BookingService.get_booking_statistics(start_date, end_date)