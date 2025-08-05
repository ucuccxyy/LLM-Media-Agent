#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
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
    echo -e "${GREEN}所有媒体服务已成功停止${NC}"
fi

# --- 停止日志收集进程 ---
LOGS_DIR="$(dirname "$0")/media_agent/logs"
LOGGING_PID_FILE="$LOGS_DIR/logging.pid"

if [ -f "$LOGGING_PID_FILE" ]; then
    LOG_PID=$(cat "$LOGGING_PID_FILE")
    if ps -p "$LOG_PID" > /dev/null; then
        echo "正在停止日志收集进程 (PID: $LOG_PID)..."
        kill "$LOG_PID"
        rm "$LOGGING_PID_FILE"
        echo -e "${GREEN}日志收集进程已停止。${NC}"
    else
        echo -e "${YELLOW}发现过期的日志收集PID文件，已移除。${NC}"
        rm "$LOGGING_PID_FILE"
    fi
fi

# --- 停止 API 服务 ---
echo -e "\n${GREEN}开始停止 API 服务...${NC}"

PROJECT_ROOT="$(dirname "$0")"
PID_DIR="$PROJECT_ROOT/media_agent/pids"
PID_FILE="$PID_DIR/api.pid"

if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}API 服务未在运行 (未找到PID文件)。${NC}"
else
    API_PID=$(cat "$PID_FILE")
    if ! ps -p "$API_PID" > /dev/null; then
        echo -e "${YELLOW}API 服务未在运行 (PID $API_PID 无效)。${NC}"
        rm "$PID_FILE"
    else
        echo "正在停止 API 服务 (PID: $API_PID)..."
        kill "$API_PID"
        sleep 2
        if ps -p "$API_PID" > /dev/null; then
            echo -e "${RED}API 服务未能正常停止，强制关闭...${NC}"
            kill -9 "$API_PID"
        fi
        rm "$PID_FILE"
        echo -e "${GREEN}API 服务已成功停止。${NC}"
    fi
fi

# --- 清空所有日志文件 ---
echo -e "\n${YELLOW}正在清空所有日志文件...${NC}"

# 清空各个服务的日志文件
log_files=(
    "$LOGS_DIR/radarr.log"
    "$LOGS_DIR/sonarr.log"
    "$LOGS_DIR/qbittorrent.log"
    "$LOGS_DIR/jackett.log"
    "$LOGS_DIR/system.log"
    "$LOGS_DIR/api.log"
)

for log_file in "${log_files[@]}"; do
    if [ -f "$log_file" ]; then
        > "$log_file"  # 清空文件内容
        echo -e "${GREEN}已清空: $(basename "$log_file")${NC}"
    fi
done

echo -e "\n${GREEN}所有服务和进程已全部停止，日志文件已清空。${NC}"