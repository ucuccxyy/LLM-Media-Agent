# Media Agent

这是一个基于大型语言模型（LLM）的智能媒体管理助理。它能理解自然语言指令，并通过调用 Radarr, Sonarr, qBittorrent 等服务的 API，帮助您自动化搜索、下载和管理电影与电视剧。

## 核心功能

- **自然语言交互**: 通过聊天界面，用日常语言下达指令。
- **智能搜索**: 搜索电影和电视剧，并能处理搜索结果不明确的情况。
- **自动下载**: 将搜索到的媒体资源添加到 Radarr 或 Sonarr，并自动开始下载。
- **多轮对话**: 能够记住上下文，完成连续的多步任务（例如：先搜索，再根据用户的确认进行下载）。
- **状态查询**: 获取 Sonarr, Radarr 的下载队列以及 qBittorrent 的任务状态。

## 技术架构

- **后端**: Python, Flask
- **核心逻辑**: LangChain Agent
- **语言模型**: Ollama (可接入任意兼容的模型)
- **前端**: Vanilla HTML, CSS, JavaScript
- **媒体服务**: Radarr, Sonarr, qBittorrent (通过 Docker Compose 管理)

---

## 快速部署指南

要在一个新的环境中部署本项目，请遵循以下步骤。

### 1. 克隆项目

首先，将本项目从 GitHub 克隆到你的本地或服务器上：

```bash
git clone https://github.com/ucuccxyy/LLMagent.git
cd LLMagent
```

### 2. 启动基础服务

本项目依赖于 Ollama 和其他媒体服务。项目内已包含一个 `docker-compose.yml` 文件来简化这个过程。

```bash
# 进入 docker 目录并启动所有服务
# -d 参数让服务在后台运行
cd media_agent/docker
docker-compose up -d
```
这个命令会启动：
- Ollama
- Radarr
- Sonarr
- qBittorrent
- Jackett
- Prowlarr

**注意**: 初次启动时，Docker 会下载所有服务的镜像，可能需要一些时间。

### 3. 配置环境变量

Agent 需要知道如何连接到这些服务。

```bash
# 回到项目根目录
cd ../..

# 复制环境变量模板文件
cp media_agent/.env.example .env
```
然后，你需要编辑这个新的 `.env` 文件，填入正确的信息。

- **OLLAMA_HOST**: Ollama 服务的地址，如果在本机运行通常是 `http://localhost:11434`。
- **OLLAMA_MODEL**: 你希望使用的模型名称，例如 `qwen2:7b`。请确保这个模型已经在 Ollama 中通过 `ollama pull qwen2:7b` 拉取。
- **RADARR_URL/SONARR_URL/QBITTORRENT_URL**: 相应服务的地址。
- **RADARR_API_KEY/SONARR_API_KEY**: 你需要登录 Radarr/Sonarr 的网页界面，在 `Settings` -> `General` 中找到并复制 API 密钥。
- **QBITTORRENT_USER/QBITTORRENT_PASSWORD**: qBittorrent 的登录用户名和密码。

### 4. 安装 Python 依赖

我们建议使用 Python 虚拟环境。

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装所有依赖包
pip install -r requirements.txt
```

### 5. 运行 Agent 服务

一切就绪后，你可以启动 Media Agent 的后端 API 服务。

```bash
./start_api.sh
```

现在，你可以通过浏览器访问 `http://<你的服务器IP>:5001` 来使用 Media Agent 了。

## 如何运行

- **启动所有服务**:
  ```bash
  # 启动 Radarr, Sonarr 等
  cd media_agent/docker
  docker-compose up -d

  # 启动 Agent API
  cd ../..
  ./start_api.sh
  ```

- **停止服务**:
  ```bash
  # 停止 Agent API
  ./stop_api.sh

  # 停止 Docker 服务
  cd media_agent/docker
  docker-compose down
  ```

- **查看日志**:
  ```bash
  tail -f media_agent/logs/api.log
  ```

## 环境变量说明

请在项目根目录的 `.env` 文件中配置以下变量：

| 变量 | 说明 | 示例 |
|---|---|---|
| `OLLAMA_HOST` | Ollama 服务的完整 URL | `http://localhost:11434` |
| `OLLAMA_MODEL`| 要使用的 LLM 模型名称 | `qwen2:7b` |
| `RADARR_URL` | Radarr 服务的 URL | `http://localhost:7878` |
| `RADARR_API_KEY`| Radarr 的 API Key | `your_radarr_api_key` |
| `SONARR_URL` | Sonarr 服务的 URL | `http://localhost:8989` |
| `SONARR_API_KEY`| Sonarr 的 API Key | `your_sonarr_api_key` |
| `QBITTORRENT_URL`| qBittorrent 服务的 URL | `http://localhost:8080` |
| `QBITTORRENT_USER`| qBittorrent 的用户名 | `admin` |
| `QBITTORRENT_PASSWORD`| qBittorrent 的密码 | `adminadmin` | 