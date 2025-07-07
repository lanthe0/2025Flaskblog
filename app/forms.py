from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Optional

class CommentForm(FlaskForm):
    """评论表单"""
    content = TextAreaField('评论内容', validators=[
        DataRequired(message='评论内容不能为空'),
        Length(min=1, max=1000, message='评论内容长度必须在1-1000字符之间')
    ])
    parent_id = HiddenField('父评论ID')  # 用于回复功能
    submit = SubmitField('发表评论')

class CommentEditForm(FlaskForm):
    """评论编辑表单"""
    content = TextAreaField('评论内容', validators=[
        DataRequired(message='评论内容不能为空'),
        Length(min=1, max=1000, message='评论内容长度必须在1-1000字符之间')
    ])
    submit = SubmitField('更新评论')
