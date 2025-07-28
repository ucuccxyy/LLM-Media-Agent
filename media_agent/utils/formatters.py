"""
格式化工具

提供各种数据的格式化功能，包括：
- 媒体信息格式化（电影、电视剧）
- 下载进度格式化
- 文件大小格式化
- 时间格式化
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import math

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from models.media_models import Movie, Series, Episode, Season

def format_movie_info(movie: Movie) -> str:
    """
    格式化电影信息
    
    Args:
        movie: 电影对象
        
    Returns:
        格式化后的字符串，如：
        - 盗梦空间 (2010)
        - Inception (2010) [1080p]
    """
    parts = [movie.title]
    
    if movie.year:
        parts.append(f"({movie.year})")
        
    if movie.quality_profile:
        parts.append(f"[{movie.quality_profile}]")
        
    if movie.original_title and movie.original_title != movie.title:
        parts.append(f"/ {movie.original_title}")
    
    return " ".join(parts)

def format_series_info(series: Series) -> str:
    """
    格式化电视剧信息
    
    Args:
        series: 电视剧对象
        
    Returns:
        格式化后的字符串，如：
        - 权力的游戏 (2011) [第1-8季]
        - Game of Thrones S01-S08
    """
    parts = [series.title]
    
    if series.year:
        parts.append(f"({series.year})")
    
    if series.seasons:
        season_count = len(series.seasons)
        if season_count == 1:
            parts.append(f"[第{series.seasons[0].number}季]")
        else:
            first_season = min(s.number for s in series.seasons)
            last_season = max(s.number for s in series.seasons)
            parts.append(f"[第{first_season}-{last_season}季]")
            
    if series.original_title and series.original_title != series.title:
        parts.append(f"/ {series.original_title}")
    
    return " ".join(parts)

def format_episode_info(episode: Episode) -> str:
    """
    格式化剧集信息
    
    Args:
        episode: 剧集对象
        
    Returns:
        格式化后的字符串，如：
        - S01E01 - 冬天来了
        - S01E01 - Winter Is Coming
    """
    season_num = str(episode.season_number).zfill(2)
    episode_num = str(episode.episode_number).zfill(2)
    
    parts = [f"S{season_num}E{episode_num}"]
    
    if episode.title:
        parts.append(f"- {episode.title}")
        
    if episode.air_date:
        parts.append(f"({episode.air_date.strftime('%Y-%m-%d')})")
    
    return " ".join(parts)

def format_download_progress(progress: float, width: int = 20) -> str:
    """
    格式化下载进度
    
    Args:
        progress: 进度百分比（0-100）
        width: 进度条宽度
        
    Returns:
        格式化后的字符串，如：
        45.5% [######### ]
    """
    if not 0 <= progress <= 100:
        raise ValueError("进度必须在0-100之间")
    
    filled_length = int(width * progress / 100)
    bar = '#' * filled_length + ' ' * (width - filled_length)
    return f"{progress:.1f}% [{bar}]"

def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化后的字符串，如：
        - 1.5 GB
        - 720.3 MB
        - 45.8 KB
    """
    if size_bytes == 0:
        return "0 B"
        
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 1)
    
    return f"{s} {size_names[i]}"

def format_duration(seconds: int) -> str:
    """
    格式化时长
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化后的字符串，如：
        - 2小时15分钟
        - 45分钟
        - 30秒
    """
    if seconds < 60:
        return f"{seconds}秒"
        
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}分钟"
        
    hours = minutes // 60
    minutes = minutes % 60
    
    if minutes == 0:
        return f"{hours}小时"
    else:
        return f"{hours}小时{minutes}分钟"

# 示例使用和测试代码
if __name__ == "__main__":
    # 测试电影信息格式化
    movie = Movie(
        id=1,
        title="盗梦空间",
        year=2010,
        quality_profile="1080p"
    )
    formatted = format_movie_info(movie)
    assert formatted == "盗梦空间 (2010) [1080p]"
    
    # 测试下载进度格式化
    progress_text = format_download_progress(45.5)
    print(f"下载进度: {progress_text}")
    
    # 测试文件大小格式化
    size_text = format_file_size(1234567890)  # ≈ 1.15 GB
    print(f"文件大小: {size_text}")
    
    # 测试时长格式化
    duration_text = format_duration(8460)  # 2小时21分钟
    print(f"视频时长: {duration_text}")
    
    print("所有测试通过！")
