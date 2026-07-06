from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.order_service import OrderService
from utils.response import success_response, error_response, unauthorized_response
from utils.helpers import validate_request_params, error_handler

order_bp = Blueprint('order', __name__, url_prefix='/api/orders')

@order_bp.route('/', methods=['POST'])
@error_handler
@jwt_required()
@validate_request_params(['room_id', 'start_time', 'end_time'])
def create_order():
    """创建订单"""
    user_id = get_jwt_identity()
    data = request.get_json()
    return OrderService.create_order(user_id, data)

@order_bp.route('/<int:order_id>/pay', methods=['POST'])
@error_handler
@jwt_required()
def pay_order(order_id):
    """支付订单"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    return OrderService.pay_order(order_id, user_id, data)

@order_bp.route('/<int:order_id>/settle', methods=['POST'])
@error_handler
@jwt_required()
def settle_order(order_id):
    """结算订单"""
    user_id = get_jwt_identity()
    return OrderService.settle_order(order_id, user_id)

@order_bp.route('/<int:order_id>/renew', methods=['POST'])
@error_handler
@jwt_required()
@validate_request_params(['extra_hours'])
def renew_order(order_id):
    """续费订单"""
    user_id = get_jwt_identity()
    data = request.get_json()
    return OrderService.renew_order(order_id, user_id, data['extra_hours'])

@order_bp.route('/<int:order_id>', methods=['GET'])
@error_handler
@jwt_required()
def get_order_detail(order_id):
    """获取订单详情"""
    user_id = get_jwt_identity()
    return OrderService.get_order_detail(order_id, user_id)

@order_bp.route('/my', methods=['GET'])
@error_handler
@jwt_required()
def get_user_orders():
    """获取用户的订单列表"""
    user_id = get_jwt_identity()
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    return OrderService.get_user_orders(user_id, status, page, per_page)

@order_bp.route('/room/<int:room_id>', methods=['GET'])
@error_handler
def get_room_orders(room_id):
    """获取房间的订单列表"""
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    return OrderService.get_room_orders(room_id, status, start_date, end_date)

@order_bp.route('/<int:order_id>', methods=['DELETE'])
@error_handler
@jwt_required()
def cancel_order(order_id):
    """取消订单"""
    user_id = get_jwt_identity()
    return OrderService.cancel_order(order_id, user_id)

@order_bp.route('/<int:order_id>/status', methods=['PUT'])
@error_handler
@jwt_required()
def update_order_status(order_id):
    """更新订单状态"""
    data = request.get_json()
    if 'status' not in data:
        return error_response(400, '缺少状态参数')
    return OrderService.update_order_status(order_id, data['status'])