# 桥梁病害检测与分割系统后端

## 项目介绍

桥梁病害检测与分割系统是一个基于 Flask 框架开发的后端服务，用于对桥梁结构进行病害检测、分割和评估。系统利用计算机视觉和深度学习技术，能够自动识别和分析桥梁表面的各类病害，如裂缝、锈蚀等，并提供详细的评估报告。

## 主要功能

- **用户管理**：支持用户注册、登录、登出和权限管理，使用 JWT 进行身份验证
- **模型管理**：支持上传、查询和管理多种病害检测模型
- **媒体处理**：支持上传和管理图片、视频等媒体文件
- **病害检测**：使用深度学习模型对桥梁图像/视频进行病害检测和分割
- **病害评估**：基于多种指标（如病害数量、面积、形状复杂度等）对病害进行综合评估
- **操作日志**：记录系统中的各类操作，便于追踪和审计
- **API限流**：防止 API 滥用，保障系统稳定性

## 技术栈

- **Web框架**：Flask
- **数据库**：MySQL + SQLAlchemy ORM
- **认证**：Flask-JWT-Extended
- **跨域支持**：Flask-CORS
- **图像处理**：OpenCV, Pillow
- **视频处理**：MoviePy
- **深度学习**：Ultralytics YOLO11-seg

## 安装指南

### 环境要求

- Python 3.8+
- MySQL 5.7+

### 安装步骤

1. 克隆项目到本地

```bash
git clone https://github.com/YHJYgain/BridgeDiseaseBackend.git
cd BridgeDiseaseBackend
```

2. 安装依赖包

```bash
pip install -r requirements.txt
```

3. 配置数据库

编辑`app/config.py`文件，修改数据库连接信息：

```python
SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/bridge_disease'  # SQLAlchemy 数据库 URI
```

4. 初始化数据库

```bash
mysql -u username -p < sql/init_db.sql
```

5. 启动服务

```bash
python run.py
```

6. 如有需要，也可以编辑`app/config.py`文件，修改`SECRET_KEY`：

```python
SECRET_KEY = 'WZY'  # Flask 密钥，用于签名 cookies 和其他需要加密的操作
```

## 项目结构

```
.
├── app/                   # 应用主目录
│   ├── __init__.py        # 应用初始化
│   ├── config.py          # 配置文件
│   ├── constants.py       # 常量定义
│   ├── decorators/        # 装饰器
│   ├── models/            # 数据模型
│   ├── routes/            # 路由和控制器
│   ├── static/            # 静态文件
│   │   ├── avatars/       # 用户头像
│   │   ├── medias/        # 媒体文件
│   │   ├── models/        # 模型文件
│   │   └── results/       # 检测结果
│   ├── templates/         # 模板文件
│   └── utils/             # 工具函数
├── docs/                  # 文档
├── logs/                  # 日志文件
├── sql/                   # SQL 脚本
├── tests/                 # 测试代码
├── requirements.txt       # 依赖包列表
└── run.py                 # 应用入口
```

## 病害评估指标

系统使用以下指标对桥梁病害进行综合评估：

- **病害数量**：检测到的病害实例数量
- **病害周长**：病害轮廓的总周长
- **病害面积**：病害区域的总面积
- **形状复杂度**：病害形状的复杂程度
- **纹理粗糙度**：病害表面纹理的粗糙程度
- **裂缝宽度**：裂缝的平均宽度（适用于裂缝类病害）
- **平均色调**：病害区域的平均色调（适用于锈蚀类病害）

基于上述指标，系统会计算出病害严重性得分，并给出相应的病害等级（轻微、中等、严重、危急）和评估描述。

## 安全性考虑

- 使用 JWT 进行身份验证和授权
- 密码使用哈希存储
- API 限流防止滥用
- 文件上传类型和大小限制

## 联系方式

如有问题或建议，请联系项目维护者。