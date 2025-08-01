# LLM 智能媒体代理

## 1. 项目简介

本项目是一个基于大型语言模型（LLM）的智能代理（Agent）系统，旨在通过自然语言指令实现对电影、电视剧等媒体资源的自动化管理。它集成了 Radarr, Sonarr, qBittorrent, 和 Jackett 等流行的媒体服务，并利用 LLM (通过 Ollama) 作为决策核心，将用户的高级指令转化为具体的操作。

用户可以通过命令行或 API 与本系统交互，轻松完成如“帮我下载最新一季的《XX》电视剧”或“找一下评价最高的科幻电影”等复杂任务。

## 2. 项目结构

```
.
├── frontend/               # 前端应用（推测）
├── media_agent/            # 媒体代理核心模块
│   ├── api/                # Flask API 定义
│   ├── core/               # 核心逻辑 (Agent, LLM管理器)
│   ├── config/             # 配置模块
│   ├── docker/             # Docker Compose & 服务配置
│   ├── data/               # 媒体数据存储 (电影/电视剧)
│   ├── logs/               # 服务和应用日志
│   └── pids/               # 进程PID文件
├── venv/                   # Python 虚拟环境
├── main.py                 # 项目主入口 (CLI / API)
├── requirements.txt        # Python 依赖
├── start_media_services.sh # 一键启动所有服务和API
├── stop_media_services.sh  # 一键停止所有服务和API
└── README.md               # 本文档
```

## 3. 核心原理

本项目的运行机制可以概括为以下几个步骤：

1.  **用户指令**: 用户通过客户端（CLI或Web前端）发出一个自然语言指令。
2.  **API 接收**: `main.py` 运行的 Flask API 服务接收到指令。
3.  **Agent 处理**: API 将请求交给 `MediaAgent` 实例进行处理。
4.  **LLM 决策**: `MediaAgent` 将用户的原始指令和一系列预定义的可用工具（Tools）信息发送给 `OllamaManager` 所管理的本地大语言模型。
5.  **工具选择与调用**: LLM 根据指令的意图，决定调用哪个或哪些工具来完成任务，并生成调用所需的参数。例如，它可能会选择 `search_movie` 工具并附带参数 `movie_name="星际穿越"`。
6.  **工具执行**: `MediaAgent` 执行 LLM 选择的工具。这些工具是封装了与 Radarr, Sonarr 等服务 API 交互的 Python 函数。
7.  **结果反馈与迭代**: 工具的执行结果会返回给 LLM。LLM 根据这个结果决定下一步行动：是已经完成任务并生成最终答复，还是需要调用其他工具进行下一步操作（例如，在找到电影后调用 `add_movie` 工具）。
8.  **最终响应**: 当任务完成后，LLM 生成最终的自然语言答复，`MediaAgent` 将其返回给用户。

这个“指令 -> 思考 -> 工具 -> 反馈”的循环使得 Agent 能够处理复杂的、多步骤的任务。

## 4. 部署与使用

### 4.1. 环境准备

1.  **安装 Docker**: 确保您的系统已安装 Docker 和 Docker Compose。
2.  **创建虚拟环境**:
    ```bash
    python3 -m venv venv
    ```
3.  **激活虚拟环境**:
    ```bash
    source venv/bin/activate
    ```
4.  **安装 Python 依赖**:
    ```bash
    pip install -r requirements.txt
    ```
5.  **配置 Ollama**: 确保本地 Ollama 服务正在运行，并且已经拉取了项目所需的模型（模型名称可在 `load_from_env` 相关配置中找到，默认为环境变量 `OLLAMA_MODEL`）。

### 4.2. 一键启动

项目提供了一个便捷的启动脚本，可以一键启动所有必需的后台服务和本项目的 API。

```bash
bash ./start_media_services.sh
```

该脚本会完成以下工作：
- 启动 Radarr, Sonarr, qBittorrent, Jackett 的 Docker 容器。
- 收集各服务的日志到 `media_agent/logs/` 目录下。
- 在后台启动 `main.py` 的 API 服务（监听 `0.0.0.0:5001`）。
- 输出所有服务的访问地址和 API 服务的运行状态。

### 4.3. 交互方式

#### API 模式 (推荐)
启动后，API 服务运行在 `http://<your-ip>:5001`。您可以构建自己的客户端或使用 Postman 等工具与 `/chat` 端点进行交互。

- **Endpoint**: `POST /chat`
- **Body** (JSON): `{"request": "你的自然语言指令"}`

#### CLI 模式 (用于调试)
您也可以直接在命令行中与 Agent 进行交互，这对于开发和调试非常有用。

```bash
# 确保虚拟环境已激活
python main.py --mode cli
```

### 4.4. 停止服务

使用以下脚本来停止由 `start_media_services.sh` 启动的所有 Docker 容器和后台 API 进程。

```bash
bash ./stop_media_services.sh
```

## 5. 工具说明

Agent 的所有功能均通过调用以下经过验证的工具来实现。这些工具是连接大语言模型（LLM）与底层媒体服务（Radarr, Sonarr, qBittorrent）的桥梁。

---

### 通用工具

-   **`ask_user_for_clarification(question: str) -> str`**
    -   **功能**: 当用户的指令意图不明确时（例如，同时可能指电影和电视剧），LLM会使用此工具来向用户提问，请求更具体的信息。
    -   **触发场景**: 用户输入“搜索‘阿凡达’”。
    -   **模型行为**: 调用此工具，并向用户返回问题：“您是想搜索电影还是电视剧？”

---

### 电影管理 (Radarr)

-   **`search_movie(query: str) -> str`**
    -   **功能**: 根据用户提供的关键词搜索电影。
    -   **实现**: 调用 `radarr_tool.search_movie_logic`，通过 Radarr API 查找电影。
    -   **返回**: 一个包含电影标题、年份和 TMDB ID 的格式化列表。

-   **`download_movie(tmdb_id: int) -> str`**
    -   **功能**: 根据电影的 TMDB ID，将其添加到 Radarr 中并触发搜索下载。
    -   **实现**: 调用 `radarr_tool.download_movie_logic`。该函数会先用 TMDB ID 确认电影信息，然后通过 Radarr API 添加电影。
    -   **返回**: 操作成功或失败的确认信息。

-   **`get_radarr_queue() -> str`**
    -   **功能**: 查询 Radarr 当前的活动队列，了解电影的下载状态。
    -   **实现**: 调用 `radarr_tool.get_radarr_queue_logic`。
    -   **返回**: 一个格式化的列表，包含队列中电影的标题、状态和预计剩余时间。

---

### 电视剧管理 (Sonarr)

-   **`search_series(query: str) -> str`**
    -   **功能**: 根据用户提供的关键词搜索电视剧。
    -   **实现**: 调用 `sonarr_tool.search_series_logic`，通过 Sonarr API 进行查找。
    -   **返回**: 一个包含电视剧标题、年份和 TVDB ID 的格式化列表。

-   **`download_series(tvdb_id: int, seasons: Union[str, list[int]]) -> str`**
    -   **功能**: 根据电视剧的 TVDB ID，将其添加到 Sonarr，并指定下载特定季度或全部季度。
    -   **实现**: 调用 `sonarr_tool.download_series_logic`。`seasons` 参数可以是一个季度编号的列表（如 `[1, 3]`），也可以是字符串 `'all'`。
    -   **返回**: 操作成功或失败的确认信息。

-   **`get_sonarr_queue() -> str`**
    -   **功能**: 查询 Sonarr 当前的活动队列，了解剧集的下载状态。
    -   **实现**: 调用 `sonarr_tool.get_sonarr_queue_logic`。
    -   **返回**: 一个格式化的列表，包含队列中剧集的标题、状态和预计剩余时间。

---

### 下载器管理 (qBittorrent)

-   **`get_torrents() -> str`**
    -   **功能**: 获取 qBittorrent 中当前所有种子任务的列表和状态。
    -   **实现**: 调用 `qbittorrent_tool.get_torrents_logic`。
    -   **返回**: 一个格式化的列表，包含种子的名称、状态和下载进度（最多显示前10个任务）。

## 6. 日志与监控

- **媒体服务日志**: 位于 `media_agent/logs/` 下，如 `radarr.log`, `sonarr.log` 等。
- **API 服务日志**: 位于 `media_agent/logs/api.log`。
- **实时查看日志**:
  ```bash
  # 查看 API 日志
  tail -f media_agent/logs/api.log

  # 查看 Radarr 日志
  tail -f media_agent/logs/radarr.log
  ``` 