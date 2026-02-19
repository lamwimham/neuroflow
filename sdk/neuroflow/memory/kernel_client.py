"""
NeuroFlow Python SDK - Kernel Memory Client

gRPC client for calling Rust Kernel's Memory module.

Usage:
    from neuroflow.memory import KernelMemoryClient
    
    client = KernelMemoryClient(endpoint="localhost:50051")
    
    # Store memory
    await client.store(
        agent_id="agent-1",
        key="user_preference",
        value={"theme": "dark", "lang": "zh"},
        tags=["preference"],
        importance=0.9,
    )
    
    # Retrieve memory
    memory = await client.retrieve("agent-1", "user_preference")
    
    # Search memories
    memories = await client.search(
        agent_id="agent-1",
        tags=["conversation"],
        limit=10,
    )
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

import grpc

from ..proto import memory_pb2, memory_pb2_grpc

logger = logging.getLogger(__name__)


class KernelMemoryClient:
    """Kernel Memory 模块的 gRPC 客户端"""
    
    def __init__(self, endpoint: str = "localhost:50051"):
        self.endpoint = endpoint
        self.channel = grpc.insecure_channel(endpoint)
        self.stub = memory_pb2_grpc.MemoryServiceStub(self.channel)
        self.conv_stub = memory_pb2_grpc.ConversationMemoryServiceStub(self.channel)
    
    async def store(
        self,
        agent_id: str,
        key: str,
        value: Dict[str, Any],
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
        expiry: Optional[datetime] = None,
        memory_type: str = "general",
    ) -> str:
        """
        存储记忆到 Kernel
        
        Args:
            agent_id: Agent 标识
            key: 记忆键
            value: 记忆内容（字典）
            tags: 标签列表
            importance: 重要性 (0.0-1.0)
            expiry: 过期时间
            memory_type: 记忆类型
            
        Returns:
            记忆 ID
        """
        entry = memory_pb2.MemoryEntry(
            agent_id=agent_id,
            key=key,
            value=json.dumps(value),
            tags=tags or [],
            importance=importance,
            memory_type=memory_type,
        )
        
        if expiry:
            # 转换为 protobuf timestamp
            from google.protobuf.timestamp_pb2 import Timestamp
            ts = Timestamp()
            ts.FromDatetime(expiry)
            entry.expiry.CopyFrom(ts)
        
        request = memory_pb2.StoreRequest(entry=entry)
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.stub.Store(request)
            )
            
            if not response.success:
                raise Exception(f"Failed to store memory: {response.error}")
            
            logger.info(f"Stored memory: {response.memory_id}")
            return response.memory_id
            
        except grpc.RpcError as e:
            logger.error(f"gRPC error storing memory: {e}")
            raise
    
    async def retrieve(
        self,
        agent_id: str,
        key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        从 Kernel 检索记忆
        
        Args:
            agent_id: Agent 标识
            key: 记忆键
            
        Returns:
            记忆内容，如果不存在则返回 None
        """
        request = memory_pb2.RetrieveRequest(
            agent_id=agent_id,
            key=key,
        )
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.stub.Retrieve(request)
            )
            
            if not response.found:
                return None
            
            return {
                "id": response.entry.id,
                "key": response.entry.key,
                "value": json.loads(response.entry.value),
                "tags": list(response.entry.tags),
                "importance": response.entry.importance,
                "memory_type": response.entry.memory_type,
            }
            
        except grpc.RpcError as e:
            logger.error(f"gRPC error retrieving memory: {e}")
            raise
    
    async def delete(
        self,
        agent_id: str,
        key: str,
    ) -> bool:
        """删除记忆"""
        request = memory_pb2.DeleteRequest(
            agent_id=agent_id,
            key=key,
        )
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.stub.Delete(request)
            )
            return response.success
            
        except grpc.RpcError as e:
            logger.error(f"gRPC error deleting memory: {e}")
            return False
    
    async def search(
        self,
        agent_id: str,
        key_pattern: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_importance: float = 0.0,
        limit: int = 10,
        sort_by: str = "timestamp_desc",
    ) -> List[Dict[str, Any]]:
        """
        搜索记忆
        
        Args:
            agent_id: Agent 标识
            key_pattern: 键模式匹配
            tags: 标签过滤
            min_importance: 最小重要性
            limit: 返回数量限制
            sort_by: 排序方式
            
        Returns:
            记忆列表
        """
        sort_enum = {
            "timestamp_asc": memory_pb2.MemorySortBy.TIMESTAMP_ASC,
            "timestamp_desc": memory_pb2.MemorySortBy.TIMESTAMP_DESC,
            "importance_asc": memory_pb2.MemorySortBy.IMPORTANCE_ASC,
            "importance_desc": memory_pb2.MemorySortBy.IMPORTANCE_DESC,
        }
        
        query = memory_pb2.MemoryQuery(
            agent_id=agent_id,
            key_pattern=key_pattern or "",
            tags=tags or [],
            min_importance=min_importance,
            limit=limit,
            sort_by=sort_enum.get(sort_by, memory_pb2.MemorySortBy.TIMESTAMP_DESC),
        )
        
        try:
            request = memory_pb2.SearchRequest(query=query)
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.stub.Search(request)
            )
            
            return [
                {
                    "id": entry.id,
                    "key": entry.key,
                    "value": json.loads(entry.value),
                    "tags": list(entry.tags),
                    "importance": entry.importance,
                    "memory_type": entry.memory_type,
                }
                for entry in response.entries
            ]
            
        except grpc.RpcError as e:
            logger.error(f"gRPC error searching memories: {e}")
            raise
    
    async def semantic_search(
        self,
        agent_id: str,
        query_text: str,
        top_k: int = 5,
        min_similarity: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        语义搜索记忆
        
        Args:
            agent_id: Agent 标识
            query_text: 查询文本
            top_k: 返回数量
            min_similarity: 最小相似度
            
        Returns:
            记忆列表（带相似度分数）
        """
        query = memory_pb2.SemanticSearchQuery(
            agent_id=agent_id,
            query_text=query_text,
            top_k=top_k,
            min_similarity=min_similarity,
        )
        
        try:
            request = memory_pb2.SemanticSearchRequest(query=query)
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.stub.SemanticSearch(request)
            )
            
            return [
                {
                    "id": result.entry.id,
                    "key": result.entry.key,
                    "value": json.loads(result.entry.value),
                    "similarity": result.similarity_score,
                }
                for result in response.results
            ]
            
        except grpc.RpcError as e:
            logger.error(f"gRPC error semantic searching: {e}")
            raise
    
    # ========== 对话记忆专用方法 ==========
    
    async def save_conversation(
        self,
        agent_id: str,
        conversation_id: str,
        turns: List[Dict[str, Any]],
        context: Optional[Dict[str, str]] = None,
    ) -> int:
        """
        保存对话到 Kernel Memory
        
        Args:
            agent_id: Agent 标识
            conversation_id: 对话 ID
            turns: 对话轮次列表
                [{"role": "user", "content": "...", "timestamp": "..."}, ...]
            context: 上下文信息
            
        Returns:
            保存的轮次数
        """
        proto_turns = []
        for turn in turns:
            proto_turn = memory_pb2.ConversationTurn(
                role=turn.get("role", "user"),
                content=turn.get("content", ""),
            )
            
            if "timestamp" in turn:
                from google.protobuf.timestamp_pb2 import Timestamp
                ts = Timestamp()
                if isinstance(turn["timestamp"], datetime):
                    ts.FromDatetime(turn["timestamp"])
                else:
                    ts.FromJsonString(turn["timestamp"])
                proto_turn.timestamp.CopyFrom(ts)
            
            if "metadata" in turn:
                proto_turn.metadata.update(turn["metadata"])
            
            proto_turns.append(proto_turn)
        
        request = memory_pb2.SaveConversationRequest(
            agent_id=agent_id,
            conversation_id=conversation_id,
            turns=proto_turns,
            metadata=context or {},
        )
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.conv_stub.SaveConversation(request)
            )
            
            if not response.success:
                raise Exception(f"Failed to save conversation: {response.error}")
            
            logger.info(f"Saved {response.turns_saved} conversation turns")
            return response.turns_saved
            
        except grpc.RpcError as e:
            logger.error(f"gRPC error saving conversation: {e}")
            raise
    
    async def get_conversation_history(
        self,
        agent_id: str,
        conversation_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """获取对话历史"""
        request = memory_pb2.GetConversationHistoryRequest(
            agent_id=agent_id,
            conversation_id=conversation_id,
            limit=limit,
        )
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.conv_stub.GetConversationHistory(request)
            )
            
            return [
                {
                    "role": turn.role,
                    "content": turn.content,
                    "timestamp": turn.timestamp.ToJsonString() if turn.timestamp else None,
                    "metadata": dict(turn.metadata),
                }
                for turn in response.turns
            ]
            
        except grpc.RpcError as e:
            logger.error(f"gRPC error getting conversation history: {e}")
            raise
    
    async def extract_knowledge(
        self,
        agent_id: str,
        conversation_id: str,
        conversation_text: str,
        context: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        从对话中提取知识
        
        Args:
            agent_id: Agent 标识
            conversation_id: 对话 ID
            conversation_text: 完整对话文本
            context: 上下文信息
            
        Returns:
            提取的知识列表
        """
        request = memory_pb2.ExtractKnowledgeRequest(
            agent_id=agent_id,
            conversation_id=conversation_id,
            conversation_text=conversation_text,
            metadata=context or {},
        )
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.conv_stub.ExtractKnowledge(request)
            )
            
            return [
                {
                    "key": item.key,
                    "value": item.value,
                    "category": item.category,
                    "confidence": item.confidence,
                    "tags": list(item.tags),
                }
                for item in response.knowledge_items
            ]
            
        except grpc.RpcError as e:
            logger.error(f"gRPC error extracting knowledge: {e}")
            raise
    
    async def save_extracted_knowledge(
        self,
        agent_id: str,
        knowledge_items: List[Dict[str, Any]],
    ) -> List[str]:
        """
        保存提取的知识到 Memory
        
        Args:
            agent_id: Agent 标识
            knowledge_items: 知识列表
            
        Returns:
            保存的记忆 ID 列表
        """
        proto_items = []
        for knowledge in knowledge_items:
            proto_item = memory_pb2.ExtractedKnowledge(
                key=knowledge.get("key", ""),
                value=knowledge.get("value", ""),
                category=knowledge.get("category", "general"),
                confidence=knowledge.get("confidence", 0.5),
                tags=knowledge.get("tags", []),
            )
            proto_items.append(proto_item)
        
        request = memory_pb2.SaveExtractedKnowledgeRequest(
            agent_id=agent_id,
            knowledge_items=proto_items,
        )
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.conv_stub.SaveExtractedKnowledge(request)
            )
            
            if not response.success:
                raise Exception(f"Failed to save knowledge: {response.error}")
            
            logger.info(f"Saved {len(response.memory_ids)} knowledge items")
            return list(response.memory_ids)
            
        except grpc.RpcError as e:
            logger.error(f"gRPC error saving knowledge: {e}")
            raise


class ConversationMemoryManager:
    """
    对话记忆管理器 - 简化对话记忆的使用
    
    Usage:
        memory_mgr = ConversationMemoryManager(agent_id="agent-1")
        
        async with memory_mgr.conversation("conv-123") as conv:
            conv.add_user("Hello")
            response = await agent.chat("Hello")
            conv.add_assistant(response)
        
        # 自动保存到 Kernel Memory
    """
    
    def __init__(self, agent_id: str, client: Optional[KernelMemoryClient] = None):
        self.agent_id = agent_id
        self.client = client or KernelMemoryClient()
        self._current_conversation: Optional[ConversationContext] = None
    
    def conversation(self, conversation_id: str) -> "ConversationContext":
        """创建对话上下文"""
        return ConversationContext(self.client, self.agent_id, conversation_id)


class ConversationContext:
    """对话上下文管理器"""
    
    def __init__(self, client: KernelMemoryClient, agent_id: str, conversation_id: str):
        self.client = client
        self.agent_id = agent_id
        self.conversation_id = conversation_id
        self.turns: List[Dict[str, Any]] = []
    
    def add_user(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """添加用户消息"""
        self.turns.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now(),
            "metadata": metadata or {},
        })
    
    def add_assistant(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """添加 AI 回复"""
        self.turns.append({
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now(),
            "metadata": metadata or {},
        })
    
    async def __aenter__(self):
        """进入上下文"""
        # 加载历史对话
        history = await self.client.get_conversation_history(
            self.agent_id,
            self.conversation_id,
            limit=50,
        )
        self.turns = history
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文 - 自动保存"""
        if self.turns:
            await self.client.save_conversation(
                self.agent_id,
                self.conversation_id,
                self.turns,
            )


__all__ = [
    "KernelMemoryClient",
    "ConversationMemoryManager",
    "ConversationContext",
]
