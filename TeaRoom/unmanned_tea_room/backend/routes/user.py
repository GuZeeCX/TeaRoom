from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from models import db, User, Room, Order, Booking, RechargeRecord, Tea, MemberRecord
from datetime import datetime, timedelta
import re

user_bp = Blueprint('user_frontend', __name__)

# 用户权限装饰器
def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'error')
            return redirect(url_for('user_frontend.login'))
        return f(*args, **kwargs)
    return decorated_function

# 用户注册页面
@user_bp.route('/user/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        real_name = request.form.get('real_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 验证用户名
        if not username:
            flash('用户名不能为空', 'error')
            return render_template('user/register.html')
        if len(username) < 3 or len(username) > 20:
            flash('用户名长度必须在3-20个字符之间', 'error')
            return render_template('user/register.html')
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9]+$', username):
            flash('用户名只能包含中文、字母和数字', 'error')
            return render_template('user/register.html')
        
        # 验证真实姓名
        if not real_name:
            flash('真实姓名不能为空', 'error')
            return render_template('user/register.html')
        if len(real_name) < 1 or len(real_name) > 20:
            flash('真实姓名长度必须在1-20个字符之间', 'error')
            return render_template('user/register.html')
        if not re.match(r'^[\u4e00-\u9fa5]+$', real_name):
            flash('真实姓名必须为中文', 'error')
            return render_template('user/register.html')
        
        # 验证手机号
        if not phone:
            flash('手机号不能为空', 'error')
            return render_template('user/register.html')
        if not re.match(r'^1[3-9]\d{9}$', phone):
            flash('请输入有效的11位手机号', 'error')
            return render_template('user/register.html')
        
        # 验证邮箱（如果提供）
        if email:
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                flash('请输入有效的邮箱地址', 'error')
                return render_template('user/register.html')
        
        # 验证密码
        if not password:
            flash('密码不能为空', 'error')
            return render_template('user/register.html')
        if len(password) < 5 or len(password) > 20:
            flash('密码长度必须在5-20个字符之间', 'error')
            return render_template('user/register.html')
        if not re.search(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', password):
            flash('密码必须包含大小写字母和数字', 'error')
            return render_template('user/register.html')
        
        # 验证确认密码
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('user/register.html')
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return render_template('user/register.html')
        
        # 检查手机号是否已存在
        if User.query.filter_by(phone=phone).first():
            flash('手机号已被注册', 'error')
            return render_template('user/register.html')
        
        # 检查邮箱是否已存在（如果提供了邮箱）
        if email and User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return render_template('user/register.html')
        
        # 创建新用户
        new_user = User(
            username=username,
            real_name=real_name,
            phone=phone,
            email=email if email else None,
            is_admin=False,
            balance=0.0
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('user_frontend.login'))
    
    return render_template('user/register.html')

# 用户登录页面
@user_bp.route('/user/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        
        if not identifier or not password:
            flash('请输入用户名/手机号和密码', 'error')
            return render_template('user/login.html')
        
        # 查找用户（支持用户名或手机号登录）
        user = User.query.filter(
            (User.username == identifier) | (User.phone == identifier)
        ).first()
        
        if user and user.check_password(password):
            # 检查用户是否被禁用（处理字段不存在的情况）
            if hasattr(user, 'is_active') and not user.is_active:
                flash('账号已被禁用，请联系管理员', 'error')
                return render_template('user/login.html')
            
            session['user_id'] = user.id
            session['user_name'] = user.real_name
            session['is_admin'] = user.is_admin
            
            flash('登录成功', 'success')
            
            # 如果是管理员，重定向到管理后台
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            
            return redirect(url_for('user_frontend.dashboard'))
        else:
            flash('用户名/手机号或密码错误', 'error')
    
    return render_template('user/login.html')

# 用户登出
@user_bp.route('/user/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('is_admin', None)
    flash('已退出登录', 'success')
    return redirect(url_for('user_frontend.login'))

# 用户首页
@user_bp.route('/user')
@user_required
def dashboard():
    # 获取当前用户信息
    user = User.query.get(session['user_id'])
    
    # 获取用户的订单
    recent_orders = Order.query.filter_by(user_id=user.id).order_by(
        Order.created_at.desc()
    ).limit(5).all()
    
    # 获取所有可用房间
    available_rooms = Room.query.filter_by(status='available').all()
    
    return render_template('user/dashboard.html',
                        user=user,
                        recent_orders=recent_orders,
                        available_rooms=available_rooms)

# 茶室列表页面
@user_bp.route('/user/rooms')
@user_required
def rooms():
    # 获取当前用户信息
    user = User.query.get(session['user_id'])
    
    # 获取查询参数
    search_query = request.args.get('search', '')
    capacity_filter = request.args.get('capacity', '')
    sort_by = request.args.get('sort', 'price_asc')
    
    # 构建查询
    query = Room.query
    
    # 应用筛选
    if search_query:
        query = query.filter(Room.name.ilike(f'%{search_query}%'))
    
    if capacity_filter:
        query = query.filter_by(capacity=capacity_filter)
    
    # 应用排序
    if sort_by == 'price_asc':
        query = query.order_by(Room.price_per_hour.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Room.price_per_hour.desc())
    elif sort_by == 'capacity_asc':
        query = query.order_by(Room.capacity.asc())
    elif sort_by == 'capacity_desc':
        query = query.order_by(Room.capacity.desc())
    
    # 执行查询
    rooms = query.all()
    
    return render_template('user/rooms.html',
                        user=user,
                        rooms=rooms,
                        search_query=search_query,
                        capacity_filter=capacity_filter,
                        sort_by=sort_by)

# 预约页面
@user_bp.route('/user/reserve/<int:room_id>', methods=['GET', 'POST'])
@user_required
def reserve(room_id):
    # 获取当前用户信息
    user = User.query.get(session['user_id'])
    
    # 获取茶室信息
    room = Room.query.get(room_id)
    if not room:
        flash('茶室不存在', 'error')
        return redirect(url_for('user_frontend.rooms'))
    
    # 获取今天的日期
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_date = datetime.now().date()
    
    # 获取已预约的时段（获取所有日期的，前端根据选择的日期过滤）
    booked_slots = []
    bookings = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.status.in_(['pending', 'confirmed']),
        Booking.start_time >= datetime.now()  # 只查询未来的预约
    ).all()
    
    for booking in bookings:
        booked_slots.append({
            'date': booking.start_time.strftime('%Y-%m-%d'),
            'start_time': booking.start_time.strftime('%H:%M'),
            'end_time': booking.end_time.strftime('%H:%M')
        })
    
    if request.method == 'POST':
        # 获取表单数据
        date = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        tea_type = request.form.get('tea_type', '自带茶叶')  # 获取茶叶选择
        tea_weight = float(request.form.get('tea_weight', 0))  # 获取茶叶重量（克）
        payment_type = request.form.get('payment_type', 'immediate')  # 获取支付方式
        
        # 验证时间
        if not date or not start_time or not end_time:
            flash('请填写完整的预约信息', 'error')
            return redirect(url_for('user_frontend.reserve', room_id=room_id))
        
        # 构建预约时间
        start_datetime = datetime.strptime(f'{date} {start_time}', '%Y-%m-%d %H:%M')
        end_datetime = datetime.strptime(f'{date} {end_time}', '%Y-%m-%d %H:%M')
        
        # 验证时间逻辑
        if end_datetime <= start_datetime:
            flash('结束时间必须晚于开始时间', 'error')
            return redirect(url_for('user_frontend.reserve', room_id=room_id))
        
        if start_datetime < datetime.now():
            flash('预约时间不能早于当前时间', 'error')
            return redirect(url_for('user_frontend.reserve', room_id=room_id))
        
        # 检查时段是否已被占用
        overlapping_bookings = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.status.in_(['pending', 'confirmed']),
            Booking.start_time < end_datetime,
            Booking.end_time > start_datetime
        ).all()
        
        if overlapping_bookings:
            flash('该时段已被预约，请选择其他时段', 'error')
            return redirect(url_for('user_frontend.reserve', room_id=room_id))
        
        # 计算费用
        hours = (end_datetime - start_datetime).total_seconds() / 3600
        room_cost = hours * room.price_per_hour
        
        # 茶叶单价配置（元/克）
        tea_unit_prices = {
            '自带茶叶': 0.0,
            '西湖龙井': 1.5,      # 15元/10克
            '安溪铁观音': 1.2,    # 12元/10克
            '武夷大红袍': 1.8,    # 18元/10克
            '云南普洱': 1.6,      # 16元/10克
            '洞庭碧螺春': 1.4,    # 14元/10克
            '黄山毛峰': 1.3,      # 13元/10克
            '君山银针': 2.0,      # 20元/10克
            '福鼎白茶': 1.0,      # 10元/10克
            '正山小种': 1.7       # 17元/10克
        }
        tea_unit_price = tea_unit_prices.get(tea_type, 0.0)
        
        # 计算茶叶费用（单价 × 重量）
        tea_price = tea_unit_price * tea_weight
        
        # 会员优惠：茶叶九折
        if user.is_member and user.member_expires_at and user.member_expires_at > datetime.now():
            tea_price = tea_price * 0.9
        
        total_amount = room_cost + tea_price
        
        # 茶室消费满减优惠
        discount = 0.0
        if total_amount >= 500:
            discount = 200.0
        elif total_amount >= 300:
            discount = 100.0
        elif total_amount >= 200:
            discount = 50.0
        
        final_amount = total_amount - discount
        
        # 检查用户余额是否足够（仅在立即支付时检查）
        if payment_type == 'immediate' and user.balance < final_amount:
            flash('账户余额不足，请先充值', 'error')
            return redirect(url_for('user_frontend.recharge'))
        
        # 检查茶叶库存（如果不是自带茶叶）
        tea = None
        if tea_type != '自带茶叶' and tea_weight > 0:
            tea = Tea.query.filter_by(name=tea_type).first()
            if not tea:
                flash('所选茶叶不存在', 'error')
                return redirect(url_for('user_frontend.reserve', room_id=room_id))
            if tea.stock < tea_weight:
                flash(f'{tea_type}库存不足，剩余{tea.stock}克', 'error')
                return redirect(url_for('user_frontend.reserve', room_id=room_id))
        
        # 开始事务
        try:
            # 计算时长
            duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
            
            # 生成6位数开门验证码
            import random
            door_code = ''.join(random.choices('0123456789', k=6))
            
            # 创建预约
            import uuid
            booking_no = f"BOOK{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
            
            booking = Booking(
                booking_no=booking_no,
                user_id=user.id,
                room_id=room_id,
                booking_date=start_datetime.date(),
                start_time=start_datetime,
                end_time=end_datetime,
                duration_hours=duration_hours,
                estimated_amount=final_amount,
                status='confirmed',  # 直接确认预约
                tea_type=tea_type,  # 茶叶类型
                tea_price=tea_price,  # 茶叶价格
                tea_weight=tea_weight,  # 茶叶重量（克）
                tea_unit_price=tea_unit_price,  # 茶叶单价（元/克）
                package_type='按小时计费'  # 套餐类型
            )
            
            # 先保存booking以获取ID
            db.session.add(booking)
            db.session.flush()  # 不提交事务，只获取ID
            
            # 创建订单
            order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
            
            order = Order(
                order_no=order_no,
                booking_id=booking.id,  # 关联预约
                user_id=user.id,
                room_id=room_id,
                start_time=start_datetime,
                end_time=end_datetime,
                duration_hours=duration_hours,
                total_amount=final_amount,
                status='completed' if payment_type == 'immediate' else 'pending',
                payment_status='paid' if payment_type == 'immediate' else 'unpaid',
                door_code=door_code,  # 开门验证码
                payment_type=payment_type,  # 支付方式
                tea_type=tea_type,  # 茶叶类型
                tea_price=tea_price,  # 茶叶价格
                tea_weight=tea_weight,  # 茶叶重量（克）
                tea_unit_price=tea_unit_price,  # 茶叶单价（元/克）
                package_type='按小时计费'  # 套餐类型
            )
            
            # 只有在立即支付时才扣减用户余额
            if payment_type == 'immediate':
                user.balance -= final_amount
                user.total_consumption += final_amount
            
            # 扣减茶叶库存（如果不是自带茶叶）
            if tea and tea_weight > 0:
                tea.stock -= tea_weight
                db.session.add(tea)
            
            # 添加到数据库
            db.session.add(booking)
            db.session.add(order)
            db.session.commit()
            
            # 根据支付方式显示不同的提示
            if payment_type == 'immediate':
                flash(f'预约成功！开门验证码：{door_code}', 'success')
            else:
                flash(f'预约成功！开门验证码：{door_code}，请在使用完毕后支付费用', 'success')
            return redirect(url_for('user_frontend.orders'))
        except Exception as e:
            db.session.rollback()
            flash(f'预约失败：{str(e)}', 'error')
            return redirect(url_for('user_frontend.reserve', room_id=room_id))
    
    return render_template('user/reserve.html',
                        user=user,
                        room=room,
                        today=today_str,
                        booked_slots=booked_slots)

# 我的订单页面
@user_bp.route('/user/orders')
@user_required
def orders():
    # 获取当前用户信息
    user = User.query.get(session['user_id'])
    
    # 获取查询参数
    status_filter = request.args.get('status', '')
    
    # 构建查询
    query = Booking.query.filter_by(user_id=user.id)
    
    # 应用筛选
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    # 按创建时间倒序排序
    query = query.order_by(Booking.created_at.desc())
    
    # 执行查询
    bookings = query.all()
    
    # 计算本月统计数据
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    month_bookings = Booking.query.filter(
        Booking.user_id == user.id,
        Booking.created_at >= month_start
    ).all()
    
    month_booking_count = len(month_bookings)
    month_total_amount = sum(booking.estimated_amount for booking in month_bookings if booking.status != 'cancelled')
    
    return render_template('user/orders.html',
                        user=user,
                        bookings=bookings,
                        status_filter=status_filter,
                        now=now,
                        month_booking_count=month_booking_count,
                        month_total_amount=month_total_amount)

# 订单详情页面
@user_bp.route('/user/order/<int:booking_id>')
@user_required
def order_detail(booking_id):
    # 获取当前用户信息
    user = User.query.get(session['user_id'])
    
    # 获取预约信息
    booking = Booking.query.filter_by(id=booking_id, user_id=user.id).first()
    if not booking:
        flash('订单不存在', 'error')
        return redirect(url_for('user_frontend.orders'))
    
    # 获取订单信息（根据booking_id查找）
    order = Order.query.filter_by(booking_id=booking.id).first()
    if not order:
        # 如果没有找到订单，使用预订信息创建一个临时对象
        order = Order(
            order_no='',
            user_id=user.id,
            room_id=booking.room_id,
            start_time=booking.start_time,
            end_time=booking.end_time,
            duration_hours=booking.duration_hours,
            total_amount=booking.estimated_amount,
            status=booking.status,
            payment_status='unpaid',
            payment_type='immediate',
            tea_type=booking.tea_type,
            tea_price=booking.tea_price,
            tea_weight=booking.tea_weight,
            tea_unit_price=booking.tea_unit_price,
            package_type=booking.package_type
        )
    
    # 获取当前时间
    now = datetime.now()
    
    return render_template('user/order_detail.html',
                        user=user,
                        booking=booking,
                        order=order,
                        now=now)

# 取消预约
@user_bp.route('/user/cancel_booking/<int:booking_id>')
@user_required
def cancel_booking(booking_id):
    # 获取当前用户信息
    user = User.query.get(session['user_id'])
    
    # 获取预约信息
    booking = Booking.query.filter_by(id=booking_id, user_id=user.id).first()
    if not booking:
        flash('订单不存在', 'error')
        return redirect(url_for('user_frontend.orders'))
    
    # 检查是否可以取消
    if booking.status != 'pending' or booking.start_time <= datetime.now():
        flash('该订单无法取消', 'error')
        return redirect(url_for('user_frontend.orders'))
    
    # 取消预约
    booking.status = 'cancelled'
    db.session.commit()
    
    flash('预约已取消', 'success')
    return redirect(url_for('user_frontend.orders'))

# 支付后付订单
@user_bp.route('/user/pay_order/<int:booking_id>')
@user_required
def pay_order(booking_id):
    # 获取当前用户信息
    user = User.query.get(session['user_id'])
    
    # 获取预约信息
    booking = Booking.query.filter_by(id=booking_id, user_id=user.id).first()
    if not booking:
        flash('订单不存在', 'error')
        return redirect(url_for('user_frontend.orders'))
    
    # 获取订单信息
    order = Order.query.filter_by(booking_id=booking.id).first()
    if not order:
        flash('订单不存在', 'error')
        return redirect(url_for('user_frontend.orders'))
    
    # 检查是否已经支付
    if order.payment_status == 'paid':
        flash('该订单已支付', 'warning')
        return redirect(url_for('user_frontend.order_detail', booking_id=booking.id))
    
    # 检查用户余额是否足够
    if user.balance < order.total_amount:
        flash('账户余额不足，请先充值', 'error')
        return redirect(url_for('user_frontend.recharge'))
    
    # 开始事务
    try:
        # 扣减用户余额
        user.balance -= order.total_amount
        
        # 更新用户消费总额
        user.total_consumption += order.total_amount
        
        # 更新订单状态
        order.payment_status = 'paid'
        order.status = 'completed'
        
        db.session.commit()
        
        flash('支付成功！', 'success')
        return redirect(url_for('user_frontend.order_detail', booking_id=booking.id))
    except Exception as e:
        db.session.rollback()
        flash(f'支付失败：{str(e)}', 'error')
        return redirect(url_for('user_frontend.order_detail', booking_id=booking.id))

# 用户个人中心
@user_bp.route('/user/profile')
@user_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('user/profile.html', user=user)

# 修改用户信息
@user_bp.route('/user/profile/edit', methods=['GET', 'POST'])
@user_required
def edit_profile():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        real_name = request.form.get('real_name')
        email = request.form.get('email')
        
        if real_name:
            user.real_name = real_name
        if email:
            user.email = email
        
        db.session.commit()
        flash('信息更新成功', 'success')
        return redirect(url_for('user_frontend.profile'))
    
    return render_template('user/edit_profile.html', user=user)

# 修改密码
@user_bp.route('/user/change-password', methods=['GET', 'POST'])
@user_required
def change_password():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not user.check_password(old_password):
            flash('原密码错误', 'error')
            return render_template('user/change_password.html')
        
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'error')
            return render_template('user/change_password.html')
        
        user.set_password(new_password)
        db.session.commit()
        
        flash('密码修改成功', 'success')
        return redirect(url_for('user_frontend.profile'))
    
    return render_template('user/change_password.html')

# 账户充值页面
@user_bp.route('/user/recharge')
@user_required
def recharge():
    user = User.query.get(session['user_id'])
    return render_template('user/recharge.html', user=user)

# 处理充值请求
@user_bp.route('/user/recharge', methods=['POST'])
@user_required
def process_recharge():
    try:
        # 获取用户对象
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': '用户未登录'})
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        # 获取充值金额和支付方式
        amount = request.form.get('amount', type=float)
        payment_method = request.form.get('payment_method')
        
        # 验证参数
        if not amount or amount < 1:
            return jsonify({'success': False, 'message': '充值金额必须≥1元'})
        
        if not payment_method:
            return jsonify({'success': False, 'message': '请选择支付方式'})
        
        # 保存原始余额
        original_balance = user.balance
        
        # 更新用户余额
        user.balance += amount
        
        # 创建充值记录
        recharge_record = RechargeRecord(
            user_id=user.id,
            amount=amount,
            payment_method=payment_method,
            status='success'
        )
        
        db.session.add(recharge_record)
        db.session.commit()
        
        # 验证余额是否已更新
        updated_user = User.query.get(user_id)
        if updated_user and updated_user.balance == original_balance + amount:
            return jsonify({'success': True, 'message': '充值成功'})
        else:
            return jsonify({'success': False, 'message': '充值失败：余额未更新'})
    except Exception as e:
        db.session.rollback()
        print(f"充值失败：{str(e)}")
        return jsonify({'success': False, 'message': f'充值失败：{str(e)}'})

# 充值记录页面
@user_bp.route('/user/recharge-records')
@user_required
def recharge_records():
    user = User.query.get(session['user_id'])
    
    # 获取用户的充值记录，按时间倒序排序
    recharge_records = RechargeRecord.query.filter_by(user_id=user.id).order_by(
        RechargeRecord.created_at.desc()
    ).all()
    
    return render_template('user/recharge_record.html', user=user, recharge_records=recharge_records)

# 茶叶种类页面
@user_bp.route('/user/teas')
@user_required
def teas():
    user = User.query.get(session['user_id'])
    
    # 获取所有茶叶种类
    teas = Tea.query.all()
    
    return render_template('user/teas.html', user=user, teas=teas)

# 会员充值页面
@user_bp.route('/user/member-recharge', methods=['GET', 'POST'])
@user_required
def member_recharge():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            months = int(request.form.get('months', 1))
            payment_method = request.form.get('payment_method')
            amount = float(request.form.get('amount', 0.0))
            
            # 验证参数
            if not payment_method:
                flash('请选择支付方式', 'error')
                return redirect(url_for('user_frontend.member_recharge'))
            
            if months < 1 or months > 12:
                flash('会员月数必须在1-12之间', 'error')
                return redirect(url_for('user_frontend.member_recharge'))
            
            if amount <= 0:
                flash('充值金额必须大于0', 'error')
                return redirect(url_for('user_frontend.member_recharge'))
            
            # 检查用户余额是否足够
            if user.balance < amount:
                flash('账户余额不足，请先充值', 'error')
                return redirect(url_for('user_frontend.recharge'))
            
            # 计算会员到期时间
            if user.member_expires_at and user.member_expires_at > datetime.now():
                # 续费，从当前到期时间开始计算
                member_expires_at = user.member_expires_at + timedelta(days=30*months)
            else:
                # 新开会员，从当前时间开始计算
                member_expires_at = datetime.now() + timedelta(days=30*months)
            
            # 开始事务
            try:
                # 扣减用户余额
                user.balance -= amount
                
                # 更新会员信息
                user.is_member = True
                user.member_level = 1
                user.member_expires_at = member_expires_at
                
                # 创建会员充值记录
                member_record = MemberRecord(
                    user_id=user.id,
                    amount=amount,
                    months=months,
                    payment_method=payment_method,
                    status='success'
                )
                db.session.add(member_record)
                db.session.commit()
                
                flash(f'会员充值成功！会员有效期至{member_expires_at.strftime("%Y-%m-%d")}', 'success')
                return redirect(url_for('user_frontend.profile'))
            except Exception as e:
                db.session.rollback()
                flash(f'会员充值失败：{str(e)}', 'error')
                return redirect(url_for('user_frontend.member_recharge'))
        except Exception as e:
            flash(f'会员充值失败：{str(e)}', 'error')
            return redirect(url_for('user_frontend.member_recharge'))
    
    return render_template('user/member_recharge.html', user=user)

# 忘记密码页面
@user_bp.route('/user/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        verification_code = request.form.get('verification_code', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 验证手机号
        if not phone:
            flash('手机号不能为空', 'error')
            return render_template('user/forgot_password.html')
        
        if not re.match(r'^1[3-9]\d{9}$', phone):
            flash('请输入有效的11位手机号', 'error')
            return render_template('user/forgot_password.html')
        
        # 查找用户
        user = User.query.filter_by(phone=phone).first()
        if not user:
            flash('该手机号未注册', 'error')
            return render_template('user/forgot_password.html')
        
        # 验证验证码（这里简化处理，实际应该验证发送的验证码）
        if not verification_code:
            flash('请输入验证码', 'error')
            return render_template('user/forgot_password.html')
        
        # 验证密码
        if not new_password:
            flash('请输入新密码', 'error')
            return render_template('user/forgot_password.html')
        
        if len(new_password) < 5 or len(new_password) > 20:
            flash('密码长度必须在5-20个字符之间', 'error')
            return render_template('user/forgot_password.html')
        
        if not re.search(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', new_password):
            flash('密码必须包含大小写字母和数字', 'error')
            return render_template('user/forgot_password.html')
        
        if new_password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('user/forgot_password.html')
        
        # 重置密码
        try:
            user.set_password(new_password)
            db.session.commit()
            flash('密码重置成功，请使用新密码登录', 'success')
            return redirect(url_for('user_frontend.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'密码重置失败：{str(e)}', 'error')
            return render_template('user/forgot_password.html')
    
    return render_template('user/forgot_password.html')

# 报修相关路由

# 我的报修列表
@user_bp.route('/user/repairs')
@user_required
def repair_list():
    from models import Repair
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    
    # 构建查询
    query = Repair.query.filter_by(user_id=session['user_id'])
    
    # 状态筛选
    if status and status in ['pending', 'processing', 'completed', 'closed']:
        query = query.filter_by(status=status)
    
    # 排序和分页
    pagination = query.order_by(Repair.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    repairs_data = []
    for repair in pagination.items:
        repair_dict = {
            'id': repair.id,
            'room_id': repair.room_id,
            'title': repair.title,
            'status': repair.status,
            'priority': repair.priority,
            'created_at': repair.created_at,
            'updated_at': repair.updated_at
        }
        if repair.room:
            repair_dict['room_name'] = repair.room.name
        repairs_data.append(repair_dict)
    
    return render_template('user/repair_list.html',
                        repairs=repairs_data,
                        page=page,
                        total_pages=pagination.pages)

# 提交报修页面
@user_bp.route('/user/repair/submit')
@user_required
def repair_submit():
    rooms = Room.query.all()
    return render_template('user/repair_submit.html', rooms=rooms)
