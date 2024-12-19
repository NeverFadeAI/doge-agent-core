"""
exceptions.py
AI Agent system exceptions hierarchy
"""
from typing import Optional, Any, Dict
from datetime import datetime


class DogeAgentError(Exception):
    """所有自定义异常的基类"""

    def __init__(
            self,
            message: str,
            error_code: Optional[str] = None,
            details: Optional[Dict[str, Any]] = None,
            timestamp: Optional[datetime] = None
    ) -> None:
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        self.timestamp = timestamp or datetime.utcnow()

        # 构建错误消息
        error_msg = f"[{self.error_code}] {self.message}"
        if self.details:
            error_msg += f"\nDetails: {self.details}"

        super().__init__(error_msg)

    def to_dict(self) -> Dict[str, Any]:
        """将异常转换为字典格式，便于API返回"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "type": self.__class__.__name__
        }


# AI Model Related Exceptions
class ModelError(DogeAgentError):
    """AI模型相关错误的基类"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="MODEL_ERROR", **kwargs)


class GrokAPIError(ModelError):
    """Grok API调用失败"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="GROK_API_ERROR", **kwargs)


class FluxAPIError(ModelError):
    """Flux API调用失败"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="FLUX_API_ERROR", **kwargs)


class ModelTimeoutError(ModelError):
    """模型调用超时"""

    def __init__(self, message: str, timeout: int, **kwargs):
        details = kwargs.get("details", {})
        details["timeout_seconds"] = timeout
        super().__init__(message, error_code="MODEL_TIMEOUT", details=details, **kwargs)


# Agent Related Exceptions
class AgentError(DogeAgentError):
    """Agent相关错误的基类"""

    def __init__(self, message: str, agent_id: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if agent_id:
            details["agent_id"] = agent_id
        super().__init__(message, error_code="AGENT_ERROR", details=details, **kwargs)


class AgentInitializationError(AgentError):
    """Agent初始化失败"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="AGENT_INIT_ERROR", **kwargs)


class AgentExecutionError(AgentError):
    """Agent执行失败"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="AGENT_EXEC_ERROR", **kwargs)


class AgentCommunicationError(AgentError):
    """Agent之间通信失败"""

    def __init__(self, message: str, source_agent: str, target_agent: str, **kwargs):
        details = kwargs.get("details", {})
        details.update({
            "source_agent": source_agent,
            "target_agent": target_agent
        })
        super().__init__(message, error_code="AGENT_COMM_ERROR", details=details, **kwargs)


# Memory Related Exceptions
class MemoryError(DogeAgentError):
    """内存管理相关错误的基类"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="MEMORY_ERROR", **kwargs)


class MemoryStorageError(MemoryError):
    """内存存储错误"""

    def __init__(self, message: str, storage_type: str, **kwargs):
        details = kwargs.get("details", {})
        details["storage_type"] = storage_type
        super().__init__(message, error_code="MEMORY_STORAGE_ERROR", details=details, **kwargs)


class MemoryRetrievalError(MemoryError):
    """内存检索错误"""

    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if query:
            details["query"] = query
        super().__init__(message, error_code="MEMORY_RETRIEVAL_ERROR", details=details, **kwargs)


# Database Related Exceptions
class DatabaseError(DogeAgentError):
    """数据库相关错误的基类"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="DB_ERROR", **kwargs)


class MySQLError(DatabaseError):
    """MySQL错误"""

    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if query:
            details["query"] = query
        super().__init__(message, error_code="MYSQL_ERROR", details=details, **kwargs)


class RedisError(DatabaseError):
    """Redis错误"""

    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if operation:
            details["operation"] = operation
        super().__init__(message, error_code="REDIS_ERROR", details=details, **kwargs)


# Input/Validation Related Exceptions
class ValidationError(DogeAgentError):
    """输入验证错误"""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        super().__init__(message, error_code="VALIDATION_ERROR", details=details, **kwargs)


# Configuration Related Exceptions
class ConfigError(DogeAgentError):
    """配置相关错误"""

    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, error_code="CONFIG_ERROR", details=details, **kwargs)


# Rate Limiting Exceptions
class RateLimitError(DogeAgentError):
    """速率限制错误"""

    def __init__(
            self,
            message: str,
            limit: int,
            reset_time: Optional[datetime] = None,
            **kwargs
    ):
        details = kwargs.get("details", {})
        details.update({
            "limit": limit,
            "reset_time": reset_time.isoformat() if reset_time else None
        })
        super().__init__(message, error_code="RATE_LIMIT_ERROR", details=details, **kwargs)


# Usage Examples:
"""
try:
    # Grok API 调用失败示例
    raise GrokAPIError(
        message="Failed to call Grok API: Connection timeout",
        details={"endpoint": "/v1/chat/completions", "status_code": 504}
    )
except GrokAPIError as e:
    print(e.to_dict())

try:
    # Agent间通信失败示例
    raise AgentCommunicationError(
        message="Failed to send message between agents",
        source_agent="creative_agent",
        target_agent="vision_agent",
        details={"message_type": "design_review", "retry_count": 3}
    )
except AgentCommunicationError as e:
    print(e.to_dict())

try:
    # 内存检索失败示例
    raise MemoryRetrievalError(
        message="Failed to retrieve memory",
        query="user_preferences",
        details={"storage_type": "redis", "error_type": "connection_timeout"}
    )
except MemoryRetrievalError as e:
    print(e.to_dict())
"""