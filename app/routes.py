from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, logout_user, login_user
from app.models import User
from app import db

# 创建蓝图
main_bp = Blueprint('main', __name__)

# 首页
@main_bp.route('/')
@main_bp.route('/index')
def index():
    """首页路由"""
    return render_template('index.html')

# 关于
@main_bp.route('/about')
def about():
    return render_template('about.html')

# 登录
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 已经处于登录状态
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    # 处理登录请求
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        # 查询用户
        user = User.query.filter_by(username=username).first()
        # 验证用户名和密码
        if user and user.check_password(password):
            # 登录用户
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('用户名或密码错误', 'danger')
            return redirect(url_for('auth/main.login'))
    # 渲染登录页面
    return render_template('auth/login.html')

# 注册
@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        email = request.form.get('email', '').strip()
        # 检查输入是否为空
        if not username or not password or not email:
            flash('请填写完整信息', 'danger')
            return redirect(url_for('auth/main.register'))
        
        # 检查用户名是否已存在
        ExistingUser = User.query.filter_by(username=username).first()
        if ExistingUser:
            flash('用户名已存在', 'danger')
            return redirect(url_for('auth/main.register'))
        # 创建新用户
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth/main.login'))
    
    return render_template('auth/register.html')

# 登出
@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# 文章
@main_bp.route('/post')
def article():
    return render_template('post.html')

# 文章详情
@main_bp.route('/post/<int:post_id>')
def post_detail(post_id):
    return render_template('detail.html')

# 写文章
@main_bp.route('/post/create')
def new_post():
    return render_template('create.html')

@main_bp.route('/guga')
def guga():
    return render_template('guga/guga.html',
                           background_image_url=url_for('static', filename='guga/MyGO_background.png'),
                           panel_image_url=url_for('static', filename='guga/gugugaga.png')
                           )

@main_bp.route('/guga/chat')
def guga_chat():
    return render_template('guga/chat.html',
                           background_image_url=url_for('static', filename='guga/MyGO_background.png')
                           )

@main_bp.route('/guli')
def guli():
    text = "灵感菇里菇里菇里瓜恰~\n灵感菇灵感菇~\n"
    return render_template('guga/guli.html', text=text)

