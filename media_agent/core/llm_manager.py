"""
Ollama LLM管理
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from langchain_ollama.chat_models import ChatOllama

class OllamaManager:
    """
    Ollama服务管理器，用于创建和配置ChatOllama实例。
    """
    
    def __init__(self, host: str, model: str):
        """
        初始化OllamaManager。
        
        参数:
            - host: Ollama服务的URL。
            - model: 要使用的模型名称。
        """
        self.llm = ChatOllama(base_url=host, model=model, temperature=0)

if __name__ == "__main__":
    # 简单的测试，确保ChatOllama可以被实例化
    try:
        llm_manager = OllamaManager(host="http://localhost:11434", model="llama3")
        print("OllamaManager 和 ChatOllama 实例化成功。")
        # 可以尝试一次简单的调用来验证连接
        response = llm_manager.llm.invoke("你好")
        print("LLM响应:", response.content)
    except Exception as e:
        print(f"测试失败: {e}")
    print("解析意图:", intent)