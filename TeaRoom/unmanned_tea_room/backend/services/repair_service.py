import os
import uuid
from datetime import datetime
from models import db, Repair, Room, User, Order
from utils.response import success_response, error_response, not_found_response, paginated_response, forbidden_response
from utils.helpers import generate_order_no

class RepairService:
    # 允许的状态流转（管理员可修改为任意状态）
    STATUS_FLOW = {
        'pending': ['processing', 'completed', 'closed'],
        'processing': ['pending', 'completed', 'closed'],
        'completed': ['pending', 'processing', 'closed'],
        'closed': ['pending', 'processing', 'completed']
    }
    
    ALLOWED_STATUSES = ['pending', 'processing', 'completed', 'closed']
    ALLOWED_PRIORITIES = ['low', 'normal', 'high']
    
    @staticmethod
    def submit_repair(user_id, data, files=None):
        """提交报修工单"""
        room_id = data.get('room_id')
        order_id = data.get('order_id')
        title = data.get('title')
        description = data.get('description')
        priority = data.get('priority', 'normal')
        
        # 验证必选字段
        if not room_id or not title or not description:
            return error_response(400, '缺少必要参数：茶室、标题、描述不能为空')
        
        # 验证标题长度
        if len(title) > 50:
            return error_response(400, '标题不能超过50字')
        
        # 验证描述长度
        if len(description) > 200:
            return error_response(400, '描述不能超过200字')
        
        # 验证优先级
        if priority not in RepairService.ALLOWED_PRIORITIES:
            return error_response(400, '优先级值无效')
        
        # 验证茶室是否存在
        room = Room.query.get(room_id)
        if not room:
            return not_found_response('茶室不存在')
        
        # 验证订单（如果有）
        if order_id:
            order = Order.query.get(order_id)
            if not order:
                return not_found_response('订单不存在')
            # 验证订单归属
            if order.user_id != user_id:
                return error_response(403, '无权操作此订单')
        
        # 处理图片上传
        image_paths = []
        if files and 'images' in files:
            images = files.getlist('images')
            max_images = 3
            max_size = 2 * 1024 * 1024  # 2MB
            
            if len(images) > max_images:
                return error_response(400, f'最多只能上传{max_images}张图片')
            
            for image in images:
                # 验证文件大小
                if len(image.read()) > max_size:
                    return error_response(400, '单张图片大小不能超过2MB')
                image.seek(0)  # 重置文件指针
                
                # 验证文件类型（通过文件头）
                content_type = image.content_type
                if content_type not in ['image/jpeg', 'image/png', 'image/jpg']:
                    return error_response(400, '图片格式仅限jpg/png')
                
                # 生成保存路径
                today = datetime.now().strftime('%Y/%m/%d')
                upload_dir = os.path.join('uploads', 'repair', today)
                os.makedirs(upload_dir, exist_ok=True)
                
                # 生成文件名
                file_ext = image.filename.split('.')[-1]
                file_name = f"{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}.{file_ext}"
                file_path = os.path.join(upload_dir, file_name)
                
                # 保存文件
                image.save(file_path)
                image_paths.append(f'/uploads/repair/{today}/{file_name}')
        
        # 创建工单
        try:
            repair = Repair(
                user_id=user_id,
                room_id=room_id,
                order_id=order_id,
                title=title,
                description=description,
                images=','.join(image_paths) if image_paths else None,
                status='pending',
                priority=priority
            )
            
            db.session.add(repair)
            db.session.commit()
            
            return success_response(repair.to_dict(), '报修提交成功')
        except Exception as e:
            db.session.rollback()
            # 清理已上传的图片
            for path in image_paths:
                try:
                    os.remove(os.path.join('backend', path.lstrip('/')))
                except:
                    pass
            return error_response(500, f'提交失败: {str(e)}')
    
    @staticmethod
    def get_user_repairs(user_id, page=1, per_page=10, status=None):
        """获取指定用户的报修列表"""
        query = Repair.query.filter_by(user_id=user_id)
        
        if status and status in RepairService.ALLOWED_STATUSES:
            query = query.filter_by(status=status)
        
        pagination = query.order_by(Repair.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        repairs = []
        for repair in pagination.items:
            repair_dict = repair.to_dict()
            repairs.append(repair_dict)
        
        return success_response({
            'repairs': repairs,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        })
    
    @staticmethod
    def get_repair_detail(repair_id, user_id=None):
        """获取工单详情"""
        repair = Repair.query.get(repair_id)
        if not repair:
            return not_found_response('工单不存在')
        
        # 如果是普通用户查询，校验归属权
        if user_id and repair.user_id != user_id:
            return forbidden_response('无权查看此工单')
        
        repair_dict = repair.to_dict()
        
        # 添加用户信息
        if repair.user:
            repair_dict['user_phone'] = repair.user.phone
        
        return success_response(repair_dict)
    
    @staticmethod
    def get_all_repairs(page=1, per_page=10, status=None, room_id=None, keyword=None):
        """管理员获取全部工单列表"""
        query = Repair.query
        
        # 状态筛选
        if status and status in RepairService.ALLOWED_STATUSES:
            query = query.filter_by(status=status)
        
        # 茶室筛选
        if room_id:
            query = query.filter_by(room_id=room_id)
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                (Repair.title.ilike(f'%{keyword}%')) |
                (Repair.description.ilike(f'%{keyword}%'))
            )
        
        pagination = query.order_by(Repair.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        repairs = []
        for repair in pagination.items:
            repair_dict = repair.to_dict()
            repairs.append(repair_dict)
        
        # 统计待处理数量
        pending_count = Repair.query.filter_by(status='pending').count()
        
        return success_response({
            'repairs': repairs,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages,
            'pending_count': pending_count
        })
    
    @staticmethod
    def update_status(repair_id, status, remark=None):
        """管理员更新工单状态"""
        repair = Repair.query.get(repair_id)
        if not repair:
            return not_found_response('工单不存在')
        
        # 验证状态值
        if status not in RepairService.ALLOWED_STATUSES:
            return error_response(400, '状态值无效')
        
        # 验证状态流转
        if status not in RepairService.STATUS_FLOW.get(repair.status, []):
            return error_response(400, f'状态无法从"{repair.status_text}"变更为"{status}"')
        
        try:
            repair.status = status
            if remark:
                repair.handler_remark = remark
            
            db.session.commit()
            return success_response(repair.to_dict(), '状态更新成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'更新失败: {str(e)}')
    
    @staticmethod
    def delete_repair(repair_id):
        """管理员删除工单"""
        repair = Repair.query.get(repair_id)
        if not repair:
            return not_found_response('工单不存在')
        
        # 删除关联图片
        if repair.images:
            for image_path in repair.images.split(','):
                try:
                    full_path = os.path.join('backend', image_path.lstrip('/'))
                    if os.path.exists(full_path):
                        os.remove(full_path)
                except:
                    pass
        
        try:
            db.session.delete(repair)
            db.session.commit()
            return success_response({}, '工单删除成功')
        except Exception as e:
            db.session.rollback()
            return error_response(500, f'删除失败: {str(e)}')
    
    @staticmethod
    def get_pending_count():
        """获取待处理工单数量"""
        count = Repair.query.filter_by(status='pending').count()
        return success_response({'pending_count': count})