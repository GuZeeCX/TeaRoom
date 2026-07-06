import random
import string
import datetime
import jwt
import hashlib
import secrets
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

# 生成随机字符串
def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# 生成订单号
def generate_order_no():
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = generate_random_string(6)
    return f'ORD{timestamp}{random_str}'

# 生成预约号
def generate_booking_no():
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = generate_random_string(6)
    return f'BOOK{timestamp}{random_str}'

# 生成验证码
def generate_verification_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

# 计算订单金额
def calculate_order_amount(price_per_hour, duration_hours):
    return round(price_per_hour * duration_hours, 2)

# 验证时间范围是否有效
def validate_time_range(start_time, end_time):
    if start_time >= end_time:
        return False
    if start_time < datetime.datetime.now():
        return False
    return True

# 检查房间是否在指定时间段内可用
def is_room_available(room_id, start_time, end_time, exclude_order_id=None):
    from models import Order
    from datetime import datetime
    
    # 检查是否有冲突的订单
    orders = Order.query.filter(
        Order.room_id == room_id,
        Order.status.in_(['pending', 'confirmed', 'in_use']),
        Order.start_time < end_time,
        Order.end_time > start_time
    )
    
    if exclude_order_id:
        orders = orders.filter(Order.id != exclude_order_id)
    
    return orders.count() == 0

# 错误处理装饰器
def error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return wrapper

# 验证请求参数
def validate_request_params(required_params):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({'error': '请求参数不能为空'}), 400
            
            missing_params = [param for param in required_params if param not in data]
            if missing_params:
                return jsonify({'error': f'缺少必要参数: {missing_params}'}), 400
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 生成JWT token
def generate_token(user_id):
    from config import Config
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.now() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')

# 验证JWT token
def verify_token(token):
    from config import Config
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        return payload
    except:
        return None

# 生成密码哈希
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 验证密码
def verify_password(hashed_password, password):
    return hashed_password == hashlib.sha256(password.encode()).hexdigest()

# 生成安全的随机token
def generate_secure_token(length=32):
    return secrets.token_hex(length)

# 格式化日期时间
def format_datetime(dt):
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return None

# 格式化日期
def format_date(date):
    if date:
        return date.strftime('%Y-%m-%d')
    return None

# 计算时间差（小时）
def calculate_duration_hours(start_time, end_time):
    if not start_time or not end_time:
        return 0
    delta = end_time - start_time
    return round(delta.total_seconds() / 3600, 2)

# 检查是否是工作日
def is_weekday(date):
    return date.weekday() < 5

# 检查是否是节假日（简单实现，实际项目需要接入节假日API）
def is_holiday(date):
    # 这里可以实现节假日判断逻辑
    return False

# 生成二维码内容
def generate_qr_code_content(order_id, room_id):
    return f'tearoom://open?order_id={order_id}&room_id={room_id}'