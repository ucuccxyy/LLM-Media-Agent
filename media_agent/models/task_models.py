"""
任务数据模型

这个模块定义了系统中所有任务相关的数据模型，包括：
- TaskType: 任务类型枚举
- TaskStatus: 任务状态枚举
- Task: 任务主模型

所有模型都使用Pydantic进行数据验证和序列化。
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from uuid import uuid4

class TaskType(Enum):
    """任务类型枚举"""
    SEARCH_MOVIE = "search_movie"          # 搜索电影
    SEARCH_TV = "search_tv"                # 搜索电视剧
    ADD_MOVIE = "add_movie"                # 添加电影下载任务
    ADD_TV = "add_tv"                      # 添加电视剧下载任务
    CHECK_STATUS = "check_status"          # 检查下载状态
    ORGANIZE_FILES = "organize_files"       # 整理文件
    UPDATE_LIBRARY = "update_library"       # 更新媒体库

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"           # 等待执行
    PROCESSING = "processing"     # 正在执行
    COMPLETED = "completed"       # 执行完成
    FAILED = "failed"            # 执行失败
    CANCELLED = "cancelled"       # 已取消

class TaskResult(BaseModel):
    """任务结果模型"""
    success: bool = Field(default=False, description="任务是否成功")
    message: str = Field(default="", description="结果消息")
    data: Optional[Dict[str, Any]] = Field(default=None, description="详细结果数据")

class Task(BaseModel):
    """任务主模型"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="任务ID")
    type: TaskType = Field(..., description="任务类型")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    params: Dict[str, Any] = Field(default_factory=dict, description="任务参数")
    result: Optional[TaskResult] = Field(default=None, description="任务结果")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    error: Optional[str] = Field(default=None, description="错误信息")

    def update_status(self, new_status: TaskStatus, error: str = None) -> None:
        """
        更新任务状态
        
        Args:
            new_status: 新状态
            error: 错误信息（如果有）
        """
        self.status = new_status
        self.error = error
        self.updated_at = datetime.now()

    def complete(self, result: TaskResult) -> None:
        """
        完成任务
        
        Args:
            result: 任务结果
        """
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.updated_at = datetime.now()

    def fail(self, error: str) -> None:
        """
        标记任务失败
        
        Args:
            error: 错误信息
        """
        self.status = TaskStatus.FAILED
        self.error = error
        self.updated_at = datetime.now()

    @field_validator('type')
    @classmethod
    def validate_task_type(cls, v: TaskType) -> TaskType:
        if not isinstance(v, TaskType):
            raise ValueError(f"无效的任务类型: {v}")
        return v

    @field_validator('status')
    @classmethod
    def validate_task_status(cls, v: TaskStatus) -> TaskStatus:
        if not isinstance(v, TaskStatus):
            raise ValueError(f"无效的任务状态: {v}")
        return v

# 示例使用和测试代码
if __name__ == "__main__":
    # 创建任务实例
    task = Task(
        id="uuid-123",
        type=TaskType.SEARCH_MOVIE,
        status=TaskStatus.PENDING,
        params={"query": "盗梦空间"}
    )
    
    # 验证任务类型
    assert task.type == TaskType.SEARCH_MOVIE
    
    # 测试状态更新
    task.update_status(TaskStatus.PROCESSING)
    assert task.status == TaskStatus.PROCESSING
    
    # 测试任务完成
    result = TaskResult(
        success=True,
        message="搜索完成",
        data={"movies": ["盗梦空间 (2010)"]}
    )
    task.complete(result)
    assert task.status == TaskStatus.COMPLETED
    assert task.result.success == True
    
    # 测试任务失败
    task = Task(
        type=TaskType.SEARCH_MOVIE,
        params={"query": "不存在的电影"}
    )
    task.fail("未找到相关电影")
    assert task.status == TaskStatus.FAILED
    assert task.error == "未找到相关电影"
    
    print("所有测试通过！")
