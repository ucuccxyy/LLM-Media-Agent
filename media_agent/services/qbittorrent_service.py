"""
qBittorrent API服务
"""

import requests
from typing import List, Dict, Any
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)
from config.settings import Settings

class QBittorrentService:
    """
    qBittorrent API服务
    
    方法:
        - __init__(host: str, username: str, password: str)
        - login() -> bool
        - get_torrents(filter: str = None) -> List[Dict]
        - get_torrent_properties(hash: str) -> Dict
        - pause(hash: str) -> bool
        - resume(hash: str) -> bool
    """
    
    def __init__(self, host: str, username: str, password: str):
        """
        初始化qBittorrent服务
        
        参数:
            - host: qBittorrent主机地址，如 http://localhost:8080
            - username: 用户名
            - password: 密码
        """
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.base_url = f"{self.host}/api/v2"
        self.cookies = None  # 用于存储登录 cookie
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    def login(self) -> bool:
        """
        登录qBittorrent
        
        返回:
            - 布尔值表示登录是否成功
        """
        endpoint = "auth/login"
        data = {
            "username": self.username,
            "password": self.password
        }
        try:
            response = requests.post(f"{self.base_url}/{endpoint}", data=data, headers=self.headers, timeout=10)
            response.raise_for_status()
            if 'SID' in response.cookies:
                self.cookies = response.cookies
                return True
            return False
        except requests.exceptions.RequestException:
            return False
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: Dict = None, params: Dict = None, return_json: bool = True) -> Any:
        """
        发起API请求（需要已登录）
        
        参数:
            - endpoint: API端点
            - method: 请求方法，默认为GET
            - data: POST数据
            - params: 查询参数
            - return_json: 是否解析为JSON，默认为True
            
        返回:
            - API响应数据（JSON或文本）
        """
        if not self.cookies:
            if not self.login():
                raise Exception("qBittorrent login failed")
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == 'GET':
                response = requests.get(url, cookies=self.cookies, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, cookies=self.cookies, data=data, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            response.raise_for_status()
            if return_json:
                return response.json() if response.text else {}
            else:
                return response.text.strip()  # 返回纯文本
        except requests.exceptions.RequestException as e:
            raise Exception(f"qBittorrent API request failed: {str(e)}")
    
    def get_torrents(self, filter: str = None) -> List[Dict]:
        """
        获取种子列表
        
        参数:
            - filter: 过滤器（如 'downloading'）
            
        返回:
            - 种子列表
        """
        endpoint = "torrents/info"
        params = {'filter': filter} if filter else None
        return self._make_request(endpoint, params=params)
    
    def get_torrent_properties(self, hash: str) -> Dict:
        """
        获取种子属性
        
        参数:
            - hash: 种子哈希
            
        返回:
            - 种子属性字典
        """
        endpoint = "torrents/properties"
        params = {'hash': hash}
        return self._make_request(endpoint, params=params)
    
    def pause(self, hash: str) -> bool:
        """
        暂停种子
        
        参数:
            - hash: 种子哈希
            
        返回:
            - 布尔值表示是否成功
        """
        endpoint = "torrents/pause"
        data = {'hashes': hash}
        try:
            self._make_request(endpoint, method='POST', data=data)
            return True
        except Exception:
            return False
    
    def resume(self, hash: str) -> bool:
        """
        恢复种子
        
        参数:
            - hash: 种子哈希
            
        返回:
            - 布尔值表示是否成功
        """
        endpoint = "torrents/resume"
        data = {'hashes': hash}
        try:
            self._make_request(endpoint, method='POST', data=data)
            return True
        except Exception:
            return False
    
    def check_health(self) -> bool:
        """
        检查qBittorrent服务健康状态（通过版本检查）
        
        返回:
            - 布尔值表示服务是否健康
        """
        try:
            endpoint = "app/version"
            response = self._make_request(endpoint, return_json=False)  # 添加参数避免 JSON 解析
            if response:
                print("Health check 成功，版本:", response)  # 添加调试
                return True
            return False
        except Exception as e:
            print("Health check 失败，错误详情:", str(e))  # 添加调试
            return False

if __name__ == "__main__":
    """
    主方法，包含QBittorrentService类的测试用例
    """
    # 初始化配置
    settings = Settings()
    settings.load_from_env()
    
    # 创建QBittorrentService实例
    qb = QBittorrentService(settings.qbittorrent_host, settings.qbittorrent_username, settings.qbittorrent_password)
    
    # 测试用例1：登录
    print("测试用例1：登录qBittorrent")
    login_success = qb.login()
    print(f"登录状态：{'成功' if login_success else '失败'}")
    
    # 测试用例2：获取种子列表
    if login_success:
        print("\n测试用例2：获取种子列表")
        try:
            torrents = qb.get_torrents()
            if torrents:
                print(f"找到 {len(torrents)} 个种子：")
                for torrent in torrents[:3]:  # 仅显示前3个
                    print(f"- {torrent.get('name', '未知名称')} (状态: {torrent.get('state', '未知')})")
            else:
                print("未找到种子")
        except Exception as e:
            print(f"获取种子列表时出错：{e}")
    
    # 测试用例3：检查健康状态
    print("\n测试用例3：检查qBittorrent服务健康状态")
    health_status = qb.check_health()
    print(f"qBittorrent服务健康状态：{'健康' if health_status else '不健康'}")
