# 媒体服务配置指南

## 目录结构

```
media-agent/
├── docker/                 # Docker 配置目录
│   ├── docker-compose.yml # Docker 编排配置文件
│   ├── radarr/           # Radarr 配置文件目录
│   ├── sonarr/           # Sonarr 配置文件目录
│   └── qbittorrent/      # qBittorrent 配置文件目录
└── data/                  # 媒体数据目录
    ├── downloads/        # 下载目录
    │   └── incomplete/   # 未完成的下载
    ├── movies/          # 电影存储目录
    └── tv_shows/        # 电视剧存储目录
```

## 服务访问信息

### qBittorrent
- 访问地址：`http://<你的IP>:8081`
- 默认用户名：`admin`
- 默认密码：123456
- 端口：
  - Web UI: 8081
  - BT: 6881 (TCP/UDP)

### Radarr (电影)
- 访问地址：`http://<你的IP>:7878`
- 端口：7878

### Sonarr (电视剧)
- 访问地址：`http://<你的IP>:8989`
- 端口：8989

## 使用说明

### 添加新电影
1. 在 Radarr 中搜索电影
2. 选择质量配置
3. 选择保存路径（/movies 下的子目录）
4. 添加并搜索

### 添加新电视剧
1. 在 Sonarr 中搜索剧集
2. 选择季数和质量配置
3. 选择保存路径（/tv 下的子目录）
4. 添加并搜索

### 下载管理
- 所有下载任务都会自动发送到 qBittorrent
- 下载完成后会自动移动到对应的媒体目录
- 可以在 qBittorrent 中查看下载进度
- Radarr 和 Sonarr 会自动重命名和整理文件

## 故障排查

### 连接问题
1. 确保所有服务都在运行：
   ```bash
   docker compose ps
   ```

2. 检查服务日志：
   ```bash
   docker compose logs qbittorrent
   docker compose logs radarr
   docker compose logs sonarr
   ```

3. 检查网络连接：
   ```bash
   docker network inspect media_net
   ```

### 权限问题
如果遇到文件权限问题：
1. 确认当前用户在 docker 组中：
   ```bash
   groups
   ```
2. 检查目录权限：
   ```bash
   ls -l data/
   ```

## 更新服务

更新服务版本：
```bash
cd media-agent/docker
docker compose pull
docker compose up -d
```
