from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, logout_user

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
@main_bp.route('/login')
def login():
    return render_template('login.html')

# 注册
@main_bp.route('/register')
def register():
    return render_template('register.html')

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

