"""
NeuroFlow Python SDK - Vector Memory Store

向量记忆存储 - 支持语义检索的长短期记忆系统
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import uuid
import time
import logging
import math

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: str = ""
    value: Any = None
    memory_type: MemoryType = MemoryType.SHORT_TERM
    tags: List[str] = field(default_factory=list)
    importance: float = 0.5  # 0.0 - 1.0
    embedding: Optional[List[float]] = None
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "memory_type": self.memory_type.value,
            "tags": self.tags,
            "importance": self.importance,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
            "access_count": self.access_count,
            "ttl_seconds": self.ttl_seconds,
            "metadata": self.metadata,
        }


class VectorMemoryStore:
    """
    向量记忆存储 - 支持语义检索
    
    核心功能:
    1. 向量嵌入存储
    2. 语义相似度检索
    3. 记忆重要性管理
    4. TTL 过期管理
    
    用法:
        store = VectorMemoryStore()
        
        # 存储记忆
        await store.store(
            key="user_preference",
            value="喜欢简洁的回答",
            memory_type=MemoryType.LONG_TERM,
            tags=["user", "preference"],
        )
        
        # 语义检索
        memories = await store.semantic_search(
            query="用户喜欢什么样的回答？",
            top_k=3,
        )
    """
    
    def __init__(
        self, 
        max_memories: int = 1000,
        embedding_fn: Optional[callable] = None,
    ):
        self.max_memories = max_memories
        self.embedding_fn = embedding_fn
        
        # 记忆存储
        self._memories: Dict[str, MemoryEntry] = {}
        
        # 索引
        self._key_index: Dict[str, str] = {}  # key -> id
        self._tag_index: Dict[str, List[str]] = {}  # tag -> [ids]
        self._type_index: Dict[MemoryType, List[str]] = {
            t: [] for t in MemoryType
        }
    
    async def store(
        self,
        key: str,
        value: Any,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryEntry:
        """
        存储记忆
        
        Args:
            key: 记忆键
            value: 记忆值
            memory_type: 记忆类型
            tags: 标签列表
            importance: 重要性 (0.0-1.0)
            ttl_seconds: TTL (秒)
            metadata: 额外元数据
            
        Returns:
            记忆条目
        """
        # 检查是否已存在
        if key in self._key_index:
            entry_id = self._key_index[key]
            entry = self._memories[entry_id]
            entry.value = value
            entry.accessed_at = time.time()
            entry.importance = importance
            if tags:
                entry.tags = tags
            if ttl_seconds is not None:
                entry.ttl_seconds = ttl_seconds
            if metadata:
                entry.metadata.update(metadata)
            logger.debug(f"Updated memory: {key}")
            return entry
        
        # 创建新记忆
        entry = MemoryEntry(
            key=key,
            value=value,
            memory_type=memory_type,
            tags=tags or [],
            importance=importance,
            ttl_seconds=ttl_seconds,
            metadata=metadata or {},
        )
        
        # 生成嵌入向量
        if self.embedding_fn:
            try:
                text = self._value_to_text(value)
                entry.embedding = await self.embedding_fn(text)
            except Exception as e:
                logger.warning(f"Failed to generate embedding: {e}")
        
        # 存储
        self._memories[entry.id] = entry
        self._key_index[key] = entry.id
        
        # 更新索引
        for tag in entry.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            self._tag_index[tag].append(entry.id)
        
        self._type_index[entry.memory_type].append(entry.id)
        
        # 检查容量限制
        if len(self._memories) > self.max_memories:
            await self._evict_memories()
        
        logger.debug(f"Stored memory: {key}")
        return entry
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """检索记忆"""
        entry_id = self._key_index.get(key)
        if not entry_id:
            return None
        
        entry = self._memories.get(entry_id)
        if not entry:
            return None
        
        # 检查过期
        if entry.is_expired():
            await self.delete(key)
            return None
        
        # 更新访问信息
        entry.accessed_at = time.time()
        entry.access_count += 1
        
        return entry.value
    
    async def delete(self, key: str) -> bool:
        """删除记忆"""
        entry_id = self._key_index.get(key)
        if not entry_id:
            return False
        
        entry = self._memories.get(entry_id)
        if entry:
            # 清理索引
            for tag in entry.tags:
                if tag in self._tag_index:
                    self._tag_index[tag].remove(entry_id)
            
            if entry_id in self._type_index[entry.memory_type]:
                self._type_index[entry.memory_type].remove(entry_id)
            
            # 删除记忆
            del self._memories[entry_id]
            del self._key_index[key]
            
            logger.debug(f"Deleted memory: {key}")
            return True
        
        return False
    
    async def search_by_tags(self, tags: List[str]) -> List[MemoryEntry]:
        """根据标签搜索记忆"""
        result_ids = set()
        
        for tag in tags:
            if tag in self._tag_index:
                if not result_ids:
                    result_ids = set(self._tag_index[tag])
                else:
                    result_ids &= set(self._tag_index[tag])
        
        if not result_ids:
            return []
        
        entries = [
            self._memories[eid] 
            for eid in result_ids 
            if eid in self._memories
        ]
        
        return sorted(entries, key=lambda e: -e.importance)
    
    async def search_by_type(self, memory_type: MemoryType) -> List[MemoryEntry]:
        """根据类型搜索记忆"""
        ids = self._type_index.get(memory_type, [])
        entries = [
            self._memories[eid] 
            for eid in ids 
            if eid in self._memories and not self._memories[eid].is_expired()
        ]
        return entries
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.5,
    ) -> List[Tuple[MemoryEntry, float]]:
        """
        语义检索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            min_similarity: 最小相似度
            
        Returns:
            (记忆条目，相似度) 列表
        """
        if not self.embedding_fn:
            logger.warning("Embedding function not set, using keyword search")
            return await self._keyword_search(query, top_k)
        
        try:
            # 生成查询嵌入
            query_embedding = await self.embedding_fn(query)
            
            # 计算相似度
            results = []
            for entry in self._memories.values():
                if entry.embedding:
                    similarity = self._cosine_similarity(
                        query_embedding, 
                        entry.embedding
                    )
                    if similarity >= min_similarity:
                        results.append((entry, similarity))
            
            # 排序
            results.sort(key=lambda x: -x[1])
            
            return results[:top_k]
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return await self._keyword_search(query, top_k)
    
    async def _keyword_search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Tuple[MemoryEntry, float]]:
        """关键词搜索（备用）"""
        query_lower = query.lower()
        results = []
        
        for entry in self._memories.values():
            score = 0.0
            
            # 匹配键
            if query_lower in entry.key.lower():
                score += 0.5
            
            # 匹配值
            value_str = str(entry.value).lower()
            if query_lower in value_str:
                score += 0.3
            
            # 匹配标签
            for tag in entry.tags:
                if query_lower in tag.lower():
                    score += 0.2
            
            if score > 0:
                results.append((entry, score))
        
        results.sort(key=lambda x: -x[1])
        return results[:top_k]
    
    def _cosine_similarity(
        self, 
        a: List[float], 
        b: List[float]
    ) -> float:
        """计算余弦相似度"""
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def _value_to_text(self, value: Any) -> str:
        """将值转换为文本（用于嵌入）"""
        if isinstance(value, str):
            return value
        elif isinstance(value, (int, float, bool)):
            return str(value)
        elif isinstance(value, (list, tuple)):
            return " ".join(str(v) for v in value)
        elif isinstance(value, dict):
            return " ".join(f"{k}: {v}" for k, v in value.items())
        else:
            return str(value)
    
    async def _evict_memories(self) -> None:
        """清理记忆（基于重要性和时间）"""
        # 计算记忆分数
        scores = []
        current_time = time.time()
        
        for entry in self._memories.values():
            # 过期记忆优先清理
            if entry.is_expired():
                scores.append((entry.id, -1.0))
                continue
            
            # 计算分数：重要性 + 新鲜度 + 访问频率
            age = current_time - entry.created_at
            recency = 1.0 / (1.0 + age / 86400)  # 天为单位
            
            access_score = min(1.0, entry.access_count / 10)
            
            score = (
                entry.importance * 0.5 +
                recency * 0.3 +
                access_score * 0.2
            )
            
            scores.append((entry.id, score))
        
        # 排序并删除最低分的记忆
        scores.sort(key=lambda x: x[1])
        
        # 删除 10% 的记忆
        to_delete = max(1, int(len(scores) * 0.1))
        for i in range(to_delete):
            entry_id = scores[i][0]
            entry = self._memories.get(entry_id)
            if entry:
                await self.delete(entry.key)
        
        logger.info(f"Evicted {to_delete} memories")
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_memories": len(self._memories),
            "by_type": {
                t.value: len(ids) 
                for t, ids in self._type_index.items()
            },
            "by_tag": {
                tag: len(ids) 
                for tag, ids in self._tag_index.items()
            },
            "expired": sum(
                1 for e in self._memories.values() 
                if e.is_expired()
            ),
        }
    
    async def clear(self) -> None:
        """清空所有记忆"""
        self._memories.clear()
        self._key_index.clear()
        self._tag_index.clear()
        for t in self._type_index:
            self._type_index[t] = []
        logger.info("Cleared all memories")


__all__ = [
    "MemoryType",
    "MemoryEntry",
    "VectorMemoryStore",
]
