from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from services.user_service import UserService
from utils.response import success_response, error_response, unauthorized_response
from utils.helpers import validate_request_params, error_handler

user_bp = Blueprint('user', __name__, url_prefix='/api/users')

@user_bp.route('/register', methods=['POST'])
@error_handler
@validate_request_params(['username', 'password', 'phone', 'real_name'])
def register():
    """用户注册"""
    data = request.get_json()
    return UserService.register(data)

@user_bp.route('/login', methods=['POST'])
@error_handler
@validate_request_params(['identifier', 'password'])
def login():
    """用户登录"""
    data = request.get_json()
    user = UserService.login(data['identifier'], data['password'])
    
    if isinstance(user, tuple):
        return user
    
    # 生成token
    access_token = create_access_token(identity=user.id)
    
    return success_response({
        'access_token': access_token,
        'user': user.to_dict()
    }, '登录成功')

@user_bp.route('/me', methods=['GET'])
@error_handler
@jwt_required()
def get_current_user():
    """获取当前用户信息"""
    user_id = get_jwt_identity()
    return UserService.get_user_by_id(user_id)

@user_bp.route('/me', methods=['PUT'])
@error_handler
@jwt_required()
def update_profile():
    """更新用户信息"""
    user_id = get_jwt_identity()
    data = request.get_json()
    return UserService.update_profile(user_id, data)

@user_bp.route('/change-password', methods=['POST'])
@error_handler
@jwt_required()
@validate_request_params(['old_password', 'new_password'])
def change_password():
    """修改密码"""
    user_id = get_jwt_identity()
    data = request.get_json()
    return UserService.change_password(user_id, data['old_password'], data['new_password'])

@user_bp.route('/verification-code', methods=['POST'])
@error_handler
@validate_request_params(['phone'])
def get_verification_code():
    """获取验证码"""
    data = request.get_json()
    return UserService.get_verification_code(data['phone'])

@user_bp.route('/verify-code', methods=['POST'])
@error_handler
@validate_request_params(['phone', 'code'])
def verify_verification_code():
    """验证验证码"""
    data = request.get_json()
    return UserService.verify_verification_code(data['phone'], data['code'])

@user_bp.route('/recharge', methods=['POST'])
@error_handler
@jwt_required()
@validate_request_params(['amount', 'payment_method'])
def recharge_balance():
    """充值余额"""
    user_id = get_jwt_identity()
    data = request.get_json()
    return UserService.recharge_balance(user_id, data['amount'], data['payment_method'])

@user_bp.route('/recharge-records', methods=['GET'])
@error_handler
@jwt_required()
def get_recharge_records():
    """获取充值记录"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    return UserService.get_recharge_records(user_id, page, per_page)

@user_bp.route('/balance', methods=['GET'])
@error_handler
@jwt_required()
def get_balance():
    """获取用户余额"""
    user_id = get_jwt_identity()
    return UserService.get_user_balance(user_id)

@user_bp.route('/', methods=['GET'])
@error_handler
def list_users():
    """获取用户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search')
    return UserService.list_users(page, per_page, search)

@user_bp.route('/<int:user_id>', methods=['GET'])
@error_handler
def get_user(user_id):
    """获取用户信息"""
    return UserService.get_user_by_id(user_id)

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@error_handler
def delete_user(user_id):
    """删除用户"""
    return UserService.delete_user(user_id)