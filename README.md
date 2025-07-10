# 2025Flaskblog - 博客系统

## 项目简介
这是一个基于Flask的全功能博客系统，包含用户认证、文章发布、评论等功能，是2025小学期作业项目。

## 功能特点
- 用户注册、登录、个人资料管理
- 文章发布、编辑、删除
- 评论和回复功能
- 实时聊天功能
- 和高松灯的虚拟对话

## 安装指南

### 前置条件
- Python 3.8+
- PostgreSQL数据库(或其他兼容SQLAlchemy的数据库)

### 安装步骤
1. 克隆仓库:
   ```bash
   git clone https://github.com/lanthe0/2025Flaskblog.git
   ```

2. 创建并激活虚拟环境(若安装了conda):
   ```bash
   conda create -n flaskblog python=3.8
   conda activate flaskblog
   ```

3. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

4. 初始化数据库:
   ```bash
   flask db upgrade
   ```

5. 配置config.yml:
   在api_key那一栏填入你的Deepseek API Key。

## 运行项目
```bash
# 开发环境
python app.py
# 生产环境
python run_ipv6.py
```
访问 http://localhost:5000
或终端给出的地址


## 项目结构
```
├── app/                  # 应用核心代码
│   ├── static/           # 静态文件(CSS, JS, 图片)
│   ├── templates/        # 模板文件
│   ├── __init__.py       # 应用工厂
│   ├── models.py         # 数据库模型
│   ├── routes.py         # 路由定义
├── migrations/           # 数据库迁移文件
├── tests/                # 测试代码
├── config.py             # 配置类
├── requirements.txt      # 依赖列表
└── README.md             # 项目文档
```

## 贡献指南
欢迎提交Pull Request。请确保:
1. 代码符合PEP8规范
2. 添加适当的测试
3. 更新相关文档

## 许可证
MIT License
