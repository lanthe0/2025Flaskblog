from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, logout_user, login_user, login_required
from app.models import User, Post, Comment, Like
from app import db
from app.forms import CommentForm, CommentEditForm
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
        # 检查邮箱是否已存在
        ExistingEmail = User.query.filter_by(email=email).first()
        if ExistingEmail:
            flash('该邮箱已被注册', 'danger')
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
    
    # 增加观看量（排除作者自己访问）
    if not current_user.is_authenticated or current_user.id != post.author_id:
        post.views = (post.views or 0) + 1
        db.session.commit()
    
    html_content = Markup(markdown.markdown(
        post.content,
        extensions=['fenced_code', 'codehilite', 'tables', 'toc']
    ))
    # 只查一级评论
    comments = list(Comment.query.filter_by(post_id=post.id, parent_id=None, is_approved=True, is_deleted=False).order_by(Comment.created_at.asc()).all())
    comment_form = CommentForm()
    return render_template('post/detail.html', post=post, html_content=html_content, comments=comments, Comment=Comment, comment_form=comment_form)

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

@main_bp.route('/my_posts')
@login_required
def my_posts():
    posts = Post.query.filter_by(author_id=current_user.id).order_by(Post.created_at.desc()).all()
    return render_template('user/my_posts.html', posts=posts)

# ===================== 评论相关 =====================
@main_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    # 只用原生input获取parent_id
    parent_id = request.form.get('parent_id')
    if not parent_id or str(parent_id).lower() == 'none':
        parent_id = None
    else:
        try:
            parent_id = int(parent_id)
        except Exception:
            parent_id = None
    content = request.form.get('content', '').strip()
    if not content:
        flash('评论内容不能为空', 'danger')
        return redirect(url_for('main.post_detail', post_id=post_id))
    # 检查 parent_id 是否为有效的评论
    if parent_id:
        parent_comment = Comment.query.get(parent_id)
        if not parent_comment or parent_comment.post_id != post_id:
            flash('回复的评论不存在', 'danger')
            return redirect(url_for('main.post_detail', post_id=post_id))
    comment = Comment(
        content=content,
        author_id=current_user.id,
        post_id=post_id,
        parent_id=parent_id,
        is_reply=bool(parent_id)
    )
    db.session.add(comment)
    db.session.commit()
    flash('评论发表成功！', 'success')
    return redirect(url_for('main.post_detail', post_id=post_id))

@main_bp.route('/comment/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    """编辑评论"""
    comment = Comment.query.get_or_404(comment_id)
    
    if not comment.can_edit(current_user):
        flash('无权编辑此评论', 'danger')
        return redirect(url_for('main.post_detail', post_id=comment.post_id))
    
    form = CommentEditForm()
    
    if request.method == 'GET':
        form.content.data = comment.content
    
    if form.validate_on_submit():
        comment.content = form.content.data.strip()
        db.session.commit()
        flash('评论已更新', 'success')
        return redirect(url_for('main.post_detail', post_id=comment.post_id))
    
    return render_template('comment/edit.html', form=form, comment=comment)

@main_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """删除评论"""
    comment = Comment.query.get_or_404(comment_id)
    
    if not comment.can_delete(current_user):
        flash('无权删除此评论', 'danger')
        return redirect(url_for('main.post_detail', post_id=comment.post_id))
    
    # 软删除
    comment.is_deleted = True
    db.session.commit()
    
    flash('评论已删除', 'success')
    return redirect(url_for('main.post_detail', post_id=comment.post_id))

@main_bp.route('/comment/<int:comment_id>/reply', methods=['GET'])
@login_required
def reply_comment(comment_id):
    """回复评论页面"""
    comment = Comment.query.get_or_404(comment_id)
    form = CommentForm()
    form.parent_id.data = comment.id
    return render_template('comment/reply.html', form=form, comment=comment, post=comment.post)

# ===================== 奇妙功能 =====================
@main_bp.route('/guga')
def guga():
    return render_template('guga/guga.html',
                            background_image_url=url_for('static', filename='guga/MyGO_background.png'),
                            panel_image_url=url_for('static', filename='guga/gugugaga.png')
                            )

from app.guga_chat import handle_chat_request


@main_bp.route('/guli')
def guli():
    text = "灵感菇里菇里菇里瓜恰~\n灵感菇灵感菇~\n"
    return render_template('guga/guli.html', text=text)

@main_bp.route('/hybridaction/<path:subpath>')
def handle_hybridaction(subpath):
    """处理所有/hybridaction开头的请求"""
    return jsonify({'error': 'Not found'}), 404

@main_bp.route('/guga/None')
def handle_guga_none():
    """处理/guga/None请求"""
    return redirect(url_for('main.guga'))

# ===================== 点赞相关 =====================
@main_bp.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def toggle_like(post_id):
    """点赞/取消点赞文章"""
    post = Post.query.get_or_404(post_id)
    
    # 检查是否已经点赞
    existing_like = Like.query.filter_by(
        author_id=current_user.id,
        post_id=post_id
    ).first()
    
    if existing_like:
        # 取消点赞
        db.session.delete(existing_like)
        action = 'unliked'
    else:
        # 添加点赞
        like = Like(author_id=current_user.id, post_id=post_id)
        db.session.add(like)
        action = 'liked'
    
    db.session.commit()
    
    # 返回JSON响应
    return jsonify({
        'success': True,
        'action': action,
        'likes_count': post.get_likes_count(),
        'is_liked': action == 'liked'
    })

@main_bp.route('/post/<int:post_id>/like/status')
@login_required
def get_like_status(post_id):
    """获取当前用户的点赞状态"""
    post = Post.query.get_or_404(post_id)
    is_liked = Like.query.filter_by(
        author_id=current_user.id,
        post_id=post_id
    ).first() is not None
    
    return jsonify({
        'is_liked': is_liked,
        'likes_count': post.get_likes_count()
    })




