"""
通知服务
"""

import logging
import sys
import os
from typing import Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)
from config.settings import Settings

class NotificationService:
    """
    通知服务
    
    方法:
        - send_download_started(media_name: str) -> bool
        - send_download_completed(media_name: str, path: str) -> bool
        - send_error(error_message: str) -> bool
    """
    
    def __init__(self, log_level: str = 'INFO'):
        """
        初始化通知服务
        
        参数:
            - log_level: 日志级别，默认为 'INFO'
        """
        self.logger = logging.getLogger('NotificationService')
        self.logger.setLevel(log_level)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        # 可选：添加其他渠道，如 email 或 webhook
    
    def send_download_started(self, media_name: str) -> bool:
        """
        发送下载开始通知
        
        参数:
            - media_name: 媒体名称
        
        返回:
            - 布尔值表示是否成功
        """
        try:
            self.logger.info(f"下载开始: {media_name}")
            # 可选：发送推送
            return True
        except Exception:
            return False
    
    def send_download_completed(self, media_name: str, path: str) -> bool:
        """
        发送下载完成通知
        
        参数:
            - media_name: 媒体名称
            - path: 文件路径
        
        返回:
            - 布尔值表示是否成功
        """
        try:
            self.logger.info(f"下载完成: {media_name}，路径: {path}")
            # 可选：发送推送
            return True
        except Exception:
            return False
    
    def send_error(self, error_message: str) -> bool:
        """
        发送错误通知
        
        参数:
            - error_message: 错误消息
        
        返回:
            - 布尔值表示是否成功
        """
        try:
            self.logger.error(f"错误: {error_message}")
            # 可选：发送警报
            return True
        except Exception:
            return False

if __name__ == "__main__":
    """
    主方法，包含NotificationService类的测试用例
    """
    # 初始化配置（可选）
    settings = Settings()
    settings.load_from_env()
    
    # 创建NotificationService实例
    notifier = NotificationService(settings.log_level)
    
    # 测试用例1：发送下载开始通知
    print("测试用例1：发送下载开始通知")
    success = notifier.send_download_started("盗梦空间")
    print(f"通知状态：{'成功' if success else '失败'}")
    
    # 测试用例2：发送下载完成通知
    print("\n测试用例2：发送下载完成通知")
    success = notifier.send_download_completed("盗梦空间", "/movies/Inception.mkv")
    print(f"通知状态：{'成功' if success else '失败'}")
    
    # 测试用例3：发送错误通知
    print("\n测试用例3：发送错误通知")
    success = notifier.send_error("下载失败：网络错误")
    print(f"通知状态：{'成功' if success else '失败'}")
