from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage

class SessionHistory(BaseChatMessageHistory):
    """
    一个将会话历史保存在内存中的类。
    """
    def __init__(self):
        self.messages = []

    def add_messages(self, messages: list[BaseMessage]) -> None:
        self.messages.extend(messages)

    def clear(self) -> None:
        self.messages = []

# 全局会话历史缓存
_session_histories: dict[str, SessionHistory] = {}

def get_session_history(session_id: str) -> SessionHistory:
    """
    根据会话ID获取会话历史记录。
    如果历史记录不存在，则创建一个新的。
    """
    if session_id not in _session_histories:
        _session_histories[session_id] = SessionHistory()
    return _session_histories[session_id] 