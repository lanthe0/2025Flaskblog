from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, logout_user, login_user, login_required
from app.models import User, Post
from app import db
import markdown
from flask import Markup

# 创建蓝图
main_bp = Blueprint('main', __name__)

# 首页
@main_bp.route('/')
@main_bp.route('/index')
def index():
    """首页路由"""
    # 取最新6篇已发布文章
    posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).limit(6).all()
    return render_template('index.html', posts=posts)

# 关于
@main_bp.route('/about')
def about():
    return render_template('about.html')

# ===================== 用户相关 =====================
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
            return redirect(url_for('main.login'))
    # 渲染登录页面
    return render_template('user/login.html')

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
            return redirect(url_for('main.register'))
        
        # 检查用户名是否已存在
        ExistingUser = User.query.filter_by(username=username).first()
        if ExistingUser:
            flash('用户名已存在', 'danger')
            return redirect(url_for('main.register'))
        # 创建新用户
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('user/register.html')

# 登出
@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# 用户个人资料
@main_bp.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(author_id=user.id).order_by(Post.created_at.desc()).all()
    return render_template('user/profile.html', user=user, posts=posts)

# 用户编辑资料
@main_bp.route('/user/<int:user_id>/set')
def user_set(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user/set.html', user=user)

# 用户文章列表
@main_bp.route('/user/<int:user_id>/posts')
def user_posts(user_id):
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(author=user).all()
    return render_template('user/posts.html', user=user, posts=posts)

# 用户编辑资料
@main_bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:
        flash('无权操作他人资料', 'danger')
        return redirect(url_for('main.user_profile', user_id=user_id))
    if request.method == 'POST':
        user.username = request.form.get('username', '').strip()
        user.avatar_url = request.form.get('avatar_url', '').strip()
        user.bio = request.form.get('bio', '').strip()
        db.session.commit()
        flash('资料已更新', 'success')
        return redirect(url_for('main.user_profile', user_id=user_id))
    return render_template('user/edit_profile.html', user=user)

# ===================== 文章相关 =====================
# 文章总览
@main_bp.route('/post')
def post_list():
    posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).all()
    return render_template('post/post.html', posts=posts)

# 文章详情
@main_bp.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    html_content = Markup(markdown.markdown(
        post.content,
        extensions=['fenced_code', 'codehilite', 'tables', 'toc']
    ))
    return render_template('post/detail.html', post=post, html_content=html_content)

# 写新文章
@main_bp.route('/post/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', '默认')
        is_published = request.form.get('is_published', '1') == '1'
        pin = int(request.form.get('pin', 0))
        summary = request.form.get('summary', '').strip() if 'summary' in request.form else ''
        # 校验
        if not title or not content:
            flash('标题和内容不能为空', 'danger')
            return render_template('post/create.html')
        # 创建文章
        post = Post(
            title=title,
            content=content,
            summary=summary,
            is_published=is_published,
            is_featured=(pin > 0),
            author_id=current_user.id,
            # category和pin字段如模型有则写入
        )
        if hasattr(post, 'category'):
            post.category = category
        if hasattr(post, 'pin'):
            post.pin = pin
        db.session.add(post)
        db.session.commit()
        if is_published:
            flash('文章已发布！', 'success')
        else:
            flash('草稿已保存！', 'info')
        return redirect(url_for('main.post_detail', post_id=post.id))
    return render_template('post/create.html')

# 文章编辑
@main_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id:
        flash('无权编辑他人文章', 'danger')
        return redirect(url_for('main.post_detail', post_id=post.id))
    if request.method == 'POST':
        post.title = request.form.get('title', '').strip()
        post.content = request.form.get('content', '').strip()
        post.summary = request.form.get('summary', '').strip()
        db.session.commit()
        flash('文章已更新', 'success')
        return redirect(url_for('main.post_detail', post_id=post.id))
    return render_template('post/edit.html', post=post)

# ===================== 奇妙功能 =====================
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
@main_bp.route('/my_posts')
@login_required
def my_posts():
    posts = Post.query.filter_by(author_id=current_user.id).order_by(Post.created_at.desc()).all()
    return render_template('user/my_posts.html', posts=posts)


