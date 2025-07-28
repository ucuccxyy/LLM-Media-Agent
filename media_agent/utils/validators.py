"""
数据验证工具

包含以下验证函数：
- validate_movie_title: 验证电影标题格式
- validate_series_format: 验证电视剧集格式（如S01E01）
- validate_quality: 验证视频质量标识
- validate_year: 验证年份
- validate_file_name: 验证文件名
"""

import re
from typing import Optional, Tuple
from datetime import datetime

def validate_movie_title(title: str) -> Tuple[bool, str]:
    """
    验证电影标题格式
    支持格式：
    - 盗梦空间 (2010)
    - Inception (2010)
    - 盗梦空间.2010.1080p
    - Inception.2010.1080p
    
    Args:
        title: 电影标题
    
    Returns:
        (bool, str): (是否有效, 错误信息)
    """
    if not title or len(title.strip()) == 0:
        return False, "标题不能为空"
        
    # 移除常见的分隔符
    clean_title = re.sub(r'[._\s]+', ' ', title).strip()
    
    # 基本格式检查
    if len(clean_title) < 2:
        return False, "标题太短"
        
    if len(clean_title) > 200:
        return False, "标题太长"
    
    # 检查特殊字符
    if re.search(r'[<>:"|?*]', clean_title):
        return False, "标题包含非法字符"
    
    return True, ""

def validate_series_format(text: str) -> Tuple[bool, str]:
    """
    验证电视剧集格式
    支持格式：
    - S01E01
    - S1E1
    - 1x01
    - E01
    
    Args:
        text: 剧集标识
    
    Returns:
        (bool, str): (是否有效, 错误信息)
    """
    # 标准格式 S01E01
    if re.match(r'^S\d{1,2}E\d{1,2}$', text, re.IGNORECASE):
        season = int(re.search(r'S(\d{1,2})', text, re.IGNORECASE).group(1))
        episode = int(re.search(r'E(\d{1,2})', text, re.IGNORECASE).group(1))
    # 1x01 格式
    elif re.match(r'^\d{1,2}x\d{1,2}$', text, re.IGNORECASE):
        season = int(text.split('x')[0])
        episode = int(text.split('x')[1])
    # 单集格式 E01
    elif re.match(r'^E\d{1,2}$', text, re.IGNORECASE):
        season = 1
        episode = int(text[1:])
    else:
        return False, "无效的剧集格式"
    
    # 验证季号和集号范围
    if season < 1 or season > 100:
        return False, "无效的季号（应在1-100之间）"
    if episode < 1 or episode > 300:
        return False, "无效的集号（应在1-300之间）"
    
    return True, ""

def validate_quality(quality: str) -> Tuple[bool, str]:
    """
    验证视频质量标识
    支持格式：
    - 480p, 720p, 1080p, 2160p
    - SD, HD, FHD, UHD
    - 4K, 8K
    
    Args:
        quality: 质量标识
    
    Returns:
        (bool, str): (是否有效, 错误信息)
    """
    valid_qualities = {
        # 常规分辨率
        '480p', '720p', '1080p', '2160p',
        # 通用标识
        'SD', 'HD', 'FHD', 'UHD',
        # K系列
        '4K', '8K'
    }
    
    if not quality:
        return False, "质量标识不能为空"
    
    # 对于通用标识和K系列使用大写，对于p系列保持原样
    if quality.endswith('p'):
        normalized_quality = quality
    else:
        normalized_quality = quality.upper()
    
    if normalized_quality not in valid_qualities:
        return False, f"无效的质量标识。支持的值: {', '.join(sorted(valid_qualities))}"
    
    return True, ""

def validate_year(year: Optional[int]) -> Tuple[bool, str]:
    """
    验证年份
    规则：
    - 电影：1888年至今
    - 电视剧：1936年至今
    
    Args:
        year: 年份
    
    Returns:
        (bool, str): (是否有效, 错误信息)
    """
    if year is None:
        return True, ""  # 允许年份为空
        
    current_year = datetime.now().year
    
    if not isinstance(year, int):
        return False, "年份必须是整数"
        
    if year < 1888:
        return False, "年份不能早于1888年"
        
    if year > current_year + 1:  # 允许未来一年的作品
        return False, f"年份不能超过{current_year + 1}年"
    
    return True, ""

def validate_file_name(file_name: str) -> Tuple[bool, str]:
    """
    验证文件名
    
    Args:
        file_name: 文件名
    
    Returns:
        (bool, str): (是否有效, 错误信息)
    """
    if not file_name:
        return False, "文件名不能为空"
    
    # 检查文件名长度
    if len(file_name) > 255:
        return False, "文件名过长"
    
    # 检查非法字符
    if re.search(r'[<>:"|?*]', file_name):
        return False, "文件名包含非法字符"
    
    # 检查文件扩展名
    valid_extensions = {'.mp4', '.mkv', '.avi', '.m4v', '.mov', '.wmv'}
    if not any(file_name.lower().endswith(ext) for ext in valid_extensions):
        return False, f"不支持的文件类型。支持的扩展名: {', '.join(valid_extensions)}"
    
    return True, ""

# 示例使用和测试代码
if __name__ == "__main__":
    # 测试电影标题验证
    assert validate_movie_title("盗梦空间 (2010)")[0] == True
    assert validate_movie_title("Inception.2010.1080p")[0] == True
    assert validate_movie_title("")[0] == False
    assert validate_movie_title("a" * 201)[0] == False
    
    # 测试剧集格式验证
    assert validate_series_format("S01E01")[0] == True
    assert validate_series_format("1x01")[0] == True
    assert validate_series_format("E01")[0] == True
    assert validate_series_format("S00E00")[0] == False
    assert validate_series_format("invalid")[0] == False
    
    # 测试质量标识验证
    assert validate_quality("1080p")[0] == True
    assert validate_quality("4K")[0] == True
    assert validate_quality("invalid")[0] == False
    
    # 测试年份验证
    assert validate_year(2010)[0] == True
    assert validate_year(1887)[0] == False
    assert validate_year(datetime.now().year + 2)[0] == False
    
    # 测试文件名验证
    assert validate_file_name("movie.mp4")[0] == True
    assert validate_file_name("movie.mkv")[0] == True
    assert validate_file_name("movie.invalid")[0] == False
    
    print("所有测试通过！")
