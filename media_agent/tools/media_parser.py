"""
媒体信息解析工具
"""

import re
from typing import Dict, Optional, TypedDict
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)
from utils.validators import validate_quality, validate_series_format  # 假设 validators.py 有这些函数

class MovieInfo(TypedDict):
    title: str
    year: Optional[int]
    quality: Optional[str]

class SeriesInfo(TypedDict):
    title: str
    season: Optional[int]
    episode: Optional[int]
    quality: Optional[str]

class MediaParser:
    """
    媒体信息解析器
    
    方法:
        - parse_movie_title(title: str) -> MovieInfo
        - parse_series_title(title: str) -> SeriesInfo
        - extract_quality(text: str) -> str
        - extract_year(text: str) -> Optional[int]
    """
    
    def parse_movie_title(self, title: str) -> MovieInfo:
        """
        解析电影标题
        
        参数:
            - title: 标题字符串
        
        返回:
            - MovieInfo 字典
        """
        # 改进正则：贪婪匹配标题直到年份，支持中文和点分隔
        match = re.match(r'^(?P<title>.*?)\.*(?P<year>\d{4})?\.*(?P<quality>1080p|720p|4K|BluRay|HDRip)?(?:\.|$)', title, re.IGNORECASE | re.UNICODE)
        if match:
            info = match.groupdict()
            info['title'] = info['title'].strip().replace('.', ' ')  # 处理点分隔并转换为空格
            info['year'] = int(info['year']) if info['year'] else None
            info['quality'] = info['quality'] if info['quality'] and validate_quality(info['quality']) else self.extract_quality(title)
            return MovieInfo(title=info['title'], year=info['year'], quality=info['quality'])
        # 默认返回，使用提取方法作为后备
        return MovieInfo(title=title, year=self.extract_year(title), quality=self.extract_quality(title))
    
    def parse_series_title(self, title: str) -> SeriesInfo:
        """
        解析电视剧标题
        
        参数:
            - title: 标题字符串
        
        返回:
            - SeriesInfo 字典
        """
        # 改进正则：贪婪匹配标题直到 SxxExx，支持点分隔和无空格
        match = re.match(r'^(?P<title>.*?)\.*S(?P<season>\d+)E(?P<episode>\d+)\.*(?P<quality>1080p|720p|4K|BluRay|HDRip)?(?:\.|$)', title, re.IGNORECASE | re.UNICODE)
        if match:
            info = match.groupdict()
            info['title'] = info['title'].strip().replace('.', ' ')  # 处理点分隔
            info['season'] = int(info['season']) if info['season'] else None
            info['episode'] = int(info['episode']) if info['episode'] else None
            info['quality'] = info['quality'] if info['quality'] and validate_quality(info['quality']) else self.extract_quality(title)
            if info['season'] is not None and info['episode'] is not None and validate_series_format(f"S{info['season']}E{info['episode']}"):
                return SeriesInfo(title=info['title'], season=info['season'], episode=info['episode'], quality=info['quality'])
        # 默认返回，使用提取方法作为后备
        return SeriesInfo(title=title, season=None, episode=None, quality=self.extract_quality(title))
    
    def extract_quality(self, text: str) -> Optional[str]:
        """
        从文本提取质量
        
        参数:
            - text: 文本字符串
        
        返回:
            - 质量字符串或 None
        """
        match = re.search(r'(1080p|720p|4K|BluRay|HDRip)', text, re.IGNORECASE)
        return match.group(0) if match else None
    
    def extract_year(self, text: str) -> Optional[int]:
        """
        从文本提取年份
        
        参数:
            - text: 文本字符串
        
        返回:
            - 年份整数或 None
        """
        match = re.search(r'\b(19|20)\d{2}\b', text)
        return int(match.group(0)) if match else None

if __name__ == "__main__":
    """
    主方法，包含MediaParser类的测试用例
    """
    parser = MediaParser()
    
    # 测试用例1：解析电影标题
    print("测试用例1：解析电影标题")
    movie_info = parser.parse_movie_title("盗梦空间.2010.1080p.BluRay")
    print("解析结果:", movie_info)
    
    # 测试用例2：解析电视剧标题
    print("\n测试用例2：解析电视剧标题")
    series_info = parser.parse_series_title("Breaking.Bad.S01E01.1080p")
    print("解析结果:", series_info)
    
    # 测试用例3：提取质量和年份
    print("\n测试用例3：提取质量和年份")
    quality = parser.extract_quality("Inception.2010.1080p.BluRay")
    year = parser.extract_year("Inception.2010.1080p.BluRay")
    print(f"质量: {quality}, 年份: {year}")
