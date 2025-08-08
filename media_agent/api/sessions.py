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
            # We append/update the tool call to the *last* AIMessage's tool_calls list.
            if not hasattr(self.messages[-1], 'tool_calls') or self.messages[-1].tool_calls is None:
                self.messages[-1].tool_calls = []
            
            existing_calls = self.messages[-1].tool_calls
            # 去重：如果已存在相同 id 的调用，则更新其参数而不是追加
            for existing in existing_calls:
                if existing.get('id') == tool_call.get('id'):
                    # 以最新的参数为准（流式分片会逐步完善 args）
                    existing['args'] = tool_call.get('args', existing.get('args'))
                    # 同步名称（一般不变）
                    if tool_call.get('name'):
                        existing['name'] = tool_call['name']
                    break
            else:
                # 未找到相同 id，安全地追加
                existing_calls.append(tool_call)

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

    def get_sanitized_messages(self) -> List[BaseMessage]:
        """返回去重后的历史消息副本，确保每个 AIMessage 的 tool_calls 按 id 唯一且完整。"""
        sanitized: List[BaseMessage] = []
        for msg in self.messages:
            if isinstance(msg, AIMessage) and getattr(msg, 'tool_calls', None):
                # 基于 id 去重，后出现的分片覆盖先前的 args
                dedup: dict[str, dict] = {}
                for tc in msg.tool_calls:
                    tc_id = tc.get('id') or str(uuid4())
                    merged = dedup.get(tc_id, {})
                    merged['id'] = tc_id
                    # 姓名保持最新非空
                    name_val = tc.get('name') or merged.get('name')
                    if name_val:
                        merged['name'] = name_val
                    # args 以最新分片为准
                    if 'args' in tc:
                        merged['args'] = tc['args']
                    dedup[tc_id] = merged
                # 生成新的 AIMessage，避免就地修改原消息对象
                sanitized.append(
                    AIMessage(content=msg.content or "", tool_calls=list(dedup.values()))
                )
            else:
                sanitized.append(msg)
        return sanitized

    def get_textualized_messages(self, max_result_chars: int = 800) -> List[BaseMessage]:
        """将历史中的工具调用与结果转换为纯文本AI消息，移除所有ToolMessage。
        返回仅包含 HumanMessage 与 AIMessage 的消息列表。
        - 对于含有 tool_calls 的 AIMessage，会将其后紧邻的匹配 ToolMessage 合并为一条纯文本AIMessage摘要。
        - 结果文本可按 max_result_chars 进行截断，避免过长。
        """
        # 先拿到已去重后的副本，避免原对象被修改
        sanitized = self.get_sanitized_messages()
        textualized: List[BaseMessage] = []
        i = 0
        n = len(sanitized)
        from langchain_core.messages import HumanMessage

        while i < n:
            msg = sanitized[i]
            # 仅保留 Human / AI 两类
            if isinstance(msg, HumanMessage):
                textualized.append(msg)
                i += 1
                continue

            if isinstance(msg, AIMessage):
                tool_calls = getattr(msg, 'tool_calls', None) or []
                if not tool_calls:
                    # 普通AI文本，直接保留
                    textualized.append(AIMessage(content=msg.content or ""))
                    i += 1
                    continue

                # 将 tool_calls 与后续的 tool 结果配对，生成文本摘要
                summary_lines: list[str] = []
                for tc in tool_calls:
                    tc_id = tc.get('id')
                    name = tc.get('name', 'unknown_tool')
                    args = tc.get('args', {})
                    # 在随后的消息中寻找第一个匹配 tool_call_id 的 ToolMessage
                    result_text = None
                    j = i + 1
                    while j < n:
                        next_msg = sanitized[j]
                        if isinstance(next_msg, AIMessage) or isinstance(next_msg, HumanMessage):
                            # 下一个轮次开始，停止查找
                            break
                        if isinstance(next_msg, ToolMessage) and next_msg.tool_call_id == tc_id:
                            result_text = next_msg.content or ""
                            break
                        j += 1

                    # 构造摘要块
                    args_preview = str(args)
                    if len(args_preview) > 300:
                        args_preview = args_preview[:300] + "..."
                    result_preview = (result_text or "(no result)")
                    if len(result_preview) > max_result_chars:
                        result_preview = result_preview[:max_result_chars] + "..."
                    summary_lines.append(
                        f"[Tool] {name} args={args_preview}\n[Result] {result_preview}"
                    )

                merged_content_parts = []
                if msg.content:
                    merged_content_parts.append(msg.content)
                if summary_lines:
                    merged_content_parts.append("\n--- Previous tool actions ---\n" + "\n\n".join(summary_lines))
                merged_content = "\n\n".join(merged_content_parts).strip()
                textualized.append(AIMessage(content=merged_content))

                # 跳过紧随其后的所有 ToolMessage（直到遇到下一条 Human/AI）
                k = i + 1
                while k < n:
                    next_msg = sanitized[k]
                    if isinstance(next_msg, ToolMessage):
                        k += 1
                        continue
                    # 遇到下一条 Human/AI，停止跳过
                    break
                i = k
                continue

            # 其他类型（例如ToolMessage），不直接保留
            i += 1

        return textualized

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