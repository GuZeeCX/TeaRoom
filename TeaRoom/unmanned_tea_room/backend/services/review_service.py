from models import db, Review, Order, Room, User
from utils.response import success_response, error_response, not_found_response, paginated_response, forbidden_response
from datetime import datetime, timedelta
from sqlalchemy import func

class ReviewService:
    @staticmethod
    def create_review(user_id, data):
        """创建评价"""
        order_id = data.get('order_id')
        room_id = data.get('room_id')
        rating = data.get('rating')
        comment = data.get('comment', '')
        
        if not order_id or not room_id or not rating:
            return error_response(400, '缺少必要参数')
        
        # 验证评分范围
        if rating < 1 or rating > 5:
            return error_response(400, '评分必须在1-5星之间')
        
        # 验证评论长度
        if comment and len(comment) > 200:
            return error_response(400, '评论内容不能超过200字')
        
        # 验证订单是否存在
        order = Order.query.get(order_id)
        if not order:
            return not_found_response('订单不存在')
        
        # 验证订单所属用户
        if order.user_id != user_id:
            return error_response(403, '无权操作此订单')
        
        # 验证订单状态
        if order.status != 'completed':
            return error_response(400, '只能对已完成的订单进行评价')
        
        # 验证是否已经评价过
        existing_review = Review.query.filter_by(order_id=order_id).first()
        if existing_review:
            return error_response(400, '该订单已经评价过')
        
        # 开始事务
        try:
            review = Review(
                user_id=user_id,
                room_id=room_id,
                order_id=order_id,
                rating=rating,
                comment=comment
            )
            
            db.session.add(review)
            db.session.commit()
            
            return success_response(review.to_dict(), '评价成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'评价失败: {str(e)}')
    
    @staticmethod
    def get_room_reviews(room_id, page=1, per_page=10):
        """获取茶室的评价列表（分页）"""
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('茶室不存在')
        
        pagination = Review.query.filter_by(room_id=room_id).order_by(Review.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        reviews_data = []
        for review in pagination.items:
            review_dict = review.to_dict()
            # 用户昵称脱敏处理
            if review.user:
                username = review.user.real_name or review.user.username
                if len(username) > 2:
                    review_dict['username'] = username[0] + '**' + username[-1]
                else:
                    review_dict['username'] = username[0] + '**'
            reviews_data.append(review_dict)
        
        # 计算平均评分
        avg_result = db.session.query(func.avg(Review.rating)).filter(Review.room_id == room_id).scalar()
        average_rating = round(float(avg_result), 1) if avg_result else 0.0
        
        # 总评价数
        total_count = Review.query.filter_by(room_id=room_id).count()
        
        return success_response({
            'reviews': reviews_data,
            'average_rating': average_rating,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        })
    
    @staticmethod
    def get_room_average_rating(room_id):
        """获取茶室的平均评分"""
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('茶室不存在')
        
        result = db.session.query(
            db.func.avg(Review.rating)
        ).filter(
            Review.room_id == room_id
        ).scalar()
        
        average_rating = round(float(result), 1) if result else 0.0
        
        return success_response({'average_rating': average_rating})
    
    @staticmethod
    def get_user_reviews(user_id, page=1, per_page=10):
        """获取用户的评价列表"""
        user = User.query.get(user_id)
        if not user:
            return not_found_response('用户不存在')
        
        pagination = Review.query.filter_by(user_id=user_id).order_by(Review.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        reviews = []
        for review in pagination.items:
            review_dict = review.to_dict()
            # 添加茶室和订单信息
            if review.room:
                review_dict['room_name'] = review.room.name
            if review.order:
                review_dict['order_no'] = review.order.order_no
            reviews.append(review_dict)
        
        return success_response({
            'reviews': reviews,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        })
    
    @staticmethod
    def get_order_review_status(order_id, user_id):
        """查询订单评价状态"""
        order = Order.query.get(order_id)
        if not order:
            return not_found_response('订单不存在')
        
        # 验证订单所属用户
        if order.user_id != user_id:
            return error_response(403, '无权查看此订单')
        
        # 查询是否已评价
        review = Review.query.filter_by(order_id=order_id).first()
        
        return success_response({
            'order_id': order_id,
            'order_status': order.status,
            'can_review': order.status == 'completed' and review is None,
            'has_reviewed': review is not None,
            'review_id': review.id if review else None
        })
    
    @staticmethod
    def update_review(review_id, user_id, data):
        """更新评价"""
        review = Review.query.get(review_id)
        if not review:
            return not_found_response('评价不存在')
        
        # 验证评价所属用户
        if review.user_id != user_id:
            return error_response(403, '无权操作此评价')
        
        # 验证评价时间（只能在创建后24小时内修改）
        if datetime.now() > review.created_at + timedelta(hours=24):
            return error_response(400, '评价超过24小时，无法修改')
        
        # 更新评价
        rating = data.get('rating')
        comment = data.get('comment')
        
        if rating is not None:
            if rating < 1 or rating > 5:
                return error_response(400, '评分必须在1-5星之间')
            review.rating = rating
        
        if comment is not None:
            if len(comment) > 200:
                return error_response(400, '评论内容不能超过200字')
            review.comment = comment
        
        try:
            db.session.commit()
            return success_response(review.to_dict(), '评价更新成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'评价更新失败: {str(e)}')
    
    @staticmethod
    def delete_review_user(review_id, user_id):
        """删除评价（用户）"""
        review = Review.query.get(review_id)
        if not review:
            return not_found_response('评价不存在')
        
        # 验证评价所属用户
        if review.user_id != user_id:
            return error_response(403, '无权操作此评价')
        
        # 验证评价时间（只能在创建后24小时内删除）
        if datetime.now() > review.created_at + timedelta(hours=24):
            return error_response(400, '评价超过24小时，无法删除')
        
        try:
            db.session.delete(review)
            db.session.commit()
            return success_response({}, '评价删除成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'评价删除失败: {str(e)}')
    
    # ==================== 管理端接口 ====================
    
    @staticmethod
    def get_all_reviews_admin(page=1, per_page=10, room_id=None, rating=None, keyword=None, start_date=None, end_date=None):
        """管理员获取全部评价列表（支持筛选）"""
        query = Review.query
        
        # 茶室筛选
        if room_id:
            query = query.filter(Review.room_id == room_id)
        
        # 星级筛选
        if rating:
            query = query.filter(Review.rating == rating)
        
        # 关键词搜索（用户昵称或评论内容）
        if keyword:
            query = query.join(User).filter(
                (User.real_name.ilike(f'%{keyword}%')) | 
                (User.username.ilike(f'%{keyword}%')) |
                (Review.comment.ilike(f'%{keyword}%'))
            )
        
        # 时间范围筛选
        if start_date:
            try:
                start = datetime.fromisoformat(start_date)
                query = query.filter(Review.created_at >= start)
            except:
                pass
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date)
                query = query.filter(Review.created_at <= end)
            except:
                pass
        
        # 排序和分页
        pagination = query.order_by(Review.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        reviews_data = []
        for review in pagination.items:
            review_dict = review.to_dict()
            # 添加完整信息
            if review.user:
                review_dict['user_real_name'] = review.user.real_name
                review_dict['user_phone'] = review.user.phone
            if review.room:
                review_dict['room_name'] = review.room.name
            if review.order:
                review_dict['order_no'] = review.order.order_no
            reviews_data.append(review_dict)
        
        # 统计数据
        total_count = Review.query.count()
        avg_result = db.session.query(func.avg(Review.rating)).scalar()
        average_rating = round(float(avg_result), 1) if avg_result else 0.0
        
        # 各星级占比
        rating_distribution = {}
        for r in range(1, 6):
            count = Review.query.filter(Review.rating == r).count()
            rating_distribution[r] = count
        
        return success_response({
            'reviews': reviews_data,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages,
            'statistics': {
                'total_count': total_count,
                'average_rating': average_rating,
                'rating_distribution': rating_distribution
            }
        })
    
    @staticmethod
    def delete_review_admin(review_id):
        """管理员删除评价"""
        review = Review.query.get(review_id)
        if not review:
            return not_found_response('评价不存在')
        
        try:
            # 记录删除信息
            review_info = review.to_dict()
            db.session.delete(review)
            db.session.commit()
            return success_response({'deleted_review': review_info}, '评价删除成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'评价删除失败: {str(e)}')
    
    @staticmethod
    def get_review_detail(review_id):
        """获取单个评价详情"""
        review = Review.query.get(review_id)
        if not review:
            return not_found_response('评价不存在')
        
        review_dict = review.to_dict()
        
        # 添加关联信息
        if review.user:
            review_dict['user_real_name'] = review.user.real_name
            review_dict['username'] = review.user.username
        if review.room:
            review_dict['room_name'] = review.room.name
        if review.order:
            review_dict['order_no'] = review.order.order_no
        
        return success_response(review_dict)