"""
多提供商LLM管理
支持OpenAI、Anthropic、Google和Ollama
"""

import sys
import os
from typing import Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from langchain_ollama.chat_models import ChatOllama

# 可选导入，如果包未安装则设为None
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    ChatOpenAI = None
    OPENAI_AVAILABLE = False

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ChatAnthropic = None
    ANTHROPIC_AVAILABLE = False

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GOOGLE_AVAILABLE = True
except ImportError:
    ChatGoogleGenerativeAI = None
    GOOGLE_AVAILABLE = False


class LLMManager:
    """
    多提供商LLM管理器，支持OpenAI、Anthropic、Google和Ollama
    """
    
    def __init__(self, settings):
        """
        初始化LLMManager
        
        参数:
            - settings: Settings对象，包含LLM配置
        """
        self.settings = settings
        self.llm = self._create_llm()
    
    def _create_llm(self):
        """
        根据配置创建相应的LLM实例
        
        返回:
            LLM实例
        """
        provider = self.settings.llm_provider
        
        if provider == "ollama":
            return self._create_ollama_llm()
        elif provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("langchain-openai 未安装。请运行: pip install langchain-openai")
            return self._create_openai_llm()
        elif provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("langchain-anthropic 未安装。请运行: pip install langchain-anthropic")
            return self._create_anthropic_llm()
        elif provider == "google":
            if not GOOGLE_AVAILABLE:
                raise ImportError("langchain-google-genai 未安装。请运行: pip install langchain-google-genai")
            return self._create_google_llm()
        else:
            raise ValueError(f"不支持的LLM提供商: {provider}")
    
    def _create_ollama_llm(self):
        """创建Ollama LLM实例"""
        return ChatOllama(
            base_url=self.settings.ollama_host,
            model=self.settings.ollama_model,
            temperature=0
        )
    
    def _create_openai_llm(self):
        """创建OpenAI LLM实例"""
        kwargs = {
            "model": self.settings.openai_model,
            "temperature": 0,
            "api_key": self.settings.openai_api_key
        }
        
        # 如果设置了自定义base_url，则使用它
        if self.settings.openai_base_url:
            kwargs["base_url"] = self.settings.openai_base_url
            
        return ChatOpenAI(**kwargs)
    
    def _create_anthropic_llm(self):
        """创建Anthropic LLM实例"""
        return ChatAnthropic(
            model=self.settings.anthropic_model,
            temperature=0,
            api_key=self.settings.anthropic_api_key
        )
    
    def _create_google_llm(self):
        """创建Google LLM实例"""
        return ChatGoogleGenerativeAI(
            model=self.settings.google_model,
            temperature=0,
            google_api_key=self.settings.google_api_key
        )
    
    def get_llm(self):
        """获取LLM实例"""
        return self.llm
    
    def test_connection(self) -> bool:
        """
        测试LLM连接
        
        返回:
            bool: 连接是否成功
        """
        try:
            response = self.llm.invoke("测试连接")
            return True
        except Exception as e:
            print(f"LLM连接测试失败: {e}")
            return False


# 为了保持向后兼容性，保留OllamaManager类
class OllamaManager:
    """
    Ollama服务管理器（向后兼容）
    """
    
    def __init__(self, host: str, model: str):
        """
        初始化OllamaManager
        
        参数:
            - host: Ollama服务的URL
            - model: 要使用的模型名称
        """
        self.llm = ChatOllama(base_url=host, model=model, temperature=0)


if __name__ == "__main__":
    # 测试代码
    from media_agent.config.settings import Settings
    
    settings = Settings()
    settings.llm_provider = "ollama"  # 测试Ollama
    
    try:
        llm_manager = LLMManager(settings)
        print("LLMManager 实例化成功")
        
        if llm_manager.test_connection():
            print("LLM连接测试成功")
        else:
            print("LLM连接测试失败")
            
    except Exception as e:
        print(f"测试失败: {e}")