# 智能影视资源管理Agent系统

本项目是一个基于LangChain框架的智能Agent系统，通过自然语言交互实现影视资源的智能搜索、管理和下载。系统集成了Radarr（电影管理）、Sonarr（电视剧管理）和qBittorrent（下载客户端），并使用本地Ollama服务提供的LLM模型。

## 功能特点

- 自然语言交互界面
- 智能搜索电影和电视剧
- 自动下载管理
- 媒体文件自动分类
- API接口支持

## 安装要求

- Python 3.9+
- Ollama服务
- Radarr
- Sonarr
- qBittorrent

## 快速开始

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 复制配置文件：`cp .env.example .env`
4. 编辑 `.env` 文件，填入您的配置
5. 运行：`python main.py`

## 使用方法

### 命令行模式
```bash
python main.py --mode cli
```

### API模式
```bash
python main.py --mode api
```
