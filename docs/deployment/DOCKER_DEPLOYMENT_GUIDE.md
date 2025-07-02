# 🐳 XTool MCP Server Docker 部署指南

## 概述

XTool MCP Server 是一个基于模型上下文协议（MCP）的AI工具服务器，支持20+种专业AI工具，包括代码分析、调试、重构、安全审计等功能。本指南将帮助您在不同环境中部署和使用该服务。

## 镜像信息

- **镜像名称**: `xtoolteam/xtool-mcp-server`
- **支持的标签**: `latest`, `v1.0.0`
- **镜像大小**: ~473MB（基于 Python 3.11-slim）
- **支持架构**: amd64, arm64

## 快速开始

### 1. 拉取镜像

```bash
docker pull xtoolteam/xtool-mcp-server:latest
```

### 2. 基本运行

```bash
# 最基本的运行方式
docker run -d \
  --name xtool-mcp-server \
  -e GEMINI_API_KEY=your_gemini_api_key \
  xtoolteam/xtool-mcp-server:latest

# 查看日志
docker logs xtool-mcp-server
```

### 3. 推荐的生产配置

```bash
docker run -d \
  --name xtool-mcp-server \
  --restart unless-stopped \
  -e GEMINI_API_KEY=your_gemini_api_key \
  -e OPENAI_API_KEY=your_openai_api_key \
  -e OPENROUTER_API_KEY=your_openrouter_api_key \
  -e LOG_LEVEL=INFO \
  -v ./logs:/app/logs \
  -v ./memory:/app/.xtool_memory \
  -v ./config:/app/conf \
  --security-opt no-new-privileges:true \
  --read-only \
  --tmpfs /tmp:noexec,nosuid,size=100m \
  --tmpfs /app/tmp:noexec,nosuid,size=50m \
  xtoolteam/xtool-mcp-server:latest
```

## 环境变量配置

### 必需的 API 密钥（至少配置一个）

| 变量名 | 描述 | 示例 |
|--------|------|------|
| `GEMINI_API_KEY` | Google Gemini API 密钥 | `AIza...` |
| `OPENAI_API_KEY` | OpenAI API 密钥 | `sk-...` |
| `OPENROUTER_API_KEY` | OpenRouter API 密钥 | `sk-or-...` |
| `ANTHROPIC_API_KEY` | Anthropic Claude API 密钥 | `sk-ant-...` |
| `XAI_API_KEY` | xAI API 密钥 | `xai-...` |

### 可选配置

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `DEFAULT_MODEL` | `auto` | 默认使用的AI模型 |
| `LOG_LEVEL` | `INFO` | 日志级别 (DEBUG/INFO/WARNING/ERROR) |
| `LOG_MAX_SIZE` | `20MB` | 单个日志文件最大大小 |
| `LOG_BACKUP_COUNT` | `10` | 日志文件备份数量 |
| `DEFAULT_THINKING_MODE_THINKDEEP` | `medium` | 深度思考模式级别 |
| `DISABLED_TOOLS` | - | 禁用的工具列表（逗号分隔） |
| `MAX_MCP_OUTPUT_TOKENS` | `100000` | MCP输出最大令牌数 |

### 自定义模型配置

| 变量名 | 描述 |
|--------|------|
| `CUSTOM_API_URL` | 自定义模型API地址 |
| `CUSTOM_API_KEY` | 自定义模型API密钥 |
| `CUSTOM_MODEL_NAME` | 自定义模型名称 |

## 数据持久化

### 重要的挂载点

- `/app/logs` - 日志文件存储
- `/app/.xtool_memory` - 会话记忆和工作流状态
- `/app/conf` - 配置文件存储

### 推荐的卷配置

```bash
# 创建数据目录
mkdir -p ./xtool-data/{logs,memory,config}

# 使用数据卷
docker run -d \
  --name xtool-mcp-server \
  -v ./xtool-data/logs:/app/logs \
  -v ./xtool-data/memory:/app/.xtool_memory \
  -v ./xtool-data/config:/app/conf \
  xtoolteam/xtool-mcp-server:latest
```

## Docker Compose 部署

### 开发环境

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  xtool-mcp:
    image: xtoolteam/xtool-mcp-server:latest
    container_name: xtool_mcp_dev
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=DEBUG
      - DEFAULT_THINKING_MODE_THINKDEEP=high
    volumes:
      - ./logs:/app/logs
      - ./memory:/app/.xtool_memory
      - ./config:/app/conf
    ports:
      - "8000:8000"  # 开发环境暴露端口便于调试
    restart: unless-stopped
```

### 生产环境

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  xtool-mcp:
    image: xtoolteam/xtool-mcp-server:latest
    container_name: xtool_mcp_prod
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - LOG_LEVEL=INFO
      - PRODUCTION=true
      - DEBUG=false
    volumes:
      - xtool-logs:/app/logs
      - xtool-memory:/app/.xtool_memory
      - xtool-config:/app/conf
      - /etc/localtime:/etc/localtime:ro
    deploy:
      resources:
        limits:
          memory: 2GB
          cpus: '2.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "python", "/usr/local/bin/healthcheck.py"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
      - /app/tmp:noexec,nosuid,size=50m

volumes:
  xtool-logs:
  xtool-memory:
  xtool-config:
```

### 启动服务

```bash
# 开发环境
docker-compose -f docker-compose.dev.yml up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

## 健康检查

容器包含内置的健康检查脚本：

```bash
# 检查容器健康状态
docker inspect --format='{{.State.Health.Status}}' xtool-mcp-server

# 查看健康检查日志
docker inspect xtool-mcp-server | grep -A 20 '"Health"'
```

## 在其他项目中集成

### 方法1: 作为服务依赖

在您的项目的 `docker-compose.yml` 中添加：

```yaml
version: '3.8'

services:
  xtool-mcp:
    image: xtoolteam/xtool-mcp-server:latest
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - xtool-memory:/app/.xtool_memory
      - xtool-logs:/app/logs
    restart: unless-stopped

  your-app:
    build: .
    depends_on:
      - xtool-mcp
    # 您的应用配置

volumes:
  xtool-memory:
  xtool-logs:
```

### 方法2: 独立运行

```bash
# 在项目目录下创建 xtool 服务
cd your-project
mkdir xtool-service
cd xtool-service

# 创建配置文件
cat > docker-compose.yml << EOF
version: '3.8'

services:
  xtool-mcp:
    image: xtoolteam/xtool-mcp-server:latest
    container_name: \${PROJECT_NAME:-myproject}_xtool_mcp
    environment:
      - GEMINI_API_KEY=\${GEMINI_API_KEY}
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
      - LOG_LEVEL=\${LOG_LEVEL:-INFO}
    volumes:
      - ./data/memory:/app/.xtool_memory
      - ./data/logs:/app/logs
      - ./data/config:/app/conf
    restart: unless-stopped
    networks:
      - xtool-network

networks:
  xtool-network:
    external: true
    name: \${PROJECT_NAME:-myproject}_network
EOF

# 启动服务
docker-compose up -d
```

## 网络配置

### 内部网络通信

```yaml
# 创建共享网络
docker network create myproject_network

# 在多个服务中使用
services:
  xtool-mcp:
    image: xtoolteam/xtool-mcp-server:latest
    networks:
      - myproject_network
  
  other-service:
    image: your-app:latest
    networks:
      - myproject_network
    # 可以通过 xtool-mcp:8000 访问服务

networks:
  myproject_network:
    external: true
```

## 日志管理

### 日志查看

```bash
# 实时查看服务日志
docker logs -f xtool-mcp-server

# 查看最近100行日志
docker logs --tail 100 xtool-mcp-server

# 查看特定时间的日志
docker logs --since "2024-01-01T00:00:00" xtool-mcp-server
```

### 日志轮转配置

在 `docker-compose.yml` 中配置：

```yaml
services:
  xtool-mcp:
    image: xtoolteam/xtool-mcp-server:latest
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
        compress: "true"
```

## 性能优化

### 资源限制

```yaml
services:
  xtool-mcp:
    image: xtoolteam/xtool-mcp-server:latest
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 缓存优化

```bash
# 预拉取镜像以加快启动
docker pull xtoolteam/xtool-mcp-server:latest

# 创建持久化卷以复用数据
docker volume create xtool_memory_data
docker volume create xtool_config_data
```

## 安全最佳实践

### 1. 环境变量管理

```bash
# 使用 .env 文件管理敏感信息
cat > .env << EOF
GEMINI_API_KEY=your_secure_key_here
OPENAI_API_KEY=your_secure_key_here
# 不要提交到版本控制
EOF

# 在 .gitignore 中添加
echo ".env" >> .gitignore
```

### 2. 容器安全加固

```yaml
services:
  xtool-mcp:
    image: xtoolteam/xtool-mcp-server:latest
    user: "1000:1000"  # 非root用户
    security_opt:
      - no-new-privileges:true
    read_only: true
    cap_drop:
      - ALL
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
```

### 3. 网络隔离

```yaml
services:
  xtool-mcp:
    image: xtoolteam/xtool-mcp-server:latest
    networks:
      - internal
    # 不暴露端口到主机

networks:
  internal:
    internal: true  # 仅内部通信
```

## 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 检查日志
   docker logs xtool-mcp-server
   
   # 检查配置
   docker exec xtool-mcp-server env | grep API_KEY
   ```

2. **内存不足**
   ```bash
   # 增加内存限制
   docker update --memory 2g xtool-mcp-server
   ```

3. **API密钥错误**
   ```bash
   # 检查环境变量
   docker exec xtool-mcp-server python -c "import os; print(bool(os.getenv('GEMINI_API_KEY')))"
   ```

### 诊断命令

```bash
# 容器信息
docker inspect xtool-mcp-server

# 进入容器调试
docker exec -it xtool-mcp-server /bin/bash

# 检查端口
docker port xtool-mcp-server

# 检查卷挂载
docker inspect xtool-mcp-server | grep -A 10 '"Mounts"'
```

## 更新和维护

### 更新镜像

```bash
# 拉取最新版本
docker pull xtoolteam/xtool-mcp-server:latest

# 停止当前容器
docker stop xtool-mcp-server

# 删除旧容器（保留数据卷）
docker rm xtool-mcp-server

# 启动新容器
docker run -d \
  --name xtool-mcp-server \
  -v xtool-memory:/app/.xtool_memory \
  -v xtool-logs:/app/logs \
  xtoolteam/xtool-mcp-server:latest
```

### 数据备份

```bash
# 备份记忆数据
docker run --rm \
  -v xtool-memory:/source \
  -v $(pwd):/backup \
  alpine \
  tar czf /backup/xtool-memory-backup.tar.gz -C /source .

# 恢复数据
docker run --rm \
  -v xtool-memory:/target \
  -v $(pwd):/backup \
  alpine \
  tar xzf /backup/xtool-memory-backup.tar.gz -C /target
```

## 支持和帮助

- **GitHub仓库**: [xtool-mcp-server](https://github.com/xtoolteam/xtool-mcp-server)
- **问题报告**: 提交 GitHub Issues
- **文档**: 查看项目README和文档目录

## 版本信息

- **当前版本**: v1.0.0
- **支持的MCP协议版本**: 2024-11-05
- **Python版本**: 3.11+
- **更新频率**: 定期更新，建议关注仓库通知