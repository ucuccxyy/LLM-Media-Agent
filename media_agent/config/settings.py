"""
全局配置管理模块

包含全局配置类Settings，用于管理应用程序的所有配置参数。
通过环境变量加载配置，并提供配置验证功能。
"""

from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv


class Settings:
    """
    全局配置类
    
    属性:
        - llm_provider: str - LLM提供商 ("ollama", "openai", "anthropic", "google")
        - ollama_host: str - Ollama服务地址
        - ollama_model: str - Ollama模型名称
        - openai_api_key: str - OpenAI API密钥
        - openai_model: str - OpenAI模型名称
        - anthropic_api_key: str - Anthropic API密钥
        - anthropic_model: str - Anthropic模型名称
        - google_api_key: str - Google API密钥
        - google_model: str - Google模型名称
        - radarr_host: str - Radarr服务地址
        - radarr_api_key: str - Radarr API密钥
        - sonarr_host: str - Sonarr服务地址
        - sonarr_api_key: str - Sonarr API密钥
        - qbittorrent_host: str - qBittorrent服务地址
        - qbittorrent_username: str - qBittorrent用户名
        - qbittorrent_password: str - qBittorrent密码
        - download_path: Path - 下载目录路径
        - movies_path: Path - 电影存储路径
        - tv_shows_path: Path - 电视剧存储路径
        - log_level: str = "INFO" - 日志级别
    """
    
    def __init__(self):
        """初始化配置对象，设置默认值"""
        # 获取项目根目录
        self.project_root = Path(__file__).parent.parent.parent
        self.docker_root = self.project_root / "media-agent" / "docker"
        
        # LLM提供商配置
        self.llm_provider: str = "ollama"  # 默认使用Ollama
        
        # Ollama配置
        self.ollama_host: str = "http://localhost:11434"
        self.ollama_model: str = "command-r-plus:latest"
        
        # OpenAI配置
        self.openai_api_key: Optional[str] = None
        self.openai_model: str = "gpt-4o-mini"
        self.openai_base_url: Optional[str] = None  # 支持自定义OpenAI兼容API
        
        # DeepSeek配置 (使用OpenAI兼容API)
        self.deepseek_api_key: Optional[str] = None
        self.deepseek_model: str = "deepseek-chat"
        self.deepseek_base_url: str = "https://api.deepseek.com"
        
        # Anthropic配置
        self.anthropic_api_key: Optional[str] = None
        self.anthropic_model: str = "claude-3-5-sonnet-20241022"
        
        # Google配置
        self.google_api_key: Optional[str] = None
        self.google_model: str = "gemini-1.5-flash"
        
        # Radarr配置
        self.radarr_host: str = "http://localhost:7878"
        self.radarr_api_key: Optional[str] = None
        
        # Sonarr配置
        self.sonarr_host: str = "http://localhost:8989"
        self.sonarr_api_key: Optional[str] = None
        
        # qBittorrent配置
        self.qbittorrent_host: str = "http://localhost:8081"
        self.qbittorrent_username: str = "admin"
        self.qbittorrent_password: str = "adminadmin"
        
        # 路径配置 - 使用项目的data目录
        self.data_root: Path = self.project_root / "media_agent" / "data"
        self.download_path: Path = self.data_root / "downloads"
        self.incomplete_path: Path = self.download_path / "incomplete"
        self.movies_path: Path = self.data_root / "movies"
        self.tv_shows_path: Path = self.data_root / "tv_shows"
        
        # 其他配置
        self.log_level: str = "INFO"

        # 初始化时自动加载配置
        self.load_from_env()
    
    def load_from_env(self) -> None:
        """
        从环境变量加载配置
        
        首先尝试加载.env文件，然后从环境变量中读取配置值
        如果环境变量存在则使用环境变量值，否则保持默认值
        """
        # 加载.env文件
        load_dotenv()
        
        # LLM提供商配置
        self.llm_provider = os.getenv("LLM_PROVIDER", self.llm_provider)
        
        # Ollama配置
        self.ollama_host = os.getenv("OLLAMA_HOST", self.ollama_host)
        self.ollama_model = os.getenv("OLLAMA_MODEL", self.ollama_model)
        
        # OpenAI配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.openai_model = os.getenv("OPENAI_MODEL", self.openai_model)
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", self.openai_base_url)
        
        # DeepSeek配置 (使用OpenAI兼容API)
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", self.deepseek_api_key)
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", self.deepseek_model)
        self.deepseek_base_url = os.getenv("DEEPSEEK_BASE_URL", self.deepseek_base_url)
        
        # Anthropic配置
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", self.anthropic_api_key)
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", self.anthropic_model)
        
        # Google配置
        self.google_api_key = os.getenv("GOOGLE_API_KEY", self.google_api_key)
        self.google_model = os.getenv("GOOGLE_MODEL", self.google_model)
        
        # Radarr配置
        self.radarr_host = os.getenv("RADARR_HOST", self.radarr_host)
        self.radarr_api_key = os.getenv("RADARR_API_KEY", self.radarr_api_key)
        
        # Sonarr配置
        self.sonarr_host = os.getenv("SONARR_HOST", self.sonarr_host)
        self.sonarr_api_key = os.getenv("SONARR_API_KEY", self.sonarr_api_key)
        
        # qBittorrent配置
        self.qbittorrent_host = os.getenv("QBITTORRENT_HOST", self.qbittorrent_host)
        self.qbittorrent_username = os.getenv("QBITTORRENT_USERNAME", self.qbittorrent_username)
        self.qbittorrent_password = os.getenv("QBITTORRENT_PASSWORD", self.qbittorrent_password)
        
        # 路径配置
        download_path = os.getenv("DOWNLOAD_PATH")
        if download_path:
            self.download_path = Path(download_path)
        else:
            self.download_path = self.download_path  # 保持默认
        
        movies_path = os.getenv("MOVIES_PATH")
        if movies_path:
            self.movies_path = Path(movies_path)
        else:
            self.movies_path = self.movies_path  # 保持默认
        
        tv_shows_path = os.getenv("TV_SHOWS_PATH")
        if tv_shows_path:
            self.tv_shows_path = Path(tv_shows_path)
        else:
            self.tv_shows_path = self.tv_shows_path  # 保持默认
            
        # 其他配置
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        
    def validate(self) -> bool:
        """
        验证配置完整性
        
        返回:
            bool: 配置是否有效
            
        验证项:
        1. 根据LLM提供商验证相应的配置
        2. 必需的服务地址和API密钥
        3. 路径配置的存在性和权限
        4. 基本URL格式检查
        """
        # 检查LLM提供商配置
        if self.llm_provider == "ollama":
            if not self.ollama_host.startswith(("http://", "https://")):
                return False
        elif self.llm_provider == "openai":
            if not self.openai_api_key:
                return False
        elif self.llm_provider == "deepseek":
            if not self.deepseek_api_key:
                return False
        elif self.llm_provider == "anthropic":
            if not self.anthropic_api_key:
                return False
        elif self.llm_provider == "google":
            if not self.google_api_key:
                return False
        else:
            return False  # 不支持的提供商
            
        # 检查Radarr配置
        if not all([
            self.radarr_host,
            self.radarr_api_key,
            self.radarr_host.startswith(("http://", "https://"))
        ]):
            return False
            
        # 检查Sonarr配置
        if not all([
            self.sonarr_host,
            self.sonarr_api_key,
            self.sonarr_host.startswith(("http://", "https://"))
        ]):
            return False
            
        # 检查qBittorrent配置
        if not all([
            self.qbittorrent_host,
            self.qbittorrent_username,
            self.qbittorrent_password,
            self.qbittorrent_host.startswith(("http://", "https://"))
        ]):
            return False
            
        # 检查路径配置
        required_paths = [
            self.download_path,
            self.movies_path,
            self.tv_shows_path
        ]
        
        if not all(required_paths):
            return False
            
        # 验证路径存在性和权限
        for path in required_paths:
            try:
                # 确保路径存在
                path.mkdir(parents=True, exist_ok=True)
                # 检查读写权限
                test_file = path / ".test_write"
                test_file.touch()
                test_file.unlink()
            except (PermissionError, OSError):
                return False
                
        return True
        
    def get_llm_config(self) -> dict:
        """
        获取当前LLM提供商的配置
        
        返回:
            dict: 包含当前LLM提供商配置的字典
        """
        if self.llm_provider == "ollama":
            return {
                "provider": "ollama",
                "host": self.ollama_host,
                "model": self.ollama_model
            }
        elif self.llm_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model,
                "base_url": self.openai_base_url
            }
        elif self.llm_provider == "deepseek":
            return {
                "provider": "deepseek",
                "api_key": self.deepseek_api_key,
                "model": self.deepseek_model,
                "base_url": self.deepseek_base_url
            }
        elif self.llm_provider == "anthropic":
            return {
                "provider": "anthropic",
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model
            }
        elif self.llm_provider == "google":
            return {
                "provider": "google",
                "api_key": self.google_api_key,
                "model": self.google_model
            }
        else:
            raise ValueError(f"不支持的LLM提供商: {self.llm_provider}")
        
    def __str__(self) -> str:
        """返回配置的字符串表示"""
        llm_config = self.get_llm_config()
        
        return (
            f"Settings:\n"
            f"  LLM Provider: {self.llm_provider}\n"
            f"  LLM Config: {llm_config}\n"
            f"  Radarr:\n"
            f"    Host: {self.radarr_host}\n"
            f"    API Key: {'*' * 8 if self.radarr_api_key else 'Not Set'}\n"
            f"  Sonarr:\n"
            f"    Host: {self.sonarr_host}\n"
            f"    API Key: {'*' * 8 if self.sonarr_api_key else 'Not Set'}\n"
            f"  qBittorrent:\n"
            f"    Host: {self.qbittorrent_host}\n"
            f"    Username: {self.qbittorrent_username}\n"
            f"  Paths:\n"
            f"    Downloads: {self.download_path}\n"
            f"    Movies: {self.movies_path}\n"
            f"    TV Shows: {self.tv_shows_path}\n"
            f"  Log Level: {self.log_level}"
        )
