from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import get_jwt_identity
from services.repair_service import RepairService
from utils.helpers import error_handler
from utils.response import success_response, error_response

repair_bp = Blueprint('repair', __name__, url_prefix='/api')

def get_current_user_id():
    """获取当前用户ID，优先从JWT获取，其次从session获取（支持用户和管理员）"""
    try:
        user_id = get_jwt_identity()
        if user_id:
            return user_id
    except:
        pass
    
    # 支持普通用户登录
    if 'user_id' in session:
        return session['user_id']
    
    # 支持管理员登录
    if 'admin_id' in session:
        return session['admin_id']
    
    return None

# ==================== 用户端接口 ====================

@repair_bp.route('/repairs', methods=['POST'])
@error_handler
def submit_repair():
    """提交报修工单"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    # 获取表单数据
    data = {
        'room_id': request.form.get('room_id'),
        'order_id': request.form.get('order_id'),
        'title': request.form.get('title'),
        'description': request.form.get('description'),
        'priority': request.form.get('priority', 'normal')
    }
    
    # 获取文件
    files = request.files
    
    return RepairService.submit_repair(user_id, data, files)

@repair_bp.route('/repairs/my', methods=['GET'])
@error_handler
def get_user_repairs():
    """获取我的报修列表"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    
    return RepairService.get_user_repairs(user_id, page, per_page, status)

@repair_bp.route('/repairs/<int:repair_id>', methods=['GET'])
@error_handler
def get_repair_detail(repair_id):
    """获取报修详情（用户端）"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    return RepairService.get_repair_detail(repair_id, user_id)

# ==================== 管理端接口 ====================

@repair_bp.route('/admin/repairs', methods=['GET'])
@error_handler
def get_all_repairs():
    """管理员获取全部报修列表"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    # 验证管理员权限
    from models import User
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return error_response(403, '无权限访问')
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    room_id = request.args.get('room_id', type=int)
    keyword = request.args.get('keyword')
    
    return RepairService.get_all_repairs(page, per_page, status, room_id, keyword)

@repair_bp.route('/admin/repairs/<int:repair_id>', methods=['GET'])
@error_handler
def get_repair_detail_admin(repair_id):
    """管理员获取工单详情"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    # 验证管理员权限
    from models import User
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return error_response(403, '无权限访问')
    
    return RepairService.get_repair_detail(repair_id)

@repair_bp.route('/admin/repairs/<int:repair_id>/status', methods=['PUT'])
@error_handler
def update_repair_status(repair_id):
    """管理员更新工单状态"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    # 验证管理员权限
    from models import User
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return error_response(403, '无权限访问')
    
    data = request.get_json()
    status = data.get('status')
    remark = data.get('handler_remark')
    
    return RepairService.update_status(repair_id, status, remark)

@repair_bp.route('/admin/repairs/<int:repair_id>', methods=['DELETE'])
@error_handler
def delete_repair(repair_id):
    """管理员删除工单"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    # 验证管理员权限
    from models import User
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return error_response(403, '无权限访问')
    
    return RepairService.delete_repair(repair_id)

@repair_bp.route('/admin/repairs/pending-count', methods=['GET'])
@error_handler
def get_pending_count():
    """获取待处理工单数量（用于首页角标）"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    # 验证管理员权限
    from models import User
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return error_response(403, '无权限访问')
    
    return RepairService.get_pending_count()