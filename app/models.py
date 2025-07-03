from app import db
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    

    # 1. id：用户ID
    # 2. username：用户名
    # 3. email：邮箱
    # 4. password_hash：密码哈希
    # 5. first_name：名
    # 6. last_name：姓
    # 7. bio：个人简介
    # 8. avatar_url：头像URL
    # 9. is_active：是否激活
    # 10. is_admin：是否管理员
    # 11. created_at：创建时间
    # 12. updated_at：更新时间
    # 13. last_login：最后登录时间
    
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)
    
    # 关联关系
    # 用户 —— 文章 一对多
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    
    # 用户 —— 评论 一对多
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')

    # 用户 —— 点赞 一对多
    likes = db.relationship('Like', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, username, email, password, first_name=None, last_name=None):
        self.username = username
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
    
    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """获取用户全名"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.now(timezone.utc)
        db.session.commit()
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class Conversation(db.Model):
    """会话模型"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_archived = db.Column(db.Boolean, default=False)
    
    # 关联关系
    user = db.relationship('User', backref=db.backref('conversations', lazy='dynamic'))
    messages = db.relationship('Message', 
                             backref='conversation', 
                             lazy='dynamic', 
                             cascade='all, delete-orphan',
                             order_by='Message.created_at.asc()')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'participant_count': len(self.participants.all())
        }
    
    def __repr__(self):
        return f'<Conversation {self.title}>'

class Message(db.Model):
    """消息模型"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # user/assistant
    is_user = db.Column(db.Boolean, default=False)    # 是否为用户消息
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # 关联关系
    user = db.relationship('User', backref=db.backref('messages', lazy='dynamic'))
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'content': self.content,
            'role': self.role,
            'model': self.model,
            'parent_id': self.parent_id,
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Message {self.id}>'

class UserConversation(db.Model):
    """用户会话关联模型"""
    __tablename__ = 'user_conversations'
    
    # 1. user_id: 用户ID
    # 2. conversation_id: 会话ID
    # 3. is_archived: 是否归档
    # 4. last_read: 最后阅读时间
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), primary_key=True)
    is_archived = db.Column(db.Boolean, default=False)
    last_read = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'is_archived': self.is_archived,
            'last_read': self.last_read.isoformat() if self.last_read else None
        }
    
    def __repr__(self):
        return f'<UserConversation user:{self.user_id} conversation:{self.conversation_id}>'

class Post(db.Model):
    """文章模型"""
    __tablename__ = 'posts'
    
    # id：主键，自增ID
    # title：文章标题，字符串类型，必填
    # content：文章内容，长文本，必填
    # summary：文章摘要，字符串类型，可选
    # created_at：创建时间，默认为当前时间
    # updated_at：更新时间，每次更新自动修改
    # views：浏览量，默认为0
    # author_id：作者ID，外键，关联users表，必填
    # is_published：是否已发布，布尔值，默认为True
    # is_featured：是否为精选，布尔值，默认为False
    # is_deleted：是否已删除，布尔值，默认为False
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    views = db.Column(db.Integer, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_published = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Post {self.title}>'

class Comment(db.Model):
    """评论模型"""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    # 通过backref，User和Post模型可直接访问comments

    def __repr__(self):
        return f'<Comment {self.id}>'

class Like(db.Model):
    """点赞模型"""
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    # 通过backref，User和Post模型可直接访问likes

    def __repr__(self):
        return f'<Like {self.id}>'