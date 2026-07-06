from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import get_jwt_identity
from services.review_service import ReviewService
from utils.helpers import error_handler, validate_request_params
from utils.response import success_response, error_response

review_bp = Blueprint('review', __name__, url_prefix='/api/reviews')

def get_current_user_id():
    """获取当前用户ID，优先从JWT获取，其次从session获取"""
    # 尝试从JWT token获取
    try:
        user_id = get_jwt_identity()
        if user_id:
            return user_id
    except:
        pass
    
    # 尝试从session获取（PC端登录）
    if 'user_id' in session:
        return session['user_id']
    
    return None

# ==================== 用户端接口 ====================

@review_bp.route('', methods=['POST'])
@error_handler
def create_review():
    """提交评价"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    data = request.get_json()
    return ReviewService.create_review(user_id, data)

@review_bp.route('/room/<int:room_id>', methods=['GET'])
def get_room_reviews(room_id):
    """获取茶室的评价列表（分页）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    return ReviewService.get_room_reviews(room_id, page, per_page)

@review_bp.route('/room/<int:room_id>/rating', methods=['GET'])
def get_room_average_rating(room_id):
    """获取茶室的平均评分"""
    return ReviewService.get_room_average_rating(room_id)

@review_bp.route('/<int:review_id>', methods=['GET'])
@error_handler
def get_review_detail(review_id):
    """获取单个评价详情"""
    return ReviewService.get_review_detail(review_id)

@review_bp.route('/user', methods=['GET'])
@error_handler
def get_user_reviews():
    """获取我的评价列表"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    return ReviewService.get_user_reviews(user_id, page, per_page)

@review_bp.route('/order/<int:order_id>/status', methods=['GET'])
@error_handler
def get_order_review_status(order_id):
    """查询订单评价状态"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    return ReviewService.get_order_review_status(order_id, user_id)

@review_bp.route('/<int:review_id>', methods=['PUT'])
@error_handler
def update_review(review_id):
    """更新评价"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    data = request.get_json()
    return ReviewService.update_review(review_id, user_id, data)

@review_bp.route('/<int:review_id>', methods=['DELETE'])
@error_handler
def delete_review(review_id):
    """删除评价"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    return ReviewService.delete_review_user(review_id, user_id)

# ==================== 管理端接口 ====================

@review_bp.route('/admin', methods=['GET'])
@error_handler
def get_all_reviews_admin():
    """管理员获取全部评价列表"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    from models import User
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return error_response(403, '无权限访问')
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    room_id = request.args.get('room_id', type=int)
    rating = request.args.get('rating', type=int)
    keyword = request.args.get('keyword', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    return ReviewService.get_all_reviews_admin(
        page=page,
        per_page=per_page,
        room_id=room_id,
        rating=rating,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date
    )

@review_bp.route('/admin/<int:review_id>', methods=['DELETE'])
@error_handler
def delete_review_admin(review_id):
    """管理员删除评价"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response(401, '请先登录')
    
    from models import User
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return error_response(403, '无权限访问')
    
    return ReviewService.delete_review_admin(review_id)