from models import db, User, RechargeRecord
from utils.helpers import generate_verification_code, hash_password, verify_password
from utils.response import success_response, error_response, not_found_response
from datetime import datetime

class UserService:
    @staticmethod
    def register(data):
        """用户注册"""
        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            return error_response(400, '用户名已存在')
        
        # 检查手机号是否已被注册
        if User.query.filter_by(phone=data['phone']).first():
            return error_response(400, '手机号已被注册')
        
        # 检查邮箱是否已被注册（如果提供）
        if data.get('email') and User.query.filter_by(email=data['email']).first():
            return error_response(400, '邮箱已被注册')
        
        # 创建用户
        user = User(
            username=data['username'],
            phone=data['phone'],
            real_name=data['real_name'],
            email=data.get('email'),
            balance=0.0
        )
        user.set_password(data['password'])
        
        try:
            db.session.add(user)
            db.session.commit()
            return success_response(user.to_dict(), '注册成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'注册失败: {str(e)}')
    
    @staticmethod
    def login(identifier, password):
        """用户登录"""
        # 支持用户名或手机号登录
        user = User.query.filter(
            (User.username == identifier) | (User.phone == identifier)
        ).first()
        
        if not user or not user.check_password(password):
            return error_response(401, '用户名或密码错误')
        
        return user
    
    @staticmethod
    def get_user_by_id(user_id):
        """根据ID获取用户信息"""
        user = User.query.get(user_id)
        if not user:
            return not_found_response('用户不存在')
        return success_response(user.to_dict())
    
    @staticmethod
    def update_profile(user_id, data):
        """更新用户信息"""
        user = User.query.get(user_id)
        if not user:
            return not_found_response('用户不存在')
        
        # 检查手机号是否被其他用户使用
        if 'phone' in data:
            existing_user = User.query.filter(
                User.phone == data['phone'],
                User.id != user_id
            ).first()
            if existing_user:
                return error_response(400, '手机号已被使用')
            user.phone = data['phone']
        
        # 检查邮箱是否被其他用户使用
        if 'email' in data:
            existing_user = User.query.filter(
                User.email == data['email'],
                User.id != user_id
            ).first()
            if existing_user:
                return error_response(400, '邮箱已被使用')
            user.email = data['email']
        
        # 更新其他信息
        if 'real_name' in data:
            user.real_name = data['real_name']
        
        try:
            db.session.commit()
            return success_response(user.to_dict(), '更新成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'更新失败: {str(e)}')
    
    @staticmethod
    def change_password(user_id, old_password, new_password):
        """修改密码"""
        user = User.query.get(user_id)
        if not user:
            return not_found_response('用户不存在')
        
        # 验证旧密码
        if not user.check_password(old_password):
            return error_response(400, '旧密码错误')
        
        # 设置新密码
        user.set_password(new_password)
        
        try:
            db.session.commit()
            return success_response(None, '密码修改成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'密码修改失败: {str(e)}')
    
    @staticmethod
    def get_verification_code(phone):
        """获取验证码"""
        # 这里可以实现发送验证码的逻辑
        # 实际项目中应该调用短信API
        code = generate_verification_code()
        # 模拟发送验证码
        print(f'向 {phone} 发送验证码: {code}')
        return success_response({'code': code}, '验证码发送成功')
    
    @staticmethod
    def verify_verification_code(phone, code):
        """验证验证码"""
        # 这里可以实现验证码验证逻辑
        # 实际项目中应该从缓存或数据库中获取验证码
        # 这里简化处理，直接返回成功
        return success_response(None, '验证码验证成功')
    
    @staticmethod
    def recharge_balance(user_id, amount, payment_method):
        """充值余额"""
        user = User.query.get(user_id)
        if not user:
            return not_found_response('用户不存在')
        
        if amount <= 0:
            return error_response(400, '充值金额必须大于0')
        
        # 更新用户余额
        user.balance += amount
        
        # 创建充值记录
        recharge_record = RechargeRecord(
            user_id=user_id,
            amount=amount,
            payment_method=payment_method,
            status='success'
        )
        
        try:
            db.session.add(recharge_record)
            db.session.commit()
            return success_response({'balance': user.balance}, '充值成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'充值失败: {str(e)}')
    
    @staticmethod
    def get_user_balance(user_id):
        """获取用户余额"""
        user = User.query.get(user_id)
        if not user:
            return not_found_response('用户不存在')
        
        return success_response({'balance': user.balance})
    
    @staticmethod
    def get_recharge_records(user_id, page=1, per_page=10):
        """获取充值记录"""
        user = User.query.get(user_id)
        if not user:
            return not_found_response('用户不存在')
        
        pagination = RechargeRecord.query.filter_by(
            user_id=user_id
        ).order_by(
            RechargeRecord.created_at.desc()
        ).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        records = []
        for record in pagination.items:
            records.append({
                'id': record.id,
                'amount': record.amount,
                'payment_method': record.payment_method,
                'status': record.status,
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return success_response({
            'records': records,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        })
    
    @staticmethod
    def list_users(page=1, per_page=10, search=None):
        """获取用户列表"""
        query = User.query
        
        if search:
            query = query.filter(
                (User.username.like(f'%{search}%')) |
                (User.phone.like(f'%{search}%')) |
                (User.real_name.like(f'%{search}%'))
            )
        
        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users = [user.to_dict() for user in pagination.items]
        
        return success_response({
            'users': users,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        })
    
    @staticmethod
    def delete_user(user_id):
        """删除用户"""
        user = User.query.get(user_id)
        if not user:
            return not_found_response('用户不存在')
        
        try:
            db.session.delete(user)
            db.session.commit()
            return success_response(None, '用户删除成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'用户删除失败: {str(e)}')