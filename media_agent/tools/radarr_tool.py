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
        

        
        if not queue:
            return "Radarr下载队列当前为空。"
        
        # 检查队列结构 - 更灵活的处理
        records = []
        total_records = 0
        
        if isinstance(queue, dict):
            # 标准格式：包含records字段
            if 'records' in queue:
                records = queue.get('records', [])
                total_records = queue.get('totalRecords', len(records))
            else:
                # 可能是其他格式，尝试直接使用
                records = [queue] if queue else []
                total_records = 1 if queue else 0
        elif isinstance(queue, list):
            # 直接是数组格式
            records = queue
            total_records = len(records)
        else:
            return f"Radarr队列响应格式异常: {queue}"
        
        if not records:
            return "Radarr下载队列当前为空。"
        
        queue_info = [f"Radarr下载队列 (共 {total_records} 个项目):"]
        
        for i, item in enumerate(records, 1):
            title = item.get('title', 'N/A')
            status = item.get('status', 'N/A')
            timeleft = item.get('timeleft', 'N/A')
            size = item.get('size', 0)
            sizeleft = item.get('sizeleft', 0)
            queue_id = item.get('id', 'N/A')  # 获取队列项目ID
            
            # 格式化文件大小
            if size > 0:
                size_mb = size / (1024 * 1024)
                sizeleft_mb = sizeleft / (1024 * 1024)
                progress = ((size - sizeleft) / size * 100) if size > 0 else 0
                size_info = f"进度: {progress:.1f}% ({sizeleft_mb:.1f}MB/剩余)"
            else:
                size_info = "大小: 未知"
            
            queue_info.append(f"{i}. {title} [队列ID: {queue_id}]")
            queue_info.append(f"   状态: {status}, 剩余时间: {timeleft}")
            queue_info.append(f"   {size_info}")
            queue_info.append("")  # 空行分隔
        
        return "\n".join(queue_info)
    except Exception as e:
        return f"获取Radarr队列时发生错误: {e}"

def get_all_movies_logic() -> str:
    """获取所有电影列表的逻辑。"""
    try:
        movies = radarr_service.get_all_movies()
        if not movies:
            return "Radarr电影库当前为空。"
        
        total_movies = len(movies)
        movies_info = [f"Radarr电影库中共有 {total_movies} 部电影:"]
        
        for i, movie in enumerate(movies, 1):
            title = movie.get('title', 'N/A')
            year = movie.get('year', 'N/A')
            movie_id = movie.get('id', 'N/A')
            monitored = "已监控" if movie.get('monitored', False) else "未监控"
            has_file = "已下载" if movie.get('hasFile', False) else "未下载"
            movies_info.append(f"{i}. {title} ({year}) - ID: {movie_id} - {monitored} - {has_file}")
        
        movies_info.append("--- 电影列表结束 ---")
        return "\n".join(movies_info)
    except Exception as e:
        return f"获取电影列表时发生错误: {e}"

def delete_movie_logic(movie_id: int) -> str:
    """删除电影的逻辑。"""
    try:
        # 首先获取电影信息以确认删除
        movie_info = radarr_service.get_movie(movie_id)
        if not movie_info:
            return f"错误: 找不到ID为 {movie_id} 的电影。"
        
        movie_title = movie_info.get('title', '未知电影')
        
        # 执行删除操作
        success = radarr_service.delete_movie(movie_id)
        
        if success:
            return f"已成功删除电影 '{movie_title}' (ID: {movie_id})。"
        else:
            return f"删除电影 '{movie_title}' (ID: {movie_id}) 时发生错误。"
    except Exception as e:
        return f"删除电影时发生错误: {e}"

def get_radarr_queue_item_details_logic(queue_id: int) -> str:
    """获取Radarr队列项目详情的逻辑。"""
    try:
        queue_details = radarr_service.get_queue_item_details(queue_id)
        if not queue_details:
            return f"错误: 找不到ID为 {queue_id} 的队列项目。"
        
        # 格式化详细信息
        details_info = [f"Radarr队列项目详情 (ID: {queue_id}):"]
        
        # 基本信息
        title = queue_details.get('title', 'N/A')
        status = queue_details.get('status', 'N/A')
        timeleft = queue_details.get('timeleft', 'N/A')
        size = queue_details.get('size', 0)
        sizeleft = queue_details.get('sizeleft', 0)
        
        details_info.append(f"标题: {title}")
        details_info.append(f"状态: {status}")
        details_info.append(f"剩余时间: {timeleft}")
        
        # 格式化文件大小和进度
        if size > 0:
            size_mb = size / (1024 * 1024)
            sizeleft_mb = sizeleft / (1024 * 1024)
            progress = ((size - sizeleft) / size * 100) if size > 0 else 0
            details_info.append(f"总大小: {size_mb:.1f} MB")
            details_info.append(f"剩余大小: {sizeleft_mb:.1f} MB")
            details_info.append(f"下载进度: {progress:.1f}%")
        else:
            details_info.append("文件大小: 未知")
        
        # 下载信息
        download_info = queue_details.get('downloadInfo', {})
        if download_info:
            protocol = download_info.get('protocol', 'N/A')
            indexer = download_info.get('indexer', 'N/A')
            details_info.append(f"下载协议: {protocol}")
            details_info.append(f"索引器: {indexer}")
        
        # 状态消息
        status_messages = queue_details.get('statusMessages', [])
        if status_messages:
            details_info.append("状态消息:")
            for msg in status_messages:
                details_info.append(f"  - {msg.get('title', 'N/A')}: {msg.get('messages', [])}")
        
        # 错误信息（如果有）
        error_message = queue_details.get('errorMessage')
        if error_message:
            details_info.append(f"错误信息: {error_message}")
        
        details_info.append("--- 详情结束 ---")
        return "\n".join(details_info)
    except Exception as e:
        return f"获取队列项目详情时发生错误: {e}"

def delete_radarr_queue_item_logic(queue_id: int) -> str:
    """删除Radarr队列项目的逻辑。"""
    try:
        # 尝试直接删除队列项目，不预先验证
        success = radarr_service.delete_queue_item(queue_id)
        
        if success:
            return f"已成功删除队列项目 (队列ID: {queue_id})。"
        else:
            return f"删除队列项目 (队列ID: {queue_id}) 时发生错误。"
    except Exception as e:
        # 如果删除失败，检查是否是404错误（项目不存在）
        if "404" in str(e) or "Not Found" in str(e):
            return f"队列项目 (ID: {queue_id}) 不存在或已被删除。"
        else:
            return f"删除队列项目时发生错误: {e}"