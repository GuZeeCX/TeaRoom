from models import db, Order, Room, Booking, User
from utils.helpers import calculate_duration_hours
from utils.response import success_response, error_response
from datetime import datetime, timedelta, date

class StatisticsService:
    @staticmethod
    def get_revenue_statistics(start_date=None, end_date=None, group_by='day'):
        """获取营收统计"""
        # 构建查询
        query = db.session.query(
            db.func.sum(Order.total_amount).label('total_amount'),
            db.func.count(Order.id).label('order_count')
        ).filter(
            Order.status == 'completed',
            Order.payment_status == 'paid'
        )
        
        # 日期筛选
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date)
                query = query.filter(Order.created_at >= start_date)
            except:
                return error_response(400, '开始日期格式错误')
        else:
            # 默认查询最近30天
            start_date = datetime.now() - timedelta(days=30)
            query = query.filter(Order.created_at >= start_date)
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date)
                query = query.filter(Order.created_at <= end_date)
            except:
                return error_response(400, '结束日期格式错误')
        else:
            # 默认查询到今天
            end_date = datetime.now()
            query = query.filter(Order.created_at <= end_date)
        
        # 按日/月/年分组
        if group_by == 'day':
            query = query.add_columns(
                db.func.date(Order.created_at).label('date')
            ).group_by(
                db.func.date(Order.created_at)
            ).order_by(
                db.func.date(Order.created_at)
            )
        elif group_by == 'month':
            query = query.add_columns(
                db.func.strftime('%Y-%m', Order.created_at).label('month')
            ).group_by(
                db.func.strftime('%Y-%m', Order.created_at)
            ).order_by(
                db.func.strftime('%Y-%m', Order.created_at)
            )
        elif group_by == 'year':
            query = query.add_columns(
                db.func.strftime('%Y', Order.created_at).label('year')
            ).group_by(
                db.func.strftime('%Y', Order.created_at)
            ).order_by(
                db.func.strftime('%Y', Order.created_at)
            )
        else:
            return error_response(400, '无效的分组方式')
        
        # 执行查询
        results = query.all()
        
        # 格式化结果
        statistics = []
        for result in results:
            statistics.append({
                'period': result[2],
                'revenue': float(result[0]) if result[0] else 0,
                'order_count': result[1] or 0
            })
        
        # 计算总计
        total_revenue = sum(item['revenue'] for item in statistics)
        total_orders = sum(item['order_count'] for item in statistics)
        
        return success_response({
            'statistics': statistics,
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'group_by': group_by
        })
    
    @staticmethod
    def get_room_usage_statistics(start_date=None, end_date=None):
        """获取房间使用率统计"""
        # 日期筛选
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date)
            except:
                return error_response(400, '开始日期格式错误')
        else:
            # 默认查询最近30天
            start_date = datetime.now() - timedelta(days=30)
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date)
            except:
                return error_response(400, '结束日期格式错误')
        else:
            # 默认查询到今天
            end_date = datetime.now()
        
        # 计算时间范围的总小时数
        total_hours = (end_date - start_date).total_seconds() / 3600
        
        # 获取所有房间
        rooms = Room.query.all()
        
        usage_statistics = []
        
        for room in rooms:
            # 获取房间的已完成订单
            orders = Order.query.filter(
                Order.room_id == room.id,
                Order.status == 'completed',
                Order.start_time >= start_date,
                Order.end_time <= end_date
            ).all()
            
            # 计算使用总小时数
            total_usage_hours = 0
            for order in orders:
                if order.check_in_time and order.check_out_time:
                    usage_hours = calculate_duration_hours(
                        order.check_in_time, order.check_out_time
                    )
                    total_usage_hours += usage_hours
                else:
                    # 如果没有签到签退时间，使用预约时长
                    total_usage_hours += order.duration_hours
            
            # 计算使用率
            usage_rate = (total_usage_hours / total_hours) * 100 if total_hours > 0 else 0
            
            usage_statistics.append({
                'room_id': room.id,
                'room_name': room.name,
                'total_hours': round(total_hours, 2),
                'usage_hours': round(total_usage_hours, 2),
                'usage_rate': round(usage_rate, 2),
                'order_count': len(orders)
            })
        
        # 计算总体使用率
        total_room_hours = total_hours * len(rooms)
        total_usage_hours = sum(item['usage_hours'] for item in usage_statistics)
        overall_usage_rate = (total_usage_hours / total_room_hours) * 100 if total_room_hours > 0 else 0
        
        return success_response({
            'statistics': usage_statistics,
            'overall_usage_rate': round(overall_usage_rate, 2),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
    
    @staticmethod
    def get_order_statistics(start_date=None, end_date=None):
        """获取订单统计"""
        # 日期筛选
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date)
            except:
                return error_response(400, '开始日期格式错误')
        else:
            # 默认查询最近30天
            start_date = datetime.now() - timedelta(days=30)
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date)
            except:
                return error_response(400, '结束日期格式错误')
        else:
            # 默认查询到今天
            end_date = datetime.now()
        
        # 按状态分组
        status_statistics = db.session.query(
            Order.status,
            db.func.count(Order.id).label('count'),
            db.func.sum(Order.total_amount).label('amount')
        ).filter(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        ).group_by(
            Order.status
        ).all()
        
        # 按支付状态分组
        payment_statistics = db.session.query(
            Order.payment_status,
            db.func.count(Order.id).label('count'),
            db.func.sum(Order.total_amount).label('amount')
        ).filter(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        ).group_by(
            Order.payment_status
        ).all()
        
        # 格式化结果
        status_stats = []
        for status, count, amount in status_statistics:
            status_stats.append({
                'status': status,
                'count': count or 0,
                'amount': float(amount) if amount else 0
            })
        
        payment_stats = []
        for status, count, amount in payment_statistics:
            payment_stats.append({
                'status': status,
                'count': count or 0,
                'amount': float(amount) if amount else 0
            })
        
        # 计算总计
        total_orders = sum(item['count'] for item in status_stats)
        total_amount = sum(item['amount'] for item in status_stats)
        
        return success_response({
            'status_statistics': status_stats,
            'payment_statistics': payment_stats,
            'total_orders': total_orders,
            'total_amount': total_amount,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
    
    @staticmethod
    def get_user_statistics(start_date=None, end_date=None):
        """获取用户统计"""
        # 日期筛选
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date)
            except:
                return error_response(400, '开始日期格式错误')
        else:
            # 默认查询最近30天
            start_date = datetime.now() - timedelta(days=30)
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date)
            except:
                return error_response(400, '结束日期格式错误')
        else:
            # 默认查询到今天
            end_date = datetime.now()
        
        # 注册用户数
        new_users = User.query.filter(
            User.created_at >= start_date,
            User.created_at <= end_date
        ).count()
        
        # 活跃用户数（有订单的用户）
        active_users = db.session.query(
            db.func.count(db.func.distinct(Order.user_id))
        ).filter(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        ).scalar() or 0
        
        # 总用户数
        total_users = User.query.count()
        
        # 平均订单金额
        avg_order_amount = db.session.query(
            db.func.avg(Order.total_amount)
        ).filter(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed',
            Order.payment_status == 'paid'
        ).scalar() or 0
        
        # 平均订单时长
        avg_order_duration = db.session.query(
            db.func.avg(Order.duration_hours)
        ).filter(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        ).scalar() or 0
        
        return success_response({
            'total_users': total_users,
            'new_users': new_users,
            'active_users': active_users,
            'avg_order_amount': round(float(avg_order_amount), 2),
            'avg_order_duration': round(float(avg_order_duration), 2),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
    
    @staticmethod
    def get_daily_statistics(date=None):
        """获取指定日期的统计信息"""
        if not date:
            date = datetime.now().date()
        else:
            try:
                date = datetime.fromisoformat(date).date()
            except:
                return error_response(400, '日期格式错误')
        
        # 开始和结束时间
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())
        
        # 当日订单数
        daily_orders = Order.query.filter(
            Order.created_at >= start_time,
            Order.created_at <= end_time
        ).count()
        
        # 当日营收
        daily_revenue = db.session.query(
            db.func.sum(Order.total_amount)
        ).filter(
            Order.created_at >= start_time,
            Order.created_at <= end_time,
            Order.status == 'completed',
            Order.payment_status == 'paid'
        ).scalar() or 0
        
        # 当日活跃用户
        active_users = db.session.query(
            db.func.count(db.func.distinct(Order.user_id))
        ).filter(
            Order.created_at >= start_time,
            Order.created_at <= end_time
        ).scalar() or 0
        
        # 当日预约数
        daily_bookings = Booking.query.filter(
            Booking.created_at >= start_time,
            Booking.created_at <= end_time
        ).count()
        
        return success_response({
            'date': date.isoformat(),
            'orders': daily_orders,
            'revenue': float(daily_revenue),
            'active_users': active_users,
            'bookings': daily_bookings
        })