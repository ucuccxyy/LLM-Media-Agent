"""
Sonarr集成工具的纯逻辑实现
"""

from typing import List, Dict, Union
import sys
import os
from pydantic import BaseModel, Field

from media_agent.services.sonarr_service import SonarrService
from media_agent.config.settings import Settings
from langchain_core.tools import tool

settings = Settings()
sonarr_service = SonarrService(host=settings.sonarr_host, api_key=settings.sonarr_api_key)

def search_series_logic(query: str) -> str:
    """根据关键词搜索电视剧的逻辑。"""
    try:
        search_results = sonarr_service.lookup_series(query)
        if not search_results:
            return f"找不到关于 '{query}' 的电视剧。"
        
        total_found = len(search_results)
        series_info = [f"找到了 {total_found} 部电视剧:"]
        for i, series in enumerate(search_results):
            title = series.get('title', 'N/A')
            year = series.get('year', 'N/A')
            tvdb_id = series.get('tvdbId', 'N/A')
            series_info.append(f"{i+1}. 电视剧: {title}, 年份: {year}, TVDB ID: {tvdb_id}")
        
        series_info.append("--- 搜索结果结束 ---")
        return "\n".join(series_info)
    except Exception as e:
        return f"搜索电视剧时发生错误: {e}"

class DownloadSeriesInput(BaseModel):
    """用于下载电视剧工具的输入模型。"""
    tvdb_id: int = Field(..., description="要下载的电视剧的TheTVDB ID。")
    seasons: Union[str, List[int]] = Field(
        ..., 
        description="要下载的季度编号列表 (例如 [1, 2, 3]) 或字符串 'all' (下载所有季度)。"
    )

def download_series_logic(tvdb_id: int, seasons: Union[str, list[int]]) -> str:
    """
    添加电视剧到Sonarr并下载指定的季度。
    seasons 参数可以是季度编号的列表 (例如 [1, 2, 3]) 或字符串 'all' (下载所有季度)。
    """
    try:
        # 直接将TVDB ID和季度信息传递给服务层
        # 服务层将负责查找和添加电视剧
        result = sonarr_service.add_series(tvdb_id, seasons)

        if result and result.get('id'):
            return f"成功将电视剧 '{result.get('title')}' 的第 {seasons} 季添加到Sonarr，并开始搜索下载。"
        # 检查是否因为“已存在”而失败
        elif result and result.get('status') == 'exists':
             # 从已存在的消息中提取标题可能比较复杂，这里使用TVDB ID
             return f"电视剧 (TVDB ID: {tvdb_id}) 已存在于Sonarr中。"
        else:
            # result 为 None 或其他未知错误
            error_details = str(result) if result else "无详细响应"
            return f"添加电视剧时失败，Sonarr返回的响应: {error_details}"
            
    except Exception as e:
        return f"添加电视剧时发生未知错误: {str(e)}"

def get_sonarr_queue_logic() -> str:
    """获取Sonarr下载队列状态的逻辑。"""
    try:
        queue = sonarr_service.get_queue()
        

        
        if not queue:
            return "Sonarr下载队列当前为空。"
        
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
            return f"Sonarr队列响应格式异常: {queue}"
        
        if not records:
            return "Sonarr下载队列当前为空。"
        
        queue_info = [f"Sonarr下载队列 (共 {total_records} 个项目):"]
        
        for i, item in enumerate(records, 1):
            # 获取电视剧和剧集信息
            series_info = item.get('series', {})
            episode_info = item.get('episode', {})
            
            series_title = series_info.get('title', 'N/A')
            episode_title = episode_info.get('title', 'N/A')
            season_number = episode_info.get('seasonNumber', 'N/A')
            episode_number = episode_info.get('episodeNumber', 'N/A')
            
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
            
            queue_info.append(f"{i}. {series_title} [队列ID: {queue_id}]")
            queue_info.append(f"   剧集: {episode_title} (S{season_number}E{episode_number})")
            queue_info.append(f"   状态: {status}, 剩余时间: {timeleft}")
            queue_info.append(f"   {size_info}")
            queue_info.append("")  # 空行分隔
        
        return "\n".join(queue_info)
    except Exception as e:
        return f"获取Sonarr队列时发生错误: {e}"

def get_all_series_logic() -> str:
    """获取所有电视剧列表的逻辑。"""
    try:
        series_list = sonarr_service.get_all_series()
        if not series_list:
            return "Sonarr电视剧库当前为空。"
        
        total_series = len(series_list)
        series_info = [f"Sonarr电视剧库中共有 {total_series} 部电视剧:"]
        
        for i, series in enumerate(series_list, 1):
            title = series.get('title', 'N/A')
            year = series.get('year', 'N/A')
            series_id = series.get('id', 'N/A')
            monitored = "已监控" if series.get('monitored', False) else "未监控"
            has_file = "已下载" if series.get('hasFile', False) else "未下载"
            season_count = len(series.get('seasons', []))
            series_info.append(f"{i}. {title} ({year}) - ID: {series_id} - {monitored} - {has_file} - 季度数: {season_count}")
        
        series_info.append("--- 电视剧列表结束 ---")
        return "\n".join(series_info)
    except Exception as e:
        return f"获取电视剧列表时发生错误: {e}"

def delete_series_logic(series_id: int) -> str:
    """删除电视剧的逻辑。"""
    try:
        # 首先获取电视剧信息以确认删除
        series_list = sonarr_service.get_all_series()
        if not series_list:
            return f"错误: 找不到ID为 {series_id} 的电视剧。"
        
        # 查找指定ID的电视剧
        target_series = None
        for series in series_list:
            if series.get('id') == series_id:
                target_series = series
                break
        
        if not target_series:
            return f"错误: 找不到ID为 {series_id} 的电视剧。"
        
        series_title = target_series.get('title', '未知电视剧')
        
        # 执行删除操作
        success = sonarr_service.delete_series(series_id)
        
        if success:
            return f"已成功删除电视剧 '{series_title}' (ID: {series_id})。"
        else:
            return f"删除电视剧 '{series_title}' (ID: {series_id}) 时发生错误。"
    except Exception as e:
        return f"删除电视剧时发生错误: {e}"

def get_sonarr_queue_item_details_logic(queue_id: int) -> str:
    """获取Sonarr队列项目详情的逻辑。"""
    try:
        queue_details = sonarr_service.get_queue_item_details(queue_id)
        if not queue_details:
            return f"错误: 找不到ID为 {queue_id} 的队列项目。"
        
        # 格式化详细信息
        details_info = [f"Sonarr队列项目详情 (ID: {queue_id}):"]
        
        # 基本信息
        series_info = queue_details.get('series', {})
        episode_info = queue_details.get('episode', {})
        
        series_title = series_info.get('title', 'N/A')
        episode_title = episode_info.get('title', 'N/A')
        season_number = episode_info.get('seasonNumber', 'N/A')
        episode_number = episode_info.get('episodeNumber', 'N/A')
        
        status = queue_details.get('status', 'N/A')
        timeleft = queue_details.get('timeleft', 'N/A')
        size = queue_details.get('size', 0)
        sizeleft = queue_details.get('sizeleft', 0)
        
        details_info.append(f"电视剧: {series_title}")
        details_info.append(f"剧集: {episode_title} (S{season_number}E{episode_number})")
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

def delete_sonarr_queue_item_logic(queue_id: int) -> str:
    """删除Sonarr队列项目的逻辑。"""
    try:
        # 尝试直接删除队列项目，不预先验证
        success = sonarr_service.delete_queue_item(queue_id)
        
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
