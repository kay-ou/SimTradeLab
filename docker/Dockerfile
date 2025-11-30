# SimTradeLab Docker Image
FROM python:3.10-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 安装系统依赖（包含编译依赖）
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Poetry
RUN pip install poetry

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 配置Poetry并安装依赖
RUN poetry config virtualenvs.create false \
    && poetry install --with data --without dev --no-root

# 复制应用代码
COPY . .

# 安装当前项目
RUN poetry install --only-root

# 创建数据目录
RUN mkdir -p data strategies reports cache web/uploads logs

# 设置脚本权限
RUN chmod +x start_web.py

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 启动应用
CMD ["python", "start_web.py", "--host", "0.0.0.0", "--no-browser"]
