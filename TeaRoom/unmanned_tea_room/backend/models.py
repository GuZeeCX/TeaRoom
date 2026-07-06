from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    real_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    balance = db.Column(db.Float, default=0.0)
    is_member = db.Column(db.Boolean, default=False)
    member_level = db.Column(db.Integer, default=1)
    member_expires_at = db.Column(db.DateTime)
    total_consumption = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'phone': self.phone,
            'real_name': self.real_name,
            'email': self.email,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'balance': self.balance,
            'is_member': self.is_member,
            'member_level': self.member_level,
            'member_expires_at': self.member_expires_at.isoformat() if self.member_expires_at else None,
            'total_consumption': self.total_consumption,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Room(db.Model):
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    capacity = db.Column(db.Integer, default=4)
    price_per_hour = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255))
    facilities = db.Column(db.Text)
    status = db.Column(db.String(20), default='available')
    floor = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='room', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='room', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'capacity': self.capacity,
            'price_per_hour': self.price_per_hour,
            'image_url': self.image_url,
            'facilities': self.facilities,
            'status': self.status,
            'floor': self.floor,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False, index=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))  # 关联预约
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration_hours = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_status = db.Column(db.String(20), default='unpaid')
    qr_code = db.Column(db.String(255))
    check_in_time = db.Column(db.DateTime)
    check_out_time = db.Column(db.DateTime)
    door_code = db.Column(db.String(6))  # 开门验证码（6位数字）
    payment_type = db.Column(db.String(20), default='immediate')  # 支付方式：immediate立即支付，postpay后付
    tea_type = db.Column(db.String(50), default='默认免费茶')  # 茶叶品类
    tea_price = db.Column(db.Float, default=0.0)  # 茶叶加价
    tea_weight = db.Column(db.Float, default=0.0)  # 茶叶重量（克）
    tea_unit_price = db.Column(db.Float, default=0.0)  # 茶叶单价（元/克）
    package_type = db.Column(db.String(50), default='按小时计费')  # 套餐类型
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_no': self.order_no,
            'user_id': self.user_id,
            'room_id': self.room_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_hours': self.duration_hours,
            'total_amount': self.total_amount,
            'status': self.status,
            'payment_status': self.payment_status,
            'qr_code': self.qr_code,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'tea_type': self.tea_type,
            'tea_price': self.tea_price,
            'tea_weight': self.tea_weight,
            'tea_unit_price': self.tea_unit_price,
            'package_type': self.package_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_no = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration_hours = db.Column(db.Float, nullable=False)
    estimated_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='confirmed')
    tea_type = db.Column(db.String(50), default='默认免费茶')  # 茶叶品类
    tea_price = db.Column(db.Float, default=0.0)  # 茶叶加价
    tea_weight = db.Column(db.Float, default=0.0)  # 茶叶重量（克）
    tea_unit_price = db.Column(db.Float, default=0.0)  # 茶叶单价（元/克）
    package_type = db.Column(db.String(50), default='按小时计费')  # 套餐类型
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'booking_no': self.booking_no,
            'user_id': self.user_id,
            'room_id': self.room_id,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_hours': self.duration_hours,
            'estimated_amount': self.estimated_amount,
            'status': self.status,
            'tea_type': self.tea_type,
            'tea_price': self.tea_price,
            'tea_weight': self.tea_weight,
            'tea_unit_price': self.tea_unit_price,
            'package_type': self.package_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RechargeRecord(db.Model):
    __tablename__ = 'recharge_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='success')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='recharge_records', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5星
    comment = db.Column(db.Text)  # 文字评价
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='reviews', lazy=True)
    room = db.relationship('Room', backref='reviews', lazy=True)
    order = db.relationship('Order', backref='review', lazy=True, uselist=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'room_id': self.room_id,
            'order_id': self.order_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'username': self.user.username if self.user else None
        }

class Tea(db.Model):
    __tablename__ = 'teas'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # 茶叶名称
    price = db.Column(db.Float, nullable=False)  # 价格
    stock = db.Column(db.Integer, default=100)  # 库存
    description = db.Column(db.Text)  # 描述
    image_url = db.Column(db.String(255))  # 图片URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'stock': self.stock,
            'description': self.description,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class MemberRecord(db.Model):
    __tablename__ = 'member_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # 充值金额
    months = db.Column(db.Integer, nullable=False)  # 会员月数
    payment_method = db.Column(db.String(20), nullable=False)  # 支付方式
    status = db.Column(db.String(20), default='success')  # 状态
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Repair(db.Model):
    __tablename__ = 'repairs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    images = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')  # pending/processing/completed/closed
    priority = db.Column(db.String(10), default='normal')  # low/normal/high
    handler_remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='repairs', lazy=True)
    room = db.relationship('Room', backref='repairs', lazy=True)
    order = db.relationship('Order', backref='repairs', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'room_id': self.room_id,
            'order_id': self.order_id,
            'title': self.title,
            'description': self.description,
            'images': self.images.split(',') if self.images else [],
            'status': self.status,
            'priority': self.priority,
            'handler_remark': self.handler_remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_real_name': self.user.real_name if self.user else None,
            'room_name': self.room.name if self.room else None,
            'order_no': self.order.order_no if self.order else None
        }
    
    @property
    def status_text(self):
        status_map = {
            'pending': '待处理',
            'processing': '处理中',
            'completed': '已完成',
            'closed': '已关闭'
        }
        return status_map.get(self.status, self.status)
    
    @property
    def priority_text(self):
        priority_map = {
            'low': '低',
            'normal': '一般',
            'high': '紧急'
        }
        return priority_map.get(self.priority, self.priority)