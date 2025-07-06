from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from config import Config

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
bcrypt = Bcrypt()

def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    
    # 配置Flask-Login
    login_manager.login_view = 'main.login'
    login_manager.login_message = '请先登录才能访问此页面。'
    login_manager.login_message_category = 'info'
    
    # 用户加载函数
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # 注册蓝图
    from app.routes import main_bp
    from app.guga_chat import guga_chat_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(guga_chat_bp)
    
    return app
