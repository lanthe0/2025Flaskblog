from app import create_app, db
from app.models import User
from flask_login import current_user

app = create_app()

# 创建上下文处理器，确保current_user在模板中可用
@app.context_processor
def inject_user():
    """注入用户信息到模板上下文"""
    return dict(current_user=current_user)

if __name__ == '__main__':
    with app.app_context():
        # 创建数据库表
        db.create_all()
    
    app.run(debug=True)
