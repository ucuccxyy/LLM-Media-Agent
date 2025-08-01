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
        
        total_found = len(search_results)
        movies_info = [f"找到了 {total_found} 部电影:"]
        for i, movie in enumerate(search_results):
            title = movie.get('title', 'N/A')
            year = movie.get('year', 'N/A')
            tmdb_id = movie.get('tmdbId', 'N/A')
            movies_info.append(f"{i+1}. 电影: {title}, 年份: {year}, TMDB ID: {tmdb_id}")
        
        movies_info.append("--- 搜索结果结束 ---")
        return "\n".join(movies_info)
    except Exception as e:
        return f"搜索电影时发生错误: {e}"

def download_movie_logic(tmdb_id: int) -> str:
    """根据TMDB ID添加并下载电影的逻辑。"""
    settings = Settings()
    settings.load_from_env()
    radarr_service = RadarrService(settings.radarr_host, settings.radarr_api_key)
    
    # 首先通过TMDB ID查找电影以获取其详细信息
    try:
        # Radarr的lookup需要的是搜索词，但我们可以通过movie接口直接获取详情
        # 这里假设我们有一个按TMDB ID查找的函数，或者我们先搜索再匹配
        # 为了简化，我们直接用tmdb_id去获取信息
        # 注意：Radarr的lookup是按名字，但add是按tmdbId
        # 我们需要先获取电影的完整信息
        search_results = radarr_service.lookup_movie(f"tmdb:{tmdb_id}")
        if not search_results:
            return f"错误: 在Radarr中通过TMDB ID: {tmdb_id} 未找到任何电影。"
            
        movie_to_add = search_results[0]
        # 在添加电影之前，先获取电影的年份
        movie_year = movie_to_add.get('year')
        movie_title = movie_to_add.get('title')

        radarr_service.add_movie(movie_to_add)
        
        return f"已成功将电影 '{movie_title} ({movie_year})' 添加到Radarr，并开始搜索下载。"
    except Exception as e:
        return f"错误: 添加电影时出错: {e}"

def get_radarr_queue_logic() -> str:
    """获取Radarr下载队列状态的逻辑。"""
    try:
        queue = radarr_service.get_queue()
        if not queue or not queue.get('records'):
            return "Radarr下载队列当前为空。"
        
        queue_info = []
        for item in queue['records']: # Top 5 items
            title = item.get('title', 'N/A')
            status = item.get('status', 'N/A')
            timeleft = item.get('timeleft', 'N/A')
            queue_info.append(f"电影: {title}, 状态: {status}, 剩余时间: {timeleft}")
            
        return "当前Radarr下载队列:\n" + "\n".join(queue_info)
    except Exception as e:
        return f"获取Radarr队列时发生错误: {e}"