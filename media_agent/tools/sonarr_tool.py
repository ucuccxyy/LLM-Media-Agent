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
        if not queue or not queue.get('records'):
            return "Sonarr下载队列当前为空。"
        
        total_items = len(queue['records'])
        queue_info = [f"当前Sonarr下载队列中有 {total_items} 个项目:"]
        for i, item in enumerate(queue['records']):
            title = item.get('series', {}).get('title', 'N/A')
            status = item.get('status', 'N/A')
            timeleft = item.get('timeleft', 'N/A')
            queue_info.append(f"{i+1}. 剧集: {title}, 状态: {status}, 剩余时间: {timeleft}")

        queue_info.append("--- 队列列表结束 ---")
        return "\n".join(queue_info)
    except Exception as e:
        return f"获取Sonarr队列时发生错误: {e}"
