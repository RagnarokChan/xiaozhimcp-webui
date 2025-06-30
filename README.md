# 🤖 小智AI聊天机器人 - MCP WEBUI v1

简洁高效的MCP (Model Context Protocol) 服务管理器，支持Docker一键部署。

## ✨ 特性

- 🌐 **Web管理界面** - 直观的MCP服务控制面板
- 🐳 **Docker部署** - 一键启动，开箱即用
- 🔧 **依赖自动安装** - 智能检测和安装MCP服务依赖
- 📝 **配置管理** - 支持JSON配置文件导入导出
- 🔄 **服务控制** - 启动、停止、重启MCP服务
- 📊 **状态监控** - 实时查看服务运行状态和日志

## 🚀 快速开始

### 前置要求
- Docker
- Docker Compose

### 镜像选择

项目提供两个镜像版本：

#### 🪶 轻量版 (375MB) - 推荐
仅包含Python环境，适合：
- 只使用Python MCP服务
- 手动管理依赖
- 生产环境部署

```bash
# 使用轻量版（默认）
docker compose up -d
```

#### 🔧 完整版 (715MB)
包含所有依赖工具，适合：
- 使用多种MCP服务
- 需要自动安装功能
- 开发测试环境

```bash
# 使用完整版
IMAGE_TYPE=full docker compose up -d
```

### 一键部署
```bash
# 克隆项目
git clone <repository-url>
cd zhimcp-control

# 启动服务（轻量版）
docker compose up -d

# 检查状态
docker ps
```

### 访问应用
- **Web界面**: http://localhost:5050
- **API接口**: http://localhost:5050/system_info

## 📦 MCP运行环境配置

### 🪶 轻量版镜像 - 补齐依赖

轻量版只包含Python环境，如需运行Node.js MCP服务，需要手动安装依赖：

#### 安装Node.js环境
```bash
# 进入容器
docker exec -it mcp-launcher bash

# 安装Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证安装
node --version
npm --version
```

#### 安装uvx工具
```bash
# 在容器内安装uvx
docker exec mcp-launcher pip install uv
docker exec mcp-launcher pip install uvx

# 验证安装
docker exec mcp-launcher uvx --version
```

### 🔧 完整版镜像 - 开箱即用

完整版已包含所有运行环境，可直接使用：
- ✅ Python 3.10 + pip
- ✅ Node.js 20 + npm + npx  
- ✅ uvx工具
- ✅ 所有MCP运行依赖

### 🐍 Python MCP服务配置

```json
{
  "mcpServers": {
    "python-service": {
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "env": {}
    }
  }
}
```

### 📦 Node.js MCP服务配置

```json
{
  "mcpServers": {
    "nodejs-service": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"],
      "env": {}
    }
  }
}
```

### 🔧 常用MCP服务安装

#### 官方服务
```bash
# 文件操作
docker exec mcp-launcher npx -y @modelcontextprotocol/server-filesystem

# 数据库操作
docker exec mcp-launcher npx -y @modelcontextprotocol/server-sqlite

# Git操作
docker exec mcp-launcher npx -y @modelcontextprotocol/server-git

# 浏览器自动化
docker exec mcp-launcher npx -y @modelcontextprotocol/server-puppeteer
```

#### Python工具
```bash
# 文档转换
docker exec mcp-launcher uvx mcp-pandoc

# 网络请求
docker exec mcp-launcher uvx mcp-server-fetch

# 时间日期
docker exec mcp-launcher pip install mcp-server-time
```

### 🌍 热门第三方MCP

#### Google服务
```bash
# Google搜索 (需要API密钥)
docker exec mcp-launcher npx -y @modelcontextprotocol/server-google-maps

# YouTube
docker exec mcp-launcher npx -y @kimtaeyoon83/mcp-server-youtube-transcript
```

#### 开发工具
```bash
# GitHub
docker exec mcp-launcher npx -y @modelcontextprotocol/server-github

# Docker管理
docker exec mcp-launcher npx -y mcp-server-docker

# Shell命令
docker exec mcp-launcher npx -y @modelcontextprotocol/server-shell
```

#### 数据处理
```bash
# PostgreSQL
docker exec mcp-launcher npx -y @modelcontextprotocol/server-postgres

# 表格处理
docker exec mcp-launcher npx -y mcp-server-spreadsheet
```

## 📋 使用说明

### 1. 添加MCP服务
通过Web界面上传配置文件或手动编辑 `mcp_config.json`:

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    },
    "google-maps": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-google-maps"],
      "env": {
        "GOOGLE_MAPS_API_KEY": "your_api_key"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {
        "MCP_FILESYSTEM_ALLOWED_DIRS": "/tmp,/home/user/documents"
      }
    }
  }
}
```

### 2. 管理服务
- 启动/停止单个服务
- 批量管理所有服务  
- 查看服务日志
- 监控运行状态

### 3. 系统信息
查看依赖安装状态和系统信息

## 🛠️ 管理命令

```bash
# 查看运行状态
docker ps

# 查看日志
docker logs mcp-launcher

# 进入容器调试
docker exec -it mcp-launcher bash

# 停止服务
docker compose down

# 重新构建
docker compose up -d --build

# 查看依赖状态
curl http://localhost:5050/system_info | jq .dependencies
```

## 📁 项目结构

```
zhimcp-control/
├── docker-compose.yml    # Docker Compose配置
├── Dockerfile           # Docker镜像构建
├── mcp_config.json      # MCP服务配置（默认为空）
├── simple_mcp_launcher.py # 主程序
├── requirements.txt     # Python依赖
├── templates/           # Web模板
├── uploads/            # 配置文件上传目录
└── logs/               # 日志目录
```

## 🔧 配置文件

默认启动时无任何MCP服务配置，需要手动添加。支持的配置格式：

- **命令类型**: `npx`, `uvx`, `python`, `python3`
- **参数**: 数组格式的命令参数
- **环境变量**: 键值对格式的环境变量
- **选项**: `disabled`, `autoApprove` 等控制选项

### 环境变量配置示例
```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["-m", "mcp_weather_server.server"],
      "env": {
        "WEATHER_API_KEY": "your_api_key",
        "DEFAULT_LOCATION": "Beijing"
      }
    }
  }
}
```

## 🐳 Docker信息

### 轻量版镜像
- **基础镜像**: python:3.10-slim
- **镜像大小**: ~375MB
- **包含工具**: Python, pip, curl, git
- **适用场景**: Python MCP服务，生产环境

### 完整版镜像  
- **基础镜像**: python:3.10-slim + Node.js 20
- **镜像大小**: ~715MB
- **包含工具**: Python, pip, Node.js, npm, npx, uvx, curl, git
- **适用场景**: 混合MCP服务，开发环境

### 通用特性
- **运行用户**: mcpuser (非root用户)
- **健康检查**: 30秒间隔自动检测
- **数据持久化**: uploads、logs、配置文件

## 📞 API接口

- `GET /` - Web管理界面
- `GET /get_config` - 获取当前配置
- `GET /system_info` - 系统信息
- `POST /start/<server_name>` - 启动服务
- `POST /stop/<server_name>` - 停止服务
- `POST /upload_config` - 上传配置文件

## 🔒 安全说明

- 容器以非root用户运行
- 配置文件权限控制
- 网络端口仅暴露必要的5050端口
- 建议生产环境配置反向代理
- npm包安装在用户目录，不影响系统

## 📖 常见问题

### Q: 如何选择镜像版本？
**A**: 
- **轻量版**: 只需Python MCP服务，愿意手动配置Node.js环境
- **完整版**: 需要Node.js MCP服务，或希望开箱即用

### Q: 轻量版如何运行Node.js MCP服务？
**A**: 需要先安装Node.js环境和uvx工具，参考"轻量版镜像 - 补齐依赖"章节的详细步骤。

### Q: 配置文件在哪里？
**A**: 主机的 `mcp_config.json` 文件会自动映射到容器内，修改后重启服务即可生效。

### Q: 如何调试MCP服务？
**A**: 通过Web界面查看日志，或使用 `docker logs mcp-launcher` 查看系统日志。

---

💡 **提示**: 项目已优化为最小化部署，支持灵活的镜像选择，确保快速启动和稳定运行。 