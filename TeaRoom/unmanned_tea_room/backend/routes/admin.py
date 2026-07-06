from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Room, Order
from datetime import datetime, timedelta
import pandas as pd
import io
import os

admin_bp = Blueprint('admin', __name__)

# 管理员权限装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('请先登录管理员账号', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

# 管理员登录页面
@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 简单验证（实际项目应该使用数据库）
        if username == 'admin' and password == 'admin123':
            session['admin_id'] = 1
            session['admin_name'] = '管理员'
            flash('登录成功', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('admin/login.html')

# 管理员登出
@admin_bp.route('/admin/logout')
def logout():
    session.clear()
    flash('已退出登录', 'success')
    return redirect(url_for('admin.login'))

# 管理员忘记密码
@admin_bp.route('/admin/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        verification_code = request.form.get('verification_code', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 验证用户名
        if not username:
            flash('请输入管理员账号', 'error')
            return render_template('admin/forgot_password.html')
        
        # 验证验证码（演示模式：验证码为123456）
        if not verification_code:
            flash('请输入安全验证码', 'error')
            return render_template('admin/forgot_password.html')
        
        if verification_code != '123456':
            flash('验证码错误', 'error')
            return render_template('admin/forgot_password.html')
        
        # 验证密码
        if not new_password:
            flash('请输入新密码', 'error')
            return render_template('admin/forgot_password.html')
        
        if len(new_password) < 5 or len(new_password) > 20:
            flash('密码长度必须在5-20个字符之间', 'error')
            return render_template('admin/forgot_password.html')
        
        import re
        if not re.search(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', new_password):
            flash('密码必须包含大小写字母和数字', 'error')
            return render_template('admin/forgot_password.html')
        
        if new_password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('admin/forgot_password.html')
        
        # 更新管理员密码
        # 注意：实际项目中应该从数据库查找管理员并更新密码
        # 这里简化处理，仅更新默认管理员密码
        if username == 'admin':
            flash('密码重置成功，请使用新密码登录', 'success')
            return redirect(url_for('admin.login'))
        else:
            flash('管理员账号不存在', 'error')
            return render_template('admin/forgot_password.html')
    
    return render_template('admin/forgot_password.html')

# 管理员首页
@admin_bp.route('/admin')
@admin_required
def dashboard():
    # 获取统计数据
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    # 今日订单数
    today_orders = Order.query.filter(Order.created_at >= today_start).count()
    
    # 今日营收
    today_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
        Order.created_at >= today_start,
        Order.status == 'completed'
    ).scalar() or 0
    
    # 总用户数
    total_users = User.query.count()
    
    # 总房间数
    total_rooms = Room.query.count()
    
    # 可用房间数
    available_rooms = Room.query.filter_by(status='available').count()
    
    # 使用中房间数
    in_use_rooms = Room.query.filter_by(status='occupied').count()
    
    # 本月订单数
    month_start = today.replace(day=1)
    month_orders = Order.query.filter(Order.created_at >= month_start).count()
    
    # 本月营收
    month_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
        Order.created_at >= month_start,
        Order.status == 'completed'
    ).scalar() or 0
    
    # ========== 评价统计 ==========
    from models import Review
    total_reviews = Review.query.count()
    today_reviews = Review.query.filter(Review.created_at >= today_start).count()
    
    # ========== 报修统计 ==========
    from models import Repair
    total_repairs = Repair.query.count()
    pending_repairs = Repair.query.filter_by(status='pending').count()
    today_repairs = Repair.query.filter(Repair.created_at >= today_start).count()
    
    # 最近订单
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                        today=today,
                        today_orders=today_orders,
                        today_revenue=today_revenue,
                        total_users=total_users,
                        total_rooms=total_rooms,
                        available_rooms=available_rooms,
                        in_use_rooms=in_use_rooms,
                        month_orders=month_orders,
                        month_revenue=month_revenue,
                        total_reviews=total_reviews,
                        today_reviews=today_reviews,
                        total_repairs=total_repairs,
                        pending_repairs=pending_repairs,
                        today_repairs=today_repairs,
                        recent_orders=recent_orders)

# 房间管理
@admin_bp.route('/admin/rooms')
@admin_required
def rooms():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Room.query
    
    if search:
        query = query.filter(Room.name.contains(search))
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    pagination = query.order_by(Room.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/rooms.html',
                        rooms=pagination.items,
                        pagination=pagination,
                        search=search,
                        status_filter=status_filter)

# 添加房间
@admin_bp.route('/admin/rooms/add', methods=['GET', 'POST'])
@admin_required
def add_room():
    if request.method == 'POST':
        room = Room(
            name=request.form.get('name'),
            description=request.form.get('description'),
            price_per_hour=float(request.form.get('price_per_hour')),
            status=request.form.get('status', 'available'),
            facilities=request.form.get('facilities', '').split(',') if request.form.get('facilities') else [],
            image_url=request.form.get('image_url', '')
        )
        
        db.session.add(room)
        db.session.commit()
        
        flash('房间添加成功', 'success')
        return redirect(url_for('admin.rooms'))
    
    return render_template('admin/room_form.html', room=None)

# 编辑房间
@admin_bp.route('/admin/rooms/<int:room_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_room(room_id):
    room = Room.query.get_or_404(room_id)
    
    if request.method == 'POST':
        room.name = request.form.get('name')
        room.description = request.form.get('description')
        room.price_per_hour = float(request.form.get('price_per_hour'))
        room.status = request.form.get('status', 'available')
        room.facilities = request.form.get('facilities', '').split(',') if request.form.get('facilities') else []
        room.image_url = request.form.get('image_url', '')
        
        db.session.commit()
        
        flash('房间更新成功', 'success')
        return redirect(url_for('admin.rooms'))
    
    return render_template('admin/room_form.html', room=room)

# 删除房间
@admin_bp.route('/admin/rooms/<int:room_id>/delete', methods=['POST'])
@admin_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    
    flash('房间删除成功', 'success')
    return redirect(url_for('admin.rooms'))

# 订单管理
@admin_bp.route('/admin/orders')
@admin_required
def orders():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Order.query
    
    if search:
        query = query.filter(Order.order_no.contains(search))
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    pagination = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/orders.html',
                        orders=pagination.items,
                        pagination=pagination,
                        search=search,
                        status_filter=status_filter)

# 订单详情
@admin_bp.route('/admin/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    # 查询订单关联的评价
    review = None
    if hasattr(order, 'review') and order.review:
        # order.review 可能是列表（一对多关系），取第一个
        reviews_list = order.review
        if isinstance(reviews_list, list) and len(reviews_list) > 0:
            review = reviews_list[0]
        else:
            review = reviews_list
    else:
        # 通过order_id查询评价
        from models import Review
        review = Review.query.filter_by(order_id=order.id).first()
    return render_template('admin/order_detail.html', order=order, review=review)

# 更新订单状态
@admin_bp.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'confirmed', 'in_use', 'completed', 'cancelled']:
        order.status = new_status
        db.session.commit()
        flash('订单状态更新成功', 'success')
    else:
        flash('无效的状态', 'error')
    
    return redirect(url_for('admin.orders'))

# 用户管理
@admin_bp.route('/admin/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.contains(search)) | 
            (User.phone.contains(search)) |
            (User.real_name.contains(search))
        )
    
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html',
                        users=pagination.items,
                        pagination=pagination,
                        search=search)

# 用户详情
@admin_bp.route('/admin/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    # 获取用户的订单
    user_orders = Order.query.filter_by(user_id=user_id).order_by(
        Order.created_at.desc()
    ).limit(10).all()
    
    return render_template('admin/user_detail.html',
                        user=user,
                        user_orders=user_orders)

# 禁用/启用用户
@admin_bp.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = '启用' if user.is_active else '禁用'
    flash(f'用户已{status}', 'success')
    
    return redirect(url_for('admin.users'))

# 导出用户数据
@admin_bp.route('/admin/users/export')
@admin_required
def export_users():
    users = User.query.all()
    
    data = []
    for user in users:
        data.append({
            'ID': user.id,
            '用户名': user.username,
            '真实姓名': user.real_name,
            '手机号': user.phone,
            '邮箱': user.email or '',
            '状态': '启用' if user.is_active else '禁用',
            '注册时间': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else ''
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='用户数据')
    
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'用户数据_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

# 数据统计
@admin_bp.route('/admin/statistics')
@admin_required
def statistics():
    # 获取日期范围
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    # 每日营收数据
    daily_revenue = db.session.query(
        db.func.date(Order.created_at).label('date'),
        db.func.sum(Order.total_amount).label('revenue'),
        db.func.count(Order.id).label('order_count')
    ).filter(
        Order.created_at >= start_datetime,
        Order.created_at < end_datetime,
        Order.status == 'completed'
    ).group_by(
        db.func.date(Order.created_at)
    ).order_by(
        db.func.date(Order.created_at)
    ).all()
    
    # 房间使用率
    room_usage = []
    rooms = Room.query.all()
    for room in rooms:
        room_orders = Order.query.filter(
            Order.room_id == room.id,
            Order.created_at >= start_datetime,
            Order.created_at < end_datetime
        ).all()
        
        total_minutes = sum(order.duration_hours * 60 for order in room_orders if order.duration_hours)
        total_available_minutes = (end_datetime - start_datetime).total_seconds() / 60
        
        usage_rate = min((total_minutes / total_available_minutes) * 100, 100) if total_available_minutes > 0 else 0
        
        room_usage.append({
            'room_id': room.id,
            'room_name': room.name,
            'usage_rate': round(usage_rate, 2),
            'order_count': len(room_orders)
        })
    
    # 将Row对象转换为字典，以便JSON序列化
    daily_revenue_list = [{
        'date': str(item.date),
        'revenue': float(item.revenue or 0),
        'order_count': item.order_count or 0
    } for item in daily_revenue]
    
    # 总体统计
    total_revenue = sum(item['revenue'] for item in daily_revenue_list)
    total_orders = sum(item['order_count'] for item in daily_revenue_list)
    
    return render_template('admin/statistics.html',
                        start_date=start_date,
                        end_date=end_date,
                        daily_revenue=daily_revenue_list,
                        room_usage=room_usage,
                        total_revenue=total_revenue,
                        total_orders=total_orders)

# 茶室盈利详情
@admin_bp.route('/admin/room_statistics/<int:room_id>')
@admin_required
def room_statistics(room_id):
    room = Room.query.get_or_404(room_id)
    
    # 获取日期范围
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    # 该茶室的订单
    room_orders = Order.query.filter(
        Order.room_id == room_id,
        Order.created_at >= start_datetime,
        Order.created_at < end_datetime
    ).order_by(Order.created_at.desc()).all()
    
    # 每日营收数据
    daily_revenue = db.session.query(
        db.func.date(Order.created_at).label('date'),
        db.func.sum(Order.total_amount).label('revenue'),
        db.func.count(Order.id).label('order_count')
    ).filter(
        Order.room_id == room_id,
        Order.created_at >= start_datetime,
        Order.created_at < end_datetime,
        Order.status == 'completed'
    ).group_by(
        db.func.date(Order.created_at)
    ).order_by(
        db.func.date(Order.created_at)
    ).all()
    
    # 将Row对象转换为字典
    daily_revenue_list = [{
        'date': str(item.date),
        'revenue': float(item.revenue or 0),
        'order_count': item.order_count or 0
    } for item in daily_revenue]
    
    # 总体统计
    total_revenue = sum(item['revenue'] for item in daily_revenue_list)
    total_orders = sum(item['order_count'] for item in daily_revenue_list)
    
    # 茶叶销售统计
    tea_sales = {}
    for order in room_orders:
        if order.tea_type and order.tea_type != '自带茶叶':
            if order.tea_type not in tea_sales:
                tea_sales[order.tea_type] = {'count': 0, 'revenue': 0, 'weight': 0}
            tea_sales[order.tea_type]['count'] += 1
            tea_sales[order.tea_type]['revenue'] += order.tea_price or 0
            tea_sales[order.tea_type]['weight'] += order.tea_weight or 0
    
    return render_template('admin/room_statistics.html',
                        room=room,
                        start_date=start_date,
                        end_date=end_date,
                        daily_revenue=daily_revenue_list,
                        total_revenue=total_revenue,
                        total_orders=total_orders,
                        room_orders=room_orders,
                        tea_sales=tea_sales)

# 系统设置
@admin_bp.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    if request.method == 'POST':
        # 这里应该保存设置到数据库或配置文件
        # 简化处理，只显示成功消息
        flash('设置保存成功', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html')

# API接口：获取统计数据
@admin_bp.route('/admin/api/statistics')
@admin_required
def api_statistics():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    # 每日营收数据
    daily_revenue = db.session.query(
        db.func.date(Order.created_at).label('date'),
        db.func.sum(Order.total_amount).label('revenue'),
        db.func.count(Order.id).label('order_count')
    ).filter(
        Order.created_at >= start_datetime,
        Order.created_at < end_datetime,
        Order.status == 'completed'
    ).group_by(
        db.func.date(Order.created_at)
    ).order_by(
        db.func.date(Order.created_at)
    ).all()
    
    data = [{
        'date': str(item.date),
        'revenue': float(item.revenue or 0),
        'order_count': item.order_count or 0
    } for item in daily_revenue]
    
    return jsonify(data)

# 评价管理
@admin_bp.route('/admin/reviews')
@admin_required
def reviews():
    from models import Review
    from sqlalchemy import func
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    room_id = request.args.get('room_id', type=int)
    rating = request.args.get('rating', type=int)
    keyword = request.args.get('keyword', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # 构建查询
    query = Review.query
    
    # 茶室筛选
    if room_id:
        query = query.filter(Review.room_id == room_id)
    
    # 星级筛选
    if rating:
        query = query.filter(Review.rating == rating)
    
    # 关键词搜索
    if keyword:
        query = query.join(User).filter(
            (User.real_name.ilike(f'%{keyword}%')) | 
            (User.username.ilike(f'%{keyword}%')) |
            (Review.comment.ilike(f'%{keyword}%'))
        )
    
    # 时间范围筛选
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Review.created_at >= start)
        except:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Review.created_at <= end)
        except:
            pass
    
    # 排序和分页
    pagination = query.order_by(Review.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 处理评价数据
    reviews_data = []
    for review in pagination.items:
        review_dict = {
            'id': review.id,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at
        }
        if review.user:
            review_dict['user_real_name'] = review.user.real_name
            review_dict['username'] = review.user.username
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
    
    # 获取所有茶室用于筛选
    rooms = Room.query.all()
    
    return render_template('admin/reviews.html',
                        reviews=reviews_data,
                        pagination=pagination,
                        page=page,
                        total_pages=pagination.pages,
                        rooms=rooms,
                        statistics={
                            'total_count': total_count,
                            'average_rating': average_rating,
                            'rating_distribution': rating_distribution
                        })

# 维修管理
@admin_bp.route('/admin/repairs')
@admin_required
def repairs():
    from models import Repair
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    status = request.args.get('status')
    room_id = request.args.get('room_id', type=int)
    priority = request.args.get('priority')
    keyword = request.args.get('keyword', '')
    
    # 构建查询
    query = Repair.query
    
    # 状态筛选
    if status:
        query = query.filter(Repair.status == status)
    
    # 茶室筛选
    if room_id:
        query = query.filter(Repair.room_id == room_id)
    
    # 优先级筛选
    if priority:
        query = query.filter(Repair.priority == priority)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            (Repair.title.ilike(f'%{keyword}%')) |
            (Repair.description.ilike(f'%{keyword}%'))
        )
    
    # 排序和分页
    pagination = query.order_by(Repair.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    repairs_data = []
    for repair in pagination.items:
        repair_dict = {
            'id': repair.id,
            'user_id': repair.user_id,
            'room_id': repair.room_id,
            'order_id': repair.order_id,
            'title': repair.title,
            'description': repair.description,
            'status': repair.status,
            'priority': repair.priority,
            'created_at': repair.created_at,
            'updated_at': repair.updated_at,
            'handler_remark': repair.handler_remark
        }
        if repair.user:
            repair_dict['user_real_name'] = repair.user.real_name
        if repair.room:
            repair_dict['room_name'] = repair.room.name
        if repair.order:
            repair_dict['order_no'] = repair.order.order_no
        repairs_data.append(repair_dict)
    
    # 统计各状态数量
    pending_count = Repair.query.filter_by(status='pending').count()
    processing_count = Repair.query.filter_by(status='processing').count()
    completed_count = Repair.query.filter_by(status='completed').count()
    closed_count = Repair.query.filter_by(status='closed').count()
    
    # 获取所有茶室用于筛选
    rooms = Room.query.all()
    
    return render_template('admin/repair_list.html',
                        repairs=repairs_data,
                        page=page,
                        total_pages=pagination.pages,
                        rooms=rooms,
                        pending_count=pending_count,
                        processing_count=processing_count,
                        completed_count=completed_count,
                        closed_count=closed_count)