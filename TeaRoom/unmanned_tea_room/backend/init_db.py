from app import create_app
from models import db, User, Room, RechargeRecord
from werkzeug.security import generate_password_hash

def init_db():
    app = create_app()
    
    with app.app_context():
        db.create_all()
        
        if User.query.filter_by(username='admin').first():
            print('管理员账号已存在')
        else:
            admin = User(
                username='admin',
                phone='13800138000',
                real_name='管理员',
                email='admin@tearoom.com',
                is_admin=True,
                balance=10000.0
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print('创建管理员账号: admin / admin123')
        
        # 添加移动端测试账号
        if User.query.filter_by(phone='13800138001').first():
            print('测试账号已存在')
        else:
            test_user = User(
                username='13800138001',
                phone='13800138001',
                real_name='测试用户',
                email='test@tearoom.com',
                is_admin=False,
                balance=500.0
            )
            test_user.set_password('test123')
            db.session.add(test_user)
            print('创建测试账号: 13800138001 / test123')
        
        if Room.query.count() == 0:
            rooms_data = [
                {
                    'name': '雅韵茶室',
                    'description': '古朴典雅的中式茶室，配备全套茶具和优质茶叶',
                    'capacity': 4,
                    'price_per_hour': 50.0,
                    'facilities': '茶具,空调,免费WiFi,独立卫生间',
                    'floor': 1
                },
                {
                    'name': '禅意茶室',
                    'description': '简约禅意的日式茶室，适合冥想和品茶',
                    'capacity': 2,
                    'price_per_hour': 40.0,
                    'facilities': '茶具,空调,免费WiFi,榻榻米',
                    'floor': 1
                },
                {
                    'name': '商务茶室',
                    'description': '宽敞明亮的商务茶室，适合商务洽谈',
                    'capacity': 8,
                    'price_per_hour': 80.0,
                    'facilities': '茶具,空调,免费WiFi,投影仪,白板',
                    'floor': 2
                },
                {
                    'name': '阳光茶室',
                    'description': '采光良好的阳光茶室，环境舒适温馨',
                    'capacity': 6,
                    'price_per_hour': 60.0,
                    'facilities': '茶具,空调,免费WiFi,落地窗',
                    'floor': 2
                },
                {
                    'name': '私密茶室',
                    'description': '高度私密的独立茶室，适合重要会谈',
                    'capacity': 4,
                    'price_per_hour': 70.0,
                    'facilities': '茶具,空调,免费WiFi,隔音墙,独立卫生间',
                    'floor': 3
                },
                {
                    'name': '景观茶室',
                    'description': '视野开阔的景观茶室，可欣赏城市美景',
                    'capacity': 6,
                    'price_per_hour': 90.0,
                    'facilities': '茶具,空调,免费WiFi,全景窗,观景台',
                    'floor': 3
                }
            ]
            
            for room_data in rooms_data:
                room = Room(**room_data)
                db.session.add(room)
            
            print(f'创建 {len(rooms_data)} 个茶室房间')
        
        db.session.commit()
        print('数据库初始化完成')

if __name__ == '__main__':
    init_db()