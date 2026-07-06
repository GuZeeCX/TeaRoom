from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db

# 直接从 routes_config.py 文件导入
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from routes_config import register_blueprints

# 从 routes 目录下的 admin.py 导入
from routes.admin import admin_bp
from routes.user import user_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    CORS(app)
    JWTManager(app)
    db.init_app(app)
    
    # 注册所有API蓝图
    register_blueprints(app)
    
    # 注册管理员后台蓝图
    app.register_blueprint(admin_bp)
    
    # 注册用户端蓝图
    app.register_blueprint(user_bp)
    
    # 根路由
    @app.route('/')
    def index():
        return render_template('admin/login.html')
    
    # 健康检查
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'}), 200
    
    # 404错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': '资源不存在'}), 404
    
    # 500错误处理
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': '服务器内部错误'}), 500
    
    return app

import socket

def find_available_port(start_port, max_attempts=10):
    """
    查找可用端口
    :param start_port: 起始端口
    :param max_attempts: 最大尝试次数
    :return: 可用端口
    """
    for port in range(start_port, start_port + max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # 尝试绑定端口
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except socket.error:
            # 端口已被占用，尝试下一个
            continue
    return None

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    
    # 查找可用端口
    port = find_available_port(5000)
    if port is None:
        port = find_available_port(8080)
    
    if port is None:
        print("无法找到可用端口，请手动指定端口")
    else:
        print(f"启动服务器，监听地址: 0.0.0.0:{port}")
        print(f"局域网访问地址: http://{socket.gethostbyname(socket.gethostname())}:{port}")
        print(f"本地访问地址: http://localhost:{port}")
        app.run(host='0.0.0.0', port=port, debug=True)