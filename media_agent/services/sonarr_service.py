"""
Sonarr API服务
"""

import requests
import logging
from typing import List, Dict, Any
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)
from config.settings import Settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SonarrService:
    """
    Sonarr API服务
    """
    
    def __init__(self, host: str, api_key: str):
        self.host = host.rstrip('/')
        self.api_key = api_key
        self.base_url = f"{self.host}/api/v3"
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
    def _make_request(self, endpoint: str, method: str = 'GET', json: Dict = None, params: Dict = None) -> Any:
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=json, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response.raise_for_status()
            # 对于返回空内容的成功响应，例如204 No Content，requests.json()会失败
            if response.status_code == 204:
                return None
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Sonarr API请求失败: {e}, URL: {url}, 方法: {method}")
            # 返回响应文本以便调试
            if e.response is not None:
                 logger.error(f"Sonarr响应: {e.response.text}")
            return None
        except ValueError as e:
            logger.error(f"Sonarr请求中不支持的方法: {e}")
            return None

    def get_queue(self) -> Dict:
        """
        获取Sonarr的活动队列。
        """
        return self._make_request("queue")

    def lookup_series(self, term: str) -> List[Dict]:
        return self._make_request("series/lookup", params={"term": term})
    
    def get_series_by_tvdb_id(self, tvdb_id: int) -> List[Dict]:
        return self._make_request("series", params={"tvdbId": tvdb_id})
    
    def add_series(self, tvdb_id: int, seasons: List[int]) -> Dict:
        """将一个电视剧按其TVDB ID添加到Sonarr，并为指定的季度开始下载。"""
        logger.info(f"正在向Sonarr添加电视剧: TVDB ID {tvdb_id}, 季度: {seasons}")

        root_folder = self._get_root_folder()
        if not root_folder:
            logger.error("在add_series中无法获取Sonarr的根目录路径。")
            return {"status": "error", "message": "无法获取Sonarr的根目录路径。"}

        series_lookup = self.lookup_series(f"tvdb:{tvdb_id}")
        if not series_lookup:
            logger.error(f"无法通过TVDB ID {tvdb_id} 找到电视剧信息。")
            return {"status": "error", "message": f"无法通过TVDB ID {tvdb_id} 找到电视剧信息。"}
        series_info = series_lookup[0]

        quality_profile_id = self._get_default_quality_profile_id()
        if quality_profile_id is None:
            logger.error("在add_series中找不到默认的质量配置文件ID。")
            return {"status": "error", "message": "找不到默认的质量配置文件ID。"}

        # 动态获取第一个可用的语言配置文件ID
        language_profile_id = self._get_first_language_profile_id()
        if language_profile_id is None:
            logger.error("在add_series中找不到默认的语言配置文件ID。")
            return {"status": "error", "message": "找不到默认的语言配置文件ID。"}

        # 使用查找到的剧集信息作为我们请求的基础
        series_data = series_info
        
        # 分配我们的本地配置
        series_data['rootFolderPath'] = root_folder
        series_data['qualityProfileId'] = quality_profile_id
        series_data['languageProfileId'] = language_profile_id
        series_data['monitored'] = True
        series_data['seasonFolder'] = True  # 为每个季度创建单独的文件夹
        series_data['tags'] = []  # 空标签列表，用户可以后续添加

        # 根据用户请求，明确设置每个季度的监控状态
        all_seasons = series_data.get('seasons', [])

        if seasons == 'all':
            # 如果用户要求下载所有季度，则监控所有存在的季度
            seasons_to_monitor = {s.get('seasonNumber') for s in all_seasons}
        else:
            seasons_to_monitor = set(seasons)

        for season in all_seasons:
            season_number = season.get('seasonNumber')
            # 明确地只监控用户指定的季度
            if season_number in seasons_to_monitor:
                season['monitored'] = True
            else:
                season['monitored'] = False
        series_data['seasons'] = all_seasons

        # 设置添加选项以搜索被监控的季度的剧集
        series_data['addOptions'] = {
            'monitor': 'missing',
                'searchForMissingEpisodes': True
        }
        
        logger.info(f"发送到Sonarr的请求体: {series_data}")
        response_json = self._make_request('series', 'POST', json=series_data)
        
        # 检查响应是否有效，以及是否是一个表示成功的字典（包含 'id'）
        if response_json and isinstance(response_json, dict) and 'id' in response_json:
            logger.info(f"成功将电视剧添加到Sonarr. 响应: {response_json}")
            return response_json  # 返回完整的字典
        else:
            # 记录详细的错误信息
            error_details = str(response_json) if response_json else "无响应"
            error_message = f"将电视剧添加到Sonarr时发生错误。响应: {error_details}"
            logger.error(error_message)
            # 对于已存在的电视剧，Sonarr可能会返回一个包含错误信息的列表
            if isinstance(response_json, list) and response_json:
                if 'already exists' in response_json[0].get('errorMessage', '').lower():
                    # 返回一个可识别的字典来表示“已存在”
                    return {"status": "exists", "message": response_json[0]['errorMessage']}
            return None # 在其他所有失败情况下返回 None

    def _get_root_folder(self) -> str:
        """获取第一个可用的根目录路径。"""
        folders = self._make_request("rootfolder")
        if folders and len(folders) > 0:
            return folders[0]['path']
        logger.error("在Sonarr中未找到任何根目录。")
        return None

    def _get_default_quality_profile_id(self) -> int:
        """获取默认的质量配置文件ID。"""
        profiles = self._make_request("qualityprofile")
        if profiles:
            # Sonarr通常将 'Any' 或 'Standard' 作为第一个配置文件，可以作为默认
            return profiles[0]['id']
        logger.error("在Sonarr中未找到任何质量配置文件。")
        return None

    def _get_first_language_profile_id(self) -> int:
        """获取第一个可用的语言配置文件ID。"""
        profiles = self._make_request("languageprofile")
        if profiles:
            # Sonarr通常将 'Any' 或 'Standard' 作为第一个配置文件，可以作为默认
            return profiles[0]['id']
        logger.error("在Sonarr中未找到任何语言配置文件。")
        return None

if __name__ == "__main__":
    settings = Settings()
    settings.load_from_env()
    sonarr = SonarrService(settings.sonarr_host, settings.sonarr_api_key)
    
    # 测试添加电视剧
    # 请用一个实际存在但你的库里没有的电视剧的TVDB ID替换
    test_tvdb_id = 247808  # 'The Simpsons'
    test_seasons = [1, 2]
    print(f"\n测试添加电视剧: TVDB ID {test_tvdb_id}")
    result = sonarr.add_series(test_tvdb_id, test_seasons)
    print(result)
    
    # 测试搜索电视剧
    print("\n测试搜索电视剧: 'Game of Thrones'")
    search_results = sonarr.lookup_series("Game of Thrones")
    if search_results:
        print("搜索成功，找到以下结果:")
        for series in search_results[:3]:
            print(f"  - {series['title']} ({series['year']})")
    else:
        print("搜索失败或未找到结果。")