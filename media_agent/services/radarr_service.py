"""
Radarr API服务
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

class RadarrService:
    """
    Radarr API服务
    
    方法:
        - __init__(host: str, api_key: str)
        - lookup_movie(term: str) -> List[Dict]
        - get_movie(movie_id: int) -> Dict
        - add_movie(movie_data: Dict) -> Dict
        - get_quality_profiles() -> List[Dict]
        - get_root_folders() -> List[Dict]
    """
    
    def __init__(self, host: str, api_key: str):
        """
        初始化Radarr服务
        
        参数:
            - host: Radarr主机地址，如 http://localhost:7878
            - api_key: Radarr API密钥
        """
        self.host = host.rstrip('/')
        self.api_key = api_key
        self.base_url = f"{self.host}/api/v3"
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
    def _make_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Any:
        """
        发起API请求
        
        参数:
            - endpoint: API端点
            - method: 请求方法，默认为GET
            - data: 请求数据
            
        返回:
            - API响应数据
            
        异常:
            - requests.exceptions.RequestException: 网络或API错误
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response.raise_for_status()
            
            # 对于DELETE请求，通常返回204 No Content，没有JSON内容
            if method == 'DELETE' or response.status_code == 204:
                return None
            
            # 对于其他请求，尝试解析JSON
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Radarr API request failed: {str(e)}")
    
    def get_queue(self) -> Dict:
        """
        获取Radarr的活动队列。
        """
        return self._make_request("queue")
    
    def get_queue_item_details(self, queue_id: int) -> Dict:
        """
        获取队列项目的详细信息
        
        参数:
            - queue_id: 队列项目ID
            
        返回:
            - 队列项目的详细信息
        """
        endpoint = f"queue/details/{queue_id}"
        return self._make_request(endpoint)
    
    def delete_queue_item(self, queue_id: int) -> bool:
        """
        删除队列中的特定项目
        
        参数:
            - queue_id: 队列项目ID
            
        返回:
            - 布尔值表示删除是否成功
        """
        try:
            endpoint = f"queue/{queue_id}"
            self._make_request(endpoint, method='DELETE')
            return True
        except Exception as e:
            logger.error(f"删除队列项目 {queue_id} 时出错: {e}")
            return False
    
    def lookup_movie(self, term: str) -> List[Dict]:
        """
        搜索电影
        
        参数:
            - term: 搜索关键词
            
        返回:
            - 电影搜索结果列表
        """
        endpoint = f"movie/lookup?term={term}"
        return self._make_request(endpoint)
    
    def get_movie(self, movie_id: int) -> Dict:
        """
        获取电影详情
        
        参数:
            - movie_id: 电影ID
            
        返回:
            - 电影详细信息
        """
        endpoint = f"movie/{movie_id}"
        return self._make_request(endpoint)
    
    def add_movie(self, movie_data: Dict) -> Dict:
        """
        添加电影到Radarr
        
        参数:
            - movie_data: 电影数据，包含title, tmdbId等
            
        返回:
            - 添加结果
        """
        title = movie_data.get('title')
        tmdb_id = movie_data.get('tmdbId')

        logger.info(f"正在向Radarr添加电影: {title} (TMDB ID: {tmdb_id})")
        
        # 确保根目录存在
        root_folder = self._get_root_folder()
        if not root_folder:
            return "错误: 无法获取Radarr的根目录路径。"

        # 动态获取第一个可用的质量配置文件ID
        quality_profile_id = self._get_first_quality_profile_id()
        if quality_profile_id is None:
            return "错误: 在Radarr中找不到任何质量配置文件。"

        # 使用查找到的电影信息来构建一个干净的请求体
        add_data = {
            'title': movie_data.get('title'),
            'tmdbId': movie_data.get('tmdbId'),
            'year': movie_data.get('year'),
            'qualityProfileId': quality_profile_id,
            'titleSlug': movie_data.get('titleSlug'),
            'images': movie_data.get('images'),
            'rootFolderPath': root_folder,
            'monitored': True,
            'addOptions': {
                'monitor': 'movieOnly',
                'searchForMovie': True
            }
        }
        
        logger.info(f"发送到Radarr的请求体: {add_data}")
        response = self._make_request('movie', 'POST', data=add_data)
        
        return response
    
    def get_quality_profiles(self) -> List[Dict]:
        """
        获取质量配置文件列表
        
        返回:
            - 质量配置文件列表
        """
        endpoint = "qualityprofile"
        return self._make_request(endpoint)
    
    def get_language_profiles(self) -> List[Dict]:
        """
        获取语言配置文件列表
        
        返回:
            - 语言配置文件列表
        """
        endpoint = "languageprofile"
        return self._make_request(endpoint)
    
    def get_root_folders(self) -> List[Dict]:
        """
        获取根文件夹列表
        
        返回:
            - 根文件夹列表
        """
        endpoint = "rootfolder"
        return self._make_request(endpoint)
    
    def _get_root_folder(self) -> str:
        """获取第一个可用的根目录路径。"""
        folders = self.get_root_folders()
        if folders and len(folders) > 0:
            return folders[0]['path']
        logger.error("在Radarr中未找到任何根目录。")
        return None

    def _get_first_quality_profile_id(self) -> int:
        """获取第一个可用的质量配置文件ID。"""
        profiles = self.get_quality_profiles()
        if profiles and len(profiles) > 0:
            return profiles[0]['id']
        logger.error("在Radarr中未找到任何质量配置文件。")
        return None
    
    def _get_first_language_profile_id(self) -> int:
        """获取第一个可用的语言配置文件ID。"""
        profiles = self.get_language_profiles()
        if profiles and len(profiles) > 0:
            return profiles[0]['id']
        logger.error("在Radarr中未找到任何语言配置文件。")
        return None
    
    def get_all_movies(self) -> List[Dict]:
        """
        获取所有电影列表
        
        返回:
            - 所有电影的详细信息列表
        """
        endpoint = "movie"
        return self._make_request(endpoint)
    
    def delete_movie(self, movie_id: int) -> bool:
        """
        删除电影
        
        参数:
            - movie_id: 电影ID
            
        返回:
            - 布尔值表示删除是否成功
        """
        try:
            endpoint = f"movie/{movie_id}"
            self._make_request(endpoint, method='DELETE')
            return True
        except Exception as e:
            logger.error(f"删除电影 {movie_id} 时出错: {e}")
            return False
    
    def check_health(self) -> bool:
        """
        检查Radarr服务健康状态
        
        返回:
            - 布尔值表示服务是否健康
        """
        try:
            endpoint = "health"
            self._make_request(endpoint)
            return True
        except Exception:
            return False
