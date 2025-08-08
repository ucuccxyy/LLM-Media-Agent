# LLM 智能媒体代理

## 1. 项目简介

本项目是一个基于大型语言模型（LLM）的智能代理（Agent）系统，旨在通过自然语言指令实现对电影、电视剧等媒体资源的自动化管理。它集成了 Radarr, Sonarr, qBittorrent, 和 Jackett 媒体服务，并利用 LLM (支持多种提供商) 作为决策核心，将用户的高级指令转化为具体的操作。

用户可以通过命令行或 API 与本系统交互，轻松完成如"帮我下载最新一季的《XX》电视剧"或"帮我搜索某一部影片"等复杂任务。

## 2. 项目结构

```
.
├── frontend/                    # 前端应用
│   └── index.html              # 前端界面文件
├── media_agent/                 # 媒体代理核心模块
│   ├── api/                    # Flask API 定义
│   │   ├── app.py             # Flask应用创建
│   │   ├── routes.py          # API路由定义
│   │   └── sessions.py        # 会话管理
│   ├── core/                   # 核心逻辑
│   │   ├── agent.py           # 媒体代理主类
│   │   └── llm_manager.py     # LLM管理器 (支持多提供商)
│   ├── config/                 # 配置模块
│   │   └── settings.py        # 全局配置管理
│   ├── docker/                 # Docker服务配置
│   │   ├── docker-compose.yml # 服务编排文件
│   │   ├── radarr/            # Radarr配置目录
│   │   ├── sonarr/            # Sonarr配置目录
│   │   ├── qbittorrent/       # qBittorrent配置目录
│   │   └── jackett/           # Jackett配置目录
│   ├── data/                   # 媒体数据存储
│   │   ├── downloads/         # 下载目录
│   │   ├── movies/            # 电影存储目录
│   │   └── tv_shows/          # 电视剧存储目录
│   ├── logs/                   # 服务和应用日志
│   ├── pids/                   # 进程PID文件
│   ├── services/               # 服务层
│   │   ├── radarr_service.py  # Radarr API服务
│   │   ├── sonarr_service.py  # Sonarr API服务
│   │   └── qbittorrent_service.py # qBittorrent API服务
│   ├── tools/                  # 工具层
│   │   ├── radarr_tool.py     # Radarr工具函数
│   │   ├── sonarr_tool.py     # Sonarr工具函数
│   │   └── qbittorrent_tool.py # qBittorrent工具函数
├── venv/                       # Python 虚拟环境
├── main.py                     # 项目主入口 (CLI / API)
├── requirements.txt            # Python 依赖
├── start_media_services.sh     # 启动所有服务和API
├── stop_media_services.sh      # 停止所有服务和API
├── .gitignore                  # Git忽略文件
└── README.md                   # 本文档
```

## 3. LLM提供商配置

本项目支持多种LLM提供商，包括本地模型和云端API服务。

### 3.1 支持的提供商

1. **Ollama** (本地模型) - 默认
2. **OpenAI** (GPT系列)
3. **Anthropic** (Claude系列)
4. **Google** (Gemini系列)

### 3.2 配置方法

#### 环境变量配置

创建 `.env` 文件并设置以下变量：

```bash
# 选择LLM提供商
LLM_PROVIDER=ollama  # 可选: ollama, openai, anthropic, google

# ===== Ollama配置 (当LLM_PROVIDER=ollama时使用) =====
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=command-r-plus:latest

# ===== OpenAI配置 (当LLM_PROVIDER=openai时使用) =====
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
# 可选：使用自定义OpenAI兼容API
# OPENAI_BASE_URL=https://api.openai.com/v1

# ===== Anthropic配置 (当LLM_PROVIDER=anthropic时使用) =====
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# ===== Google配置 (当LLM_PROVIDER=google时使用) =====
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_MODEL=gemini-1.5-flash
```

#### 安装依赖

根据你选择的提供商，安装相应的依赖：

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装所有依赖（推荐）
pip install -r requirements.txt

# 或者只安装你需要的提供商
pip install langchain-openai      # OpenAI
pip install langchain-anthropic   # Anthropic
pip install langchain-google-genai # Google
```

### 3.3 配置示例

#### 使用OpenAI GPT-4
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

#### 使用Anthropic Claude
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

#### 使用Google Gemini
```bash
LLM_PROVIDER=google
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_MODEL=gemini-1.5-flash
```

#### 使用本地Ollama
```bash
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=command-r-plus:latest
```

### 3.4 获取API密钥

#### OpenAI
1. 访问 https://platform.openai.com/
2. 注册并登录
3. 在API Keys页面创建新的API密钥

#### Anthropic
1. 访问 https://console.anthropic.com/
2. 注册并登录
3. 在API Keys页面创建新的API密钥

#### Google
1. 访问 https://makersuite.google.com/app/apikey
2. 使用Google账号登录
3. 创建新的API密钥

### 3.5 故障排除

#### 模块未找到错误
如果遇到 `ModuleNotFoundError`，请安装相应的依赖：

```bash
pip install langchain-openai langchain-anthropic langchain-google-genai
```

## 4. 核心原理

本项目的运行机制可以概括为以下几个步骤：

1.  **用户指令**: 用户通过客户端（CLI或Web前端）发出一个自然语言指令。
2.  **API 接收**: `main.py` 运行的 Flask API 服务接收到指令。
3.  **Agent 处理**: API 将请求交给 `MediaAgent` 实例进行处理。
4.  **LLM 决策**: `MediaAgent` 将用户的原始指令和一系列预定义的可用工具（Tools）信息发送给 LLM 管理器所管理的语言模型。
5.  **工具选择与调用**: LLM 根据指令的意图，决定调用哪个或哪些工具来完成任务，并生成调用所需的参数。例如，它可能会选择 `search_movie` 工具并附带参数 `movie_name="星际穿越"`。
6.  **工具执行**: `MediaAgent` 执行 LLM 选择的工具。这些工具是封装了与 Radarr, Sonarr 等服务 API 交互的 Python 函数。
7.  **结果反馈与迭代**: 工具的执行结果会返回给 LLM。LLM 根据这个结果决定下一步行动：是已经完成任务并生成最终答复，还是需要调用其他工具进行下一步操作（例如，在找到电影后调用 `add_movie` 工具）。
8.  **最终响应**: 当任务完成后，LLM 生成最终的自然语言答复，`MediaAgent` 将其返回给用户。

这个"指令 -> 思考 -> 工具 -> 反馈"的循环使得 Agent 能够处理复杂的、多步骤的任务。

## 5. 部署与使用

### 5.1. 环境准备

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
5.  **配置 LLM**: 根据你的需求配置相应的LLM提供商（详见第3节）。

### 5.2. 一键启动

项目提供了一个便捷的启动脚本，可以一键启动所有必需的后台服务和本项目的 API。

```bash
bash ./start_media_services.sh
```

该脚本会完成以下工作：
- 启动 Radarr, Sonarr, qBittorrent, Jackett 的 Docker 容器。
- 收集各服务的日志到 `media_agent/logs/` 目录下。
- 在后台启动 `main.py` 的 API 服务（监听 `0.0.0.0:5001`）。
- 输出所有服务的访问地址和 API 服务的运行状态。

### 5.3. 交互方式

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

### 5.4. 停止服务

使用以下脚本来停止由 `start_media_services.sh` 启动的所有 Docker 容器和后台 API 进程。

```bash
bash ./stop_media_services.sh
```

## 6. 工具说明

Agent 的所有功能均通过调用以下工具来实现。这些工具是连接大语言模型（LLM）与底层媒体服务（Radarr, Sonarr, qBittorrent）的桥梁。

---

### 通用工具

-   **`ask_user_for_clarification(question: str) -> str`**
    -   **功能**: 当用户的指令意图不明确时（例如，同时可能指电影和电视剧），LLM会使用此工具来向用户提问，请求更具体的信息。
    -   **触发场景**: 用户输入"搜索'阿凡达'"。
    -   **模型行为**: 调用此工具，并向用户返回问题："您是想搜索电影还是电视剧？"
    -   **返回类型**: `str` - 格式化的中文问题字符串，用于向用户请求澄清

---

### 电影管理 (Radarr)

-   **`search_movie(query: str) -> str`**
    -   **功能**: 根据用户提供的关键词搜索电影。
    -   **实现**: 调用 `radarr_tool.search_movie_logic`，通过 Radarr API 查找电影。
    -   **返回类型**: `str` - 格式化的中文搜索结果字符串，包含电影标题、年份、TMDB ID，格式如："找到了 X 部电影:\n1. 电影: 标题, 年份: 年份, TMDB ID: ID\n--- 搜索结果结束 ---"

-   **`download_movie(tmdb_id: int) -> str`**
    -   **功能**: 根据电影的 TMDB ID，将其添加到 Radarr 中并触发搜索下载。
    -   **实现**: 调用 `radarr_tool.download_movie_logic`。该函数会先用 TMDB ID 确认电影信息，然后通过 Radarr API 添加电影。
    -   **返回类型**: `str` - 操作结果字符串，成功时返回："已成功将电影 '标题 (年份)' 添加到Radarr，并开始搜索下载。"，失败时返回错误信息

-   **`get_radarr_queue() -> str`**
    -   **功能**: 查询 Radarr 当前的活动队列，了解电影的下载状态。
    -   **实现**: 调用 `radarr_tool.get_radarr_queue_logic`。
    -   **返回类型**: `str` - 格式化的队列状态字符串，包含队列项目数量、每个项目的标题、状态、队列ID、剩余时间、下载进度等信息

-   **`get_all_movies() -> str`**
    -   **功能**: 获取 Radarr 电影库中的所有电影列表。
    -   **实现**: 调用 `radarr_tool.get_all_movies_logic`。
    -   **返回类型**: `str` - 格式化的电影库列表字符串，包含每部电影的标题、年份、ID、监控状态（已监控/未监控）、下载状态（已下载/未下载）

-   **`delete_movie(movie_id: int) -> str`**
    -   **功能**: 从 Radarr 电影库中删除指定的电影（永久移除）。
    -   **实现**: 调用 `radarr_tool.delete_movie_logic`。
    -   **返回类型**: `str` - 删除操作结果字符串，成功时返回："已成功删除电影 '标题' (ID: ID)。"，失败时返回错误信息

-   **`get_radarr_queue_item_details(queue_id: int) -> str`**
    -   **功能**: 获取 Radarr 队列中特定项目的详细信息。
    -   **实现**: 调用 `radarr_tool.get_radarr_queue_item_details_logic`。
    -   **返回类型**: `str` - 详细的队列项目信息字符串，包含标题、状态、剩余时间、文件大小、下载进度、下载协议、索引器、状态消息、错误信息等

-   **`delete_radarr_queue_item(queue_id: int) -> str`**
    -   **功能**: 删除 Radarr 下载队列中的特定任务（停止下载，移除任务，清理相关文件）。
    -   **实现**: 调用 `radarr_tool.delete_radarr_queue_item_logic`。
    -   **返回类型**: `str` - 删除操作结果字符串，成功时返回："已成功删除队列项目 (队列ID: ID)。"，失败时返回错误信息或"队列项目不存在"提示

---

### 电视剧管理 (Sonarr)

-   **`search_series(query: str) -> str`**
    -   **功能**: 根据用户提供的关键词搜索电视剧。
    -   **实现**: 调用 `sonarr_tool.search_series_logic`，通过 Sonarr API 进行查找。
    -   **返回类型**: `str` - 格式化的中文搜索结果字符串，包含电视剧标题、年份、TVDB ID，格式如："找到了 X 部电视剧:\n1. 电视剧: 标题, 年份: 年份, TVDB ID: ID\n--- 搜索结果结束 ---"

-   **`download_series(tvdb_id: int, seasons: Union[str, list[int]]) -> str`**
    -   **功能**: 根据电视剧的 TVDB ID，将其添加到 Sonarr，并指定下载特定季度或全部季度。
    -   **实现**: 调用 `sonarr_tool.download_series_logic`。`seasons` 参数可以是一个季度编号的列表（如 `[1, 3]`），也可以是字符串 `'all'`。
    -   **返回类型**: `str` - 操作结果字符串，成功时返回："成功将电视剧 '标题' 的第 X 季添加到Sonarr，并开始搜索下载。"，失败时返回错误信息或"已存在"提示

-   **`get_sonarr_queue() -> str`**
    -   **功能**: 查询 Sonarr 当前的活动队列，了解剧集的下载状态。
    -   **实现**: 调用 `sonarr_tool.get_sonarr_queue_logic`。
    -   **返回类型**: `str` - 格式化的队列状态字符串，包含队列项目数量、每个项目的电视剧标题、剧集信息、状态、队列ID、剩余时间、下载进度等信息

-   **`get_all_series() -> str`**
    -   **功能**: 获取 Sonarr 电视剧库中的所有电视剧列表。
    -   **实现**: 调用 `sonarr_tool.get_all_series_logic`。
    -   **返回类型**: `str` - 格式化的电视剧库列表字符串，包含每部电视剧的标题、年份、ID、监控状态（已监控/未监控）、下载状态（已下载/未下载）、季度数

-   **`delete_series(series_id: int) -> str`**
    -   **功能**: 从 Sonarr 电视剧库中删除指定的电视剧（永久移除）。
    -   **实现**: 调用 `sonarr_tool.delete_series_logic`。
    -   **返回类型**: `str` - 删除操作结果字符串，成功时返回："已成功删除电视剧 '标题' (ID: ID)。"，失败时返回错误信息

-   **`get_sonarr_queue_item_details(queue_id: int) -> str`**
    -   **功能**: 获取 Sonarr 队列中特定项目的详细信息。
    -   **实现**: 调用 `sonarr_tool.get_sonarr_queue_item_details_logic`。
    -   **返回类型**: `str` - 详细的队列项目信息字符串，包含电视剧标题、剧集信息、状态、剩余时间、文件大小、下载进度、下载协议、索引器、状态消息、错误信息等

-   **`delete_sonarr_queue_item(queue_id: int) -> str`**
    -   **功能**: 删除 Sonarr 下载队列中的特定任务（停止下载，移除任务，清理相关文件）。
    -   **实现**: 调用 `sonarr_tool.delete_sonarr_queue_item_logic`。
    -   **返回类型**: `str` - 删除操作结果字符串，成功时返回："已成功删除队列项目 (队列ID: ID)。"，失败时返回错误信息或"队列项目不存在"提示

---

### 下载器管理 (qBittorrent)

-   **`get_torrents() -> str`**
    -   **功能**: 获取 qBittorrent 中当前所有种子任务的列表和状态。
    -   **实现**: 调用 `qbittorrent_tool.get_torrents_logic`。
    -   **返回类型**: `str` - 格式化的种子状态字符串，包含种子名称、状态、下载进度，最多显示前10个任务，格式如："当前种子列表:\n种子: 名称, 状态: 状态, 进度: XX.XX%"

---

## 7. 日志与监控

- **媒体服务日志**: 位于 `media_agent/logs/` 下，如 `radarr.log`, `sonarr.log` 等。
- **API 服务日志**: 位于 `media_agent/logs/api.log`。
- **实时查看日志**:
  ```bash
  # 查看 API 日志
  tail -f media_agent/logs/api.log

  # 查看 Radarr 日志
  tail -f media_agent/logs/radarr.log
  ``` 