import os
import yaml
from datetime import timedelta

def load_yaml_config():
    # 尝试加载config.yml或config.yaml
    for filename in ['config.yml', 'config.yaml']:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f'Error loading config file: {str(e)}')
                break
    # 返回默认配置
    return {
        'api_key': os.environ.get('DEEPSEEK_API_KEY'),
        'base_url': 'https://api.deepseek.com',
        'model': 'deepseek-chat'
    }

class Config:
    """应用配置类"""
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///blog.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app/static/uploads')
    
    # 分页配置
    POSTS_PER_PAGE = 10
    
    # 从yml读取配置
    MODEL_CONFIG = load_yaml_config()
