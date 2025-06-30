FROM python:3.10-slim as base

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=simple_mcp_launcher.py
ENV MCP_PORT=5050

# 安装基础系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# === 轻量版镜像 (仅Python环境) ===
FROM base as lite

# 复制项目文件
COPY simple_mcp_launcher.py .
COPY mcp_websocket_proxy.py .
COPY mcp.json mcp_config.json
COPY templates/ templates/

# 创建必要目录
RUN mkdir -p uploads logs

# 创建非root用户
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

USER mcpuser

# 暴露端口
EXPOSE 5050

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5050/system_info || exit 1

# 启动命令
CMD ["python", "simple_mcp_launcher.py"]

# === 完整版镜像 (包含Node.js等所有依赖) ===
FROM base as full

# 安装Node.js和其他依赖
RUN apt-get update && apt-get install -y \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 安装Python包管理器
RUN pip install --no-cache-dir uv

# 复制项目文件
COPY simple_mcp_launcher.py .
COPY mcp_websocket_proxy.py .
COPY mcp.json mcp_config.json
COPY templates/ templates/

# 创建必要目录
RUN mkdir -p uploads logs

# 创建非root用户并设置权限
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app && \
    # 确保mcpuser可以使用npm全局安装，并清理缓存
    mkdir -p /home/mcpuser/.npm-global/lib /home/mcpuser/.npm-global/bin && \
    mkdir -p /home/mcpuser/.npm && \
    mkdir -p /home/mcpuser/.cache && \
    mkdir -p /home/mcpuser/.config && \
    chown -R mcpuser:mcpuser /home/mcpuser/.npm-global && \
    chown -R mcpuser:mcpuser /home/mcpuser/.npm && \
    chown -R mcpuser:mcpuser /home/mcpuser/.cache && \
    chown -R mcpuser:mcpuser /home/mcpuser/.config && \
    npm cache clean --force

# 切换到非root用户
USER mcpuser

# 配置npm全局路径
ENV PATH=/home/mcpuser/.npm-global/bin:$PATH
ENV NPM_CONFIG_PREFIX=/home/mcpuser/.npm-global

# 暴露端口
EXPOSE 5050

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5050/system_info || exit 1

# 启动命令
CMD ["python", "simple_mcp_launcher.py"] 