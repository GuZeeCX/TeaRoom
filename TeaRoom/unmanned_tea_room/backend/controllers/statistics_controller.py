from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.statistics_service import StatisticsService
from utils.response import success_response, error_response, unauthorized_response
from utils.helpers import error_handler

statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')

@statistics_bp.route('/revenue', methods=['GET'])
@error_handler
def get_revenue_statistics():
    """获取营收统计"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    group_by = request.args.get('group_by', 'day')
    return StatisticsService.get_revenue_statistics(start_date, end_date, group_by)

@statistics_bp.route('/room-usage', methods=['GET'])
@error_handler
def get_room_usage_statistics():
    """获取房间使用率统计"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    return StatisticsService.get_room_usage_statistics(start_date, end_date)

@statistics_bp.route('/orders', methods=['GET'])
@error_handler
def get_order_statistics():
    """获取订单统计"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    return StatisticsService.get_order_statistics(start_date, end_date)

@statistics_bp.route('/users', methods=['GET'])
@error_handler
def get_user_statistics():
    """获取用户统计"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    return StatisticsService.get_user_statistics(start_date, end_date)

@statistics_bp.route('/daily', methods=['GET'])
@error_handler
def get_daily_statistics():
    """获取指定日期的统计信息"""
    date = request.args.get('date')
    return StatisticsService.get_daily_statistics(date)