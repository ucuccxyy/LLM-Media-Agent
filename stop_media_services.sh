#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始停止媒体服务...${NC}"

# 进入docker目录
cd "$(dirname "$0")/media_agent/docker" || exit

# 检查docker是否安装
if ! command -v docker &> /dev/null
then
    echo -e "${RED}错误: docker未安装${NC}"
    exit 1
fi

# 停止服务
echo "正在停止 Radarr, Sonarr, qBittorrent 和 Jackett 服务..."
docker compose down

# 检查是否有残留容器
if docker ps | grep -q -E 'radarr|sonarr|qbittorrent|jackett'; then
    echo -e "${RED}警告：某些容器可能未正常停止${NC}"
    echo "尝试强制停止..."
    docker compose down -v --remove-orphans
else
    echo -e "${GREEN}所有服务已成功停止${NC}"
fi