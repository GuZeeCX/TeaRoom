from controllers.user_controller import user_bp
from controllers.room_controller import room_bp
from controllers.booking_controller import booking_bp
from controllers.order_controller import order_bp
from controllers.access_controller import access_bp
from controllers.statistics_controller import statistics_bp
from controllers.review_controller import review_bp
from controllers.repair_controller import repair_bp

# 注册所有蓝图
def register_blueprints(app):
    app.register_blueprint(user_bp)
    app.register_blueprint(room_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(access_bp)
    app.register_blueprint(statistics_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(repair_bp)

# 蓝图列表
blueprints = [
    user_bp,
    room_bp,
    booking_bp,
    order_bp,
    access_bp,
    statistics_bp,
    review_bp,
    repair_bp
]