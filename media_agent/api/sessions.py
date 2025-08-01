from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage
from uuid import uuid4
from typing import List

class InMemoryHistory(BaseChatMessageHistory):
    """
    一个将会话历史保存在内存中的类。
    """
    def __init__(self):
        self.messages: List[BaseMessage] = []

    def add_messages(self, messages: list[BaseMessage]) -> None:
        self.messages.extend(messages)
    
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