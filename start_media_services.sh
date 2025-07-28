#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取项目根目录的绝对路径
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
MEDIA_AGENT_ROOT="$PROJECT_ROOT/media_agent"
LOGS_DIR="$MEDIA_AGENT_ROOT/logs"

# 创建日志目录（如果不存在）
mkdir -p "$LOGS_DIR"

# 定义日志文件
RADARR_LOG="$LOGS_DIR/radarr.log"
SONARR_LOG="$LOGS_DIR/sonarr.log"
QBIT_LOG="$LOGS_DIR/qbittorrent.log"
JACKETT_LOG="$LOGS_DIR/jackett.log"
SYSTEM_LOG="$LOGS_DIR/system.log"

# 修改后的日志函数 - 只写入文件，不输出到终端，自动维护行数限制
log_silent() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    write_log_with_limit "$SYSTEM_LOG" "[$timestamp] $1"
}

# 显示信息的函数 - 只在终端显示，不写入日志
show_info() {
    echo -e "$1"
}

# 既显示又记录的函数，带行数限制
log_and_show() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    write_log_with_limit "$SYSTEM_LOG" "[$timestamp] $1"
    echo -e "$1"
}

# 清理旧的日志文件，保持2500行
clean_logs() {
    for log_file in "$RADARR_LOG" "$SONARR_LOG" "$QBIT_LOG" "$JACKETT_LOG" "$SYSTEM_LOG"; do
        if [ -f "$log_file" ]; then
            # 保存最后2500行日志
            tail -n 2500 "$log_file" > "${log_file}.tmp"
            mv "${log_file}.tmp" "$log_file"
        fi
    done
}

# 智能写入日志函数 - 自动维护行数限制
write_log_with_limit() {
    local log_file="$1"
    local content="$2"
    local max_lines=2500
    
    # 写入新日志行
    echo "$content" >> "$log_file"
    
    # 检查行数，如果超过限制则清理
    local current_lines=$(wc -l < "$log_file" 2>/dev/null || echo 0)
    if [ "$current_lines" -gt "$max_lines" ]; then
        tail -n "$max_lines" "$log_file" > "${log_file}.tmp"
        mv "${log_file}.tmp" "$log_file"
    fi
}

# 启动时清理日志
clean_logs

# 获取公网IP
show_info "${BLUE}正在获取服务器公网IP...${NC}"
PUBLIC_IP=$(curl -s https://api.ipify.org || curl -s http://ifconfig.me || curl -s icanhazip.com)
if [ -z "$PUBLIC_IP" ]; then
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    SERVER_IP=$LOCAL_IP
    show_info "${YELLOW}警告: 无法获取公网IP，使用本地IP地址: ${SERVER_IP}${NC}"
else
    SERVER_IP=$PUBLIC_IP
    show_info "${GREEN}获取到公网IP: ${SERVER_IP}${NC}"
fi

show_info "\n${GREEN}开始启动媒体服务...${NC}"
show_info "项目目录: ${YELLOW}$PROJECT_ROOT${NC}"
show_info "媒体服务目录: ${YELLOW}$MEDIA_AGENT_ROOT${NC}"

# 定义服务端口映射
declare -A service_ports
service_ports["radarr"]=7878
service_ports["sonarr"]=8989
service_ports["qbittorrent"]=8081
service_ports["jackett"]=9117

# 确保目录存在
if [ ! -d "$MEDIA_AGENT_ROOT" ]; then
    show_info "${RED}错误: 找不到媒体服务目录${NC}"
    exit 1
fi

# 进入docker目录
cd "$MEDIA_AGENT_ROOT/docker" || exit

# 启动服务
log_and_show "启动 Radarr, Sonarr, qBittorrent 和 Jackett 服务..."
docker compose up -d

# === 关键修改：静默收集日志，自动维护行数限制 ===
log_silent "开始收集服务日志..."

# 创建日志收集的后台进程 - 完全静默运行，自动管理日志文件大小
{
    docker compose logs -f --tail=100 | while IFS= read -r line; do
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        timestamped_line="$timestamp $line"
        
        # 根据内容分类写入不同的日志文件，自动维护行数限制
        case "$line" in
            *radarr*)
                write_log_with_limit "$RADARR_LOG" "$timestamped_line"
                ;;
            *sonarr*)
                write_log_with_limit "$SONARR_LOG" "$timestamped_line"
                ;;
            *qbittorrent*)
                write_log_with_limit "$QBIT_LOG" "$timestamped_line"
                ;;
            *jackett*)
                write_log_with_limit "$JACKETT_LOG" "$timestamped_line"
                ;;
        esac
    done
} >> /dev/null 2>&1 & # 重定向到 /dev/null，完全静默

# 保存日志收集进程的PID
echo $! > "$LOGS_DIR/logging.pid"

# 检查服务状态
log_silent "检查服务状态..."
sleep 5 # 等待服务启动

# 检查各个服务
services=("radarr" "sonarr" "qbittorrent" "jackett")
all_running=true

show_info "\n${YELLOW}服务状态和访问地址：${NC}"
show_info "───────────────────────────────────────────────────"

for service in "${services[@]}"
do
    if docker compose ps "$service" | grep -q "Up"; then
        port=${service_ports[$service]}
        show_info "${GREEN}✓ $service${NC}"
        show_info "  访问地址: ${BLUE}http://$SERVER_IP:$port${NC}"
        show_info "  端口: ${YELLOW}$port${NC} (TCP)"
        
        # 为qBittorrent添加额外的端口信息
        if [ "$service" == "qbittorrent" ]; then
            show_info "  BT端口: ${YELLOW}6881${NC} (TCP/UDP)"
        fi
        show_info "───────────────────────────────────────────────────"
    else
        show_info "${RED}✗ $service 启动失败${NC}"
        show_info "───────────────────────────────────────────────────"
        all_running=false
    fi
done

if [ "$all_running" = true ]; then
    show_info "\n${GREEN}所有服务已成功启动！${NC}"
    show_info "\n${YELLOW}登录信息：${NC}"
    show_info "qBittorrent:"
    show_info "  用户名: ${BLUE}admin${NC}"
    show_info "  密码: ${BLUE}$(docker compose logs qbittorrent 2>&1 | grep "temporary password" | awk -F': ' '{print $2}')${NC}"
    
    show_info "\n${YELLOW}日志文件位置（每个文件最多保存2500行）：${NC}"
    show_info "  系统日志: ${LOGS_DIR}/system.log"
    show_info "  Radarr日志: ${LOGS_DIR}/radarr.log"
    show_info "  Sonarr日志: ${LOGS_DIR}/sonarr.log"
    show_info "  qBittorrent日志: ${LOGS_DIR}/qbittorrent.log"
    show_info "  Jackett日志: ${LOGS_DIR}/jackett.log"
    
    show_info "\n${YELLOW}查看实时日志命令：${NC}"
    show_info "  查看所有服务: docker compose logs -f"
    show_info "  查看Radarr: tail -f ${LOGS_DIR}/radarr.log"
    show_info "  查看Sonarr: tail -f ${LOGS_DIR}/sonarr.log"
    show_info "  查看qBittorrent: tail -f ${LOGS_DIR}/qbittorrent.log"
    show_info "  查看Jackett: tail -f ${LOGS_DIR}/jackett.log"
    
    show_info "\n${YELLOW}日志管理说明：${NC}"
    show_info "  • 每个日志文件自动维护最多2500行"
    show_info "  • 新日志会自动挤掉最老的日志行"
    show_info "  • 手动清理所有日志：clean_logs函数"
else
    show_info "\n${RED}部分服务启动失败，请检查日志获取详细信息${NC}"
    show_info "使用以下命令查看详细日志："
    show_info "${YELLOW}docker compose logs${NC}"
    exit 1
fi

# 添加停止日志收集的函数说明
show_info "\n${YELLOW}停止日志收集：${NC}"
show_info "  kill \$(cat ${LOGS_DIR}/logging.pid)"