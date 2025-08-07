from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage
from uuid import uuid4
from typing import List

class InMemoryHistory(BaseChatMessageHistory):
    """
    一个将会话历史保存在内存中的类。
    """
    def __init__(self, max_messages: int = 50):
        self.messages: List[BaseMessage] = []
        self.max_messages = max_messages

    def add_messages(self, messages: list[BaseMessage]) -> None:
        self.messages.extend(messages)
        self._trim_history()
    
    def add_user_message(self, message: str) -> None:
        """Adds a user message to the history."""
        from langchain_core.messages import HumanMessage
        self.add_messages([HumanMessage(content=message)])

    def add_ai_message(self, message: str) -> None:
        """Adds an AI message to the history, associating it with previous tool calls."""
        # This concludes a turn. We are adding the final response.
        self.add_messages([AIMessage(content=message)])

    def add_ai_tool_call_message(self, tool_call: dict):
        """Adds a tool call message from the AI to the history."""
        # Ensure we have a unique ID for the tool call
        if 'id' not in tool_call:
            tool_call['id'] = str(uuid4())
        
        # If there is no AIMessage, we create one.
        if not self.messages or not isinstance(self.messages[-1], AIMessage):
            self.add_messages([AIMessage(content="", tool_calls=[tool_call])])
        else:
            # We append the tool call to the *last* AIMessage's tool_calls list.
            if not hasattr(self.messages[-1], 'tool_calls'):
                self.messages[-1].tool_calls = []
            self.messages[-1].tool_calls.append(tool_call)

    def add_tool_result_message(self, tool_name: str, result: str, tool_call_id: str):
        """Adds a tool's result to the history."""
        self.add_messages([ToolMessage(content=result, name=tool_name, tool_call_id=tool_call_id)])

    def clear(self) -> None:
        self.messages = []
    
    def _trim_history(self) -> None:
        """保持历史消息数量在限制范围内，保留最新的消息"""
        if len(self.messages) > self.max_messages:
            # 保留最新的消息，删除最旧的消息
            # 为了保持对话的完整性，我们删除中间的消息，保留开头和结尾
            keep_start = 10  # 保留前5条消息（通常是系统消息和初始对话）
            keep_end = self.max_messages - keep_start  # 保留最新的消息
            
            self.messages = (
                self.messages[:keep_start] + 
                self.messages[-keep_end:]
            )

# 全局会话历史缓存
_session_histories: dict[str, InMemoryHistory] = {}

def get_session_history(session_id: str) -> InMemoryHistory:
    """
    根据会话ID获取会话历史记录。
    如果历史记录不存在，则创建一个新的。
    """
    if session_id not in _session_histories:
        _session_histories[session_id] = InMemoryHistory()
    return _session_histories[session_id]

def clear_session_history(session_id: str) -> bool:
    """
    清除指定会话的历史记录
    
    参数:
        session_id: 会话ID
        
    返回:
        bool: 是否成功清除
    """
    if session_id in _session_histories:
        del _session_histories[session_id]
        return True
    return False

def get_all_session_ids() -> list[str]:
    """
    获取所有活跃的会话ID列表
    
    返回:
        list[str]: 会话ID列表
    """
    return list(_session_histories.keys())

def cleanup_old_sessions(max_sessions: int = 100) -> int:
    """
    清理过多的会话，保留最新的会话
    
    参数:
        max_sessions: 最大会话数量
        
    返回:
        int: 清理的会话数量
    """
    if len(_session_histories) <= max_sessions:
        return 0
    
    # 按会话ID排序，删除最旧的会话
    session_ids = sorted(_session_histories.keys())
    sessions_to_remove = session_ids[:-max_sessions]
    
    for session_id in sessions_to_remove:
        del _session_histories[session_id]
    
    return len(sessions_to_remove) 