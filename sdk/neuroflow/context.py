from typing import Optional, Dict, Any, List
from contextvars import ContextVar
import uuid
import json
from datetime import datetime
from enum import Enum

class MemoryType(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

class MemoryEntry:
    """记忆条目"""
    def __init__(self, key: str, value: Any, memory_type: MemoryType, tags: List[str] = None, 
                 importance: float = 0.5, ttl_seconds: Optional[int] = None):
        self.key = key
        self.value = value
        self.type = memory_type
        self.tags = tags or []
        self.importance = importance  # 0.0-1.0
        self.created_at = datetime.utcnow()
        self.ttl_seconds = ttl_seconds  # Time-to-live in seconds
        self.access_count = 0
        
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'value': self.value,
            'type': self.type.value,
            'tags': self.tags,
            'importance': self.importance,
            'created_at': self.created_at.isoformat(),
            'ttl_seconds': self.ttl_seconds,
            'access_count': self.access_count
        }

class MemoryManager:
    """记忆管理器"""
    def __init__(self):
        self._memory_store: Dict[str, MemoryEntry] = {}
        self._recent_access: List[str] = []  # 最近访问的记忆键
        self._max_recent_items = 100
    
    def store(self, key: str, value: Any, memory_type: MemoryType = MemoryType.SHORT_TERM, 
              tags: List[str] = None, importance: float = 0.5, ttl_seconds: Optional[int] = None):
        """存储记忆"""
        entry = MemoryEntry(key, value, memory_type, tags, importance, ttl_seconds)
        self._memory_store[key] = entry
        
        # 添加到最近访问列表
        self._recent_access.append(key)
        if len(self._recent_access) > self._max_recent_items:
            self._recent_access.pop(0)
    
    def retrieve(self, key: str) -> Optional[Any]:
        """检索记忆"""
        if key in self._memory_store:
            entry = self._memory_store[key]
            if entry.is_expired():
                del self._memory_store[key]
                return None
            
            entry.access_count += 1
            return entry.value
        return None
    
    def search_by_tags(self, tags: List[str]) -> List[MemoryEntry]:
        """根据标签搜索记忆"""
        results = []
        for entry in self._memory_store.values():
            if entry.is_expired():
                continue
            if any(tag in entry.tags for tag in tags):
                results.append(entry)
        return sorted(results, key=lambda x: x.importance, reverse=True)
    
    def search_by_type(self, memory_type: MemoryType) -> List[MemoryEntry]:
        """根据类型搜索记忆"""
        results = []
        for entry in self._memory_store.values():
            if entry.is_expired():
                continue
            if entry.type == memory_type:
                results.append(entry)
        return sorted(results, key=lambda x: x.importance, reverse=True)
    
    def get_recent_items(self, count: int = 10) -> List[MemoryEntry]:
        """获取最近访问的记忆"""
        recent_keys = self._recent_access[-count:]
        results = []
        for key in reversed(recent_keys):
            if key in self._memory_store:
                entry = self._memory_store[key]
                if not entry.is_expired():
                    results.append(entry)
        return results
    
    def delete(self, key: str) -> bool:
        """删除记忆"""
        if key in self._memory_store:
            del self._memory_store[key]
            if key in self._recent_access:
                self._recent_access.remove(key)
            return True
        return False
    
    def clear_expired(self):
        """清除过期记忆"""
        expired_keys = []
        for key, entry in self._memory_store.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._memory_store[key]
            if key in self._recent_access:
                self._recent_access.remove(key)

class Context:
    """增强的请求上下文对象，支持记忆管理"""
    
    def __init__(self, trace_id: str, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        self.trace_id = trace_id
        self.user_id = user_id
        self.metadata = metadata or {}
        self.memory = MemoryManager()
        self.session_state = {}
        
    def __repr__(self):
        return f"Context(trace_id='{self.trace_id}', user_id={self.user_id}, metadata={self.metadata})"

# 全局上下文变量
_current_context: ContextVar[Optional[Context]] = ContextVar("_current_context", default=None)

def get_context() -> Context:
    """获取当前请求上下文"""
    ctx = _current_context.get()
    if ctx is None:
        # 如果没有上下文，创建一个默认的
        ctx = Context(trace_id=str(uuid.uuid4()))
        _current_context.set(ctx)
    return ctx

def set_context(context: Context) -> None:
    """设置当前请求上下文"""
    _current_context.set(context)

def clear_context() -> None:
    """清除当前请求上下文"""
    _current_context.set(None)