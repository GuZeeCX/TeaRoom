from flask import jsonify

# 成功响应
def success_response(data=None, message='操作成功'):
    response = {
        'code': 200,
        'message': message
    }
    if data is not None:
        response['data'] = data
    return jsonify(response), 200

# 错误响应
def error_response(code=400, message='操作失败'):
    return jsonify({
        'code': code,
        'message': message
    }), code

# 未授权响应
def unauthorized_response(message='未授权访问'):
    return jsonify({
        'code': 401,
        'message': message
    }), 401

# 禁止访问响应
def forbidden_response(message='禁止访问'):
    return jsonify({
        'code': 403,
        'message': message
    }), 403

# 资源不存在响应
def not_found_response(message='资源不存在'):
    return jsonify({
        'code': 404,
        'message': message
    }), 404

# 服务器错误响应
def server_error_response(message='服务器内部错误'):
    return jsonify({
        'code': 500,
        'message': message
    }), 500

# 验证错误响应
def validation_error_response(message='参数验证失败'):
    return jsonify({
        'code': 422,
        'message': message
    }), 422

# 分页响应
def paginated_response(data, total, page, per_page):
    return jsonify({
        'code': 200,
        'message': '操作成功',
        'data': data,
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    }), 200