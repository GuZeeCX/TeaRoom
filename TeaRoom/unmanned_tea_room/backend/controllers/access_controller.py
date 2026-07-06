from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.access_service import AccessService
from utils.response import success_response, error_response, unauthorized_response
from utils.helpers import validate_request_params, error_handler

access_bp = Blueprint('access', __name__, url_prefix='/api/access')

@access_bp.route('/verify-qr', methods=['POST'])
@error_handler
@validate_request_params(['qr_code'])
def verify_qr_code():
    """验证二维码"""
    data = request.get_json()
    return AccessService.verify_qr_code(data['qr_code'])

@access_bp.route('/open-door', methods=['POST'])
@error_handler
@validate_request_params(['order_id', 'room_id', 'access_token'])
def open_door():
    """开门"""
    data = request.get_json()
    return AccessService.open_door(
        data['order_id'],
        data['room_id'],
        data['access_token']
    )

@access_bp.route('/close-door', methods=['POST'])
@error_handler
@validate_request_params(['order_id', 'room_id'])
def close_door():
    """关门"""
    data = request.get_json()
    return AccessService.close_door(data['order_id'], data['room_id'])

@access_bp.route('/records', methods=['GET'])
@error_handler
@jwt_required()
def get_open_records():
    """获取用户的开门记录"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    return AccessService.get_open_records(user_id, page, per_page)

@access_bp.route('/records/room/<int:room_id>', methods=['GET'])
@error_handler
def get_room_open_records(room_id):
    """获取房间的开门记录"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    return AccessService.get_room_open_records(room_id, start_date, end_date)