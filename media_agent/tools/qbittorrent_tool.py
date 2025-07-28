"""
qBittorrent集成工具的纯逻辑实现
"""

import sys
import os

from media_agent.services.qbittorrent_service import QBittorrentService
from media_agent.config.settings import Settings

settings = Settings()
qb_service = QBittorrentService(
    host=settings.qbittorrent_host,
    username=settings.qbittorrent_username,
    password=settings.qbittorrent_password
)

def get_torrents_logic() -> str:
    """获取当前所有种子的列表和状态的逻辑。"""
    try:
        torrents = qb_service.get_torrents()
        if not torrents:
            return "当前没有活动的种子。"
        
        torrent_info = []
        for torrent in torrents[:10]: # Top 10 torrents
            name = torrent.get('name', 'N/A')
            state = torrent.get('state', 'N/A')
            progress = torrent.get('progress', 0) * 100
            torrent_info.append(f"种子: {name}, 状态: {state}, 进度: {progress:.2f}%")
            
        return "当前种子列表:\n" + "\n".join(torrent_info)
    except Exception as e:
        return f"获取种子列表时发生错误: {e}"

def get_torrent_info_logic(hash: str, qb_service: QBittorrentService) -> str:
    """根据种子哈希值获取其详细信息的逻辑。"""
    try:
        torrent_list = qb_service.get_torrent_info(hash)
        if not torrent_list:
            return f"未找到哈希值为 '{hash}' 的种子。"
        
            t = torrent_list[0]
        properties = qb_service.get_torrent_properties(hash)
        
        name = t.get('name', '未知')
        progress = t.get('progress', 0) * 100
        dlspeed = t.get('dlspeed', 0) / 1024
        upspeed = t.get('upspeed', 0) / 1024
        state = t.get('state', '未知')
        save_path = properties.get('save_path', '未知')
        total_size = t.get('total_size', 0) / (1024 * 1024)  # MB

        formatted = (
            f"种子详细信息 (哈希: {hash}):\n"
            f"  名称: {name}\n"
            f"  状态: {state}\n"
            f"  进度: {progress:.1f}%\n"
            f"  下载速度: {dlspeed:.1f} KB/s\n"
            f"  上传速度: {upspeed:.1f} KB/s\n"
            f"  保存路径: {save_path}\n"
            f"  总大小: {total_size:.1f} MB"
        )
        return formatted
    except Exception as e:
        return f"获取种子详细信息时发生错误: {e}"


