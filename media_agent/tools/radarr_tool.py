"""
Radarr集成工具的纯逻辑实现
"""

from typing import List, Dict
import sys
import os

from media_agent.services.radarr_service import RadarrService
from media_agent.config.settings import Settings

settings = Settings()
radarr_service = RadarrService(host=settings.radarr_host, api_key=settings.radarr_api_key)

def search_movie_logic(query: str) -> str:
    """根据关键词搜索电影的逻辑。"""
    try:
        search_results = radarr_service.lookup_movie(query)
        if not search_results:
            return f"找不到关于 '{query}' 的电影。"
        
        movies_info = []
        for movie in search_results[:5]:
            title = movie.get('title', 'N/A')
            year = movie.get('year', 'N/A')
            tmdb_id = movie.get('tmdbId', 'N/A')
            movies_info.append(f"电影: {title}, 年份: {year}, TMDB ID: {tmdb_id}")
        
        return "\n".join(movies_info)
    except Exception as e:
        return f"搜索电影时发生错误: {e}"

def download_movie_logic(tmdb_id: int) -> str:
    """添加电影到Radarr并触发下载的逻辑。"""
    try:
        # 查找电影的完整信息
        lookup_results = radarr_service.lookup_movie(f"tmdb:{tmdb_id}")
        if not lookup_results:
            return f"错误: 通过 TMDB ID {tmdb_id} 未找到电影。"
        movie_data = lookup_results[0]
        
        # 调用服务层添加电影
        result = radarr_service.add_movie(movie_data)
        
        # 处理响应
        if result and result.get('id'):
            return f"成功将电影 '{result.get('title')}' 添加到Radarr，并开始搜索下载。"
        elif result and 'already exists' in result.get('message', '').lower():
            return f"电影 '{movie_data.get('title')}' 已存在于Radarr中。"
        else:
            # 记录更详细的错误以供调试
            error_details = str(result)
            return f"添加电影失败，Radarr返回的响应: {error_details}"

    except Exception as e:
        return f"添加电影时发生未知错误: {str(e)}"

def get_radarr_queue_logic() -> str:
    """获取Radarr下载队列状态的逻辑。"""
    try:
        queue = radarr_service.get_queue()
        if not queue or not queue.get('records'):
            return "Radarr下载队列当前为空。"
        
        queue_info = []
        for item in queue['records'][:5]: # Top 5 items
            title = item.get('title', 'N/A')
            status = item.get('status', 'N/A')
            timeleft = item.get('timeleft', 'N/A')
            queue_info.append(f"电影: {title}, 状态: {status}, 剩余时间: {timeleft}")
            
        return "当前Radarr下载队列:\n" + "\n".join(queue_info)
    except Exception as e:
        return f"获取Radarr队列时发生错误: {e}"