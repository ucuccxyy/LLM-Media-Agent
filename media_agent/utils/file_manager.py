"""
文件管理工具

负责管理媒体文件的存储、移动和清理：
- 创建和维护目录结构
- 移动下载完成的文件到适当位置
- 检查存储空间
- 清理临时文件
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import psutil

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.settings import Settings

class FileManager:
    """文件管理器"""
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        初始化文件管理器
        
        Args:
            settings: 配置对象，如果为None则创建新实例
        """
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)
        
        # 定义关键目录
        self.root_dir = Path(self.settings.root_path)
        self.download_dir = self.root_dir / "downloads"
        self.incomplete_dir = self.download_dir / "incomplete"
        self.movies_dir = self.root_dir / "movies"
        self.tv_shows_dir = self.root_dir / "tv_shows"
        self.temp_dir = self.root_dir / "temp"
        
        # 定义允许的文件类型
        self.video_extensions = {'.mp4', '.mkv', '.avi', '.m4v', '.mov', '.wmv'}
        
        # 最小可用空间（GB）
        self.min_free_space = 10
    
    def ensure_directories(self) -> None:
        """
        确保所有必要的目录存在
        如果目录不存在则创建
        """
        directories = [
            self.download_dir,
            self.incomplete_dir,
            self.movies_dir,
            self.tv_shows_dir,
            self.temp_dir
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                # 设置目录权限为755（rwxr-xr-x）
                directory.chmod(0o755)
            except Exception as e:
                self.logger.error(f"创建目录 {directory} 失败: {e}")
                raise
    
    def move_completed_download(self, source: Path, media_type: str) -> Path:
        """
        移动完成的下载文件到适当的位置
        
        Args:
            source: 源文件路径
            media_type: 媒体类型（"movie" 或 "tv_show"）
            
        Returns:
            目标文件路径
            
        Raises:
            ValueError: 如果媒体类型无效或文件不存在
            OSError: 如果移动操作失败
        """
        if not source.exists():
            raise ValueError(f"源文件不存在: {source}")
            
        if media_type not in ("movie", "tv_show"):
            raise ValueError(f"无效的媒体类型: {media_type}")
            
        # 检查文件类型
        if source.suffix.lower() not in self.video_extensions:
            raise ValueError(f"不支持的文件类型: {source.suffix}")
            
        # 检查目标目录空间
        if not self._check_free_space(source.stat().st_size):
            raise OSError("目标目录空间不足")
        
        # 确定目标目录和文件名
        if media_type == "movie":
            dest_dir = self.movies_dir
        else:
            dest_dir = self.tv_shows_dir
            
        dest_file = dest_dir / source.name
        
        # 如果目标文件已存在，添加时间戳
        if dest_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_file = dest_dir / f"{source.stem}_{timestamp}{source.suffix}"
        
        try:
            # 使用shutil.move确保原子性操作
            shutil.move(str(source), str(dest_file))
            # 设置文件权限为644（rw-r--r--）
            dest_file.chmod(0o644)
            return dest_file
        except Exception as e:
            self.logger.error(f"移动文件失败: {e}")
            raise
    
    def clean_temp_files(self, max_age_days: int = 7) -> None:
        """
        清理临时文件
        
        Args:
            max_age_days: 文件保留的最大天数
        """
        now = datetime.now()
        cutoff = now - timedelta(days=max_age_days)
        
        try:
            for item in self.temp_dir.glob("**/*"):
                if item.is_file():
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if mtime < cutoff:
                        item.unlink()
            
            # 清理空目录
            for item in self.temp_dir.glob("**/*"):
                if item.is_dir() and not any(item.iterdir()):
                    item.rmdir()
        except Exception as e:
            self.logger.error(f"清理临时文件失败: {e}")
            raise
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        获取存储空间信息
        
        Returns:
            包含存储信息的字典：
            - total_space: 总空间（GB）
            - used_space: 已用空间（GB）
            - free_space: 可用空间（GB）
            - usage_percent: 使用百分比
        """
        try:
            usage = psutil.disk_usage(str(self.root_dir))
            return {
                "total_space": usage.total / (1024**3),
                "used_space": usage.used / (1024**3),
                "free_space": usage.free / (1024**3),
                "usage_percent": usage.percent
            }
        except Exception as e:
            self.logger.error(f"获取存储信息失败: {e}")
            raise
    
    def _check_free_space(self, required_bytes: int) -> bool:
        """
        检查是否有足够的可用空间
        
        Args:
            required_bytes: 需要的空间（字节）
            
        Returns:
            是否有足够空间
        """
        try:
            free_space = psutil.disk_usage(str(self.root_dir)).free
            # 确保至少保留最小可用空间
            return free_space - required_bytes > self.min_free_space * (1024**3)
        except Exception:
            # 如果无法检查空间，返回False以确保安全
            return False

# 测试代码
if __name__ == "__main__":
    import tempfile
    
    # 创建临时测试目录
    with tempfile.TemporaryDirectory() as temp_root:
        # 创建测试设置
        class TestSettings:
            root_path = temp_root
        
        # 创建文件管理器实例
        fm = FileManager(TestSettings())
        
        # 测试目录创建
        fm.ensure_directories()
        assert Path(temp_root).exists()
        assert (Path(temp_root) / "movies").exists()
        assert (Path(temp_root) / "tv_shows").exists()
        
        # 测试文件移动
        test_file = Path(temp_root) / "downloads" / "test_movie.mp4"
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("test content")
        
        dest_file = fm.move_completed_download(test_file, "movie")
        assert dest_file.exists()
        assert not test_file.exists()  # 确保源文件已移动
        
        # 测试存储信息获取
        storage_info = fm.get_storage_info()
        assert "total_space" in storage_info
        assert "free_space" in storage_info
        
        print("所有测试通过！")
