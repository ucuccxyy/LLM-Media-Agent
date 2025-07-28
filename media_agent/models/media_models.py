"""
媒体数据模型

这个模块定义了系统中使用的所有媒体相关的数据模型，包括：
- Movie: 电影模型
- Series: 电视剧模型
- Season: 季模型
- Episode: 集模型

所有模型都使用Pydantic进行数据验证和序列化。
"""

from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class MediaType(Enum):
    """媒体类型枚举"""
    MOVIE = "movie"
    TV = "tv_show"

class MediaStatus(Enum):
    """媒体状态枚举"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"

class Season(BaseModel):
    """季模型"""
    number: int = Field(..., description="季号")
    episode_count: int = Field(..., description="集数")
    monitored: bool = Field(default=True, description="是否监控")
    
    @field_validator('number')
    @classmethod
    def validate_season_number(cls, v: Any) -> int:
        if v < 0:
            raise ValueError("季号不能为负数")
        return v
    
    @field_validator('episode_count')
    @classmethod
    def validate_episode_count(cls, v: Any) -> int:
        if v < 0:
            raise ValueError("集数不能为负数")
        return v

class Episode(BaseModel):
    """集模型"""
    id: int
    season_number: int = Field(..., description="季号")
    episode_number: int = Field(..., description="集号")
    title: str = Field(..., description="标题")
    air_date: Optional[datetime] = Field(None, description="播出日期")
    has_file: bool = Field(default=False, description="是否已下载")
    
    @field_validator('season_number', 'episode_number')
    @classmethod
    def validate_numbers(cls, v: Any) -> int:
        if v < 0:
            raise ValueError("季号和集号不能为负数")
        return v

class Movie(BaseModel):
    """电影模型"""
    id: int
    title: str = Field(..., description="电影标题")
    original_title: Optional[str] = Field(None, description="原始标题")
    year: Optional[int] = Field(None, description="发行年份")
    imdb_id: Optional[str] = Field(None, description="IMDB ID")
    tmdb_id: Optional[int] = Field(None, description="TMDB ID")
    quality_profile: str = Field(..., description="画质配置")
    path: Optional[str] = Field(None, description="存储路径")
    status: MediaStatus = Field(default=MediaStatus.PENDING, description="状态")
    
    @field_validator('year')
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            current_year = datetime.now().year
            if v < 1888 or v > current_year + 1:  # 1888年是第一部电影诞生的年份
                raise ValueError(f"年份必须在1888和{current_year + 1}之间")
        return v
    
    @field_validator('quality_profile')
    @classmethod
    def validate_quality(cls, v: str) -> str:
        valid_qualities = {'1080p', '720p', '2160p', '4K', 'SD'}
        if v not in valid_qualities:
            raise ValueError(f"无效的画质配置。支持的值: {', '.join(valid_qualities)}")
        return v

class Series(BaseModel):
    """电视剧模型"""
    id: int
    title: str = Field(..., description="剧集标题")
    original_title: Optional[str] = Field(None, description="原始标题")
    year: Optional[int] = Field(None, description="首播年份")
    tvdb_id: Optional[int] = Field(None, description="TVDB ID")
    seasons: List[Season] = Field(default_factory=list, description="季信息")
    path: Optional[str] = Field(None, description="存储路径")
    status: MediaStatus = Field(default=MediaStatus.PENDING, description="状态")
    
    @field_validator('year')
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            current_year = datetime.now().year
            if v < 1936 or v > current_year + 1:  # 1936年是第一部电视剧播出的年份
                raise ValueError(f"年份必须在1936和{current_year + 1}之间")
        return v

# 示例使用和测试代码
if __name__ == "__main__":
    # 创建电影实例
    movie = Movie(
        id=1,
        title="盗梦空间",
        year=2010,
        quality_profile="1080p"
    )
    print(f"电影标题: {movie.title}")
    print(f"电影年份: {movie.year}")
    print(f"JSON格式: {movie.model_dump_json(indent=2)}")
    
    # 创建电视剧实例
    series = Series(
        id=1,
        title="权力的游戏",
        year=2011,
        seasons=[
            Season(number=1, episode_count=10),
            Season(number=2, episode_count=10)
        ]
    )
    print(f"\n剧集标题: {series.title}")
    print(f"季数: {len(series.seasons)}")
    print(f"JSON格式: {series.model_dump_json(indent=2)}")