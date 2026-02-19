"""
NeuroFlow Agent with Memory - 完整示例

演示如何在 Agent 对话过程中自动保存学到的知识到 Kernel Memory
"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime

from neuroflow import AINativeAgent, LLMConfig
from neuroflow.memory import KernelMemoryClient, ConversationMemoryManager


# ========== 场景 1: 基础记忆使用 ==========

async def example_basic_memory():
    """基础记忆使用示例"""
    print("\n=== 示例 1: 基础记忆使用 ===\n")
    
    # 创建 Agent
    agent = AINativeAgent(
        name="assistant",
        llm_config=LLMConfig(provider="openai", model="gpt-4"),
    )
    
    # 创建 Memory 客户端
    memory_client = KernelMemoryClient(endpoint="localhost:50051")
    
    # 1. 存储用户偏好
    await memory_client.store(
        agent_id="user-123",
        key="preference:theme",
        value={"theme": "dark", "language": "zh-CN"},
        tags=["preference", "ui"],
        importance=0.8,
    )
    
    # 2. 检索用户偏好
    preference = await memory_client.retrieve("user-123", "preference:theme")
    print(f"用户偏好：{preference}")
    
    # 3. 搜索相关记忆
    memories = await memory_client.search(
        agent_id="user-123",
        tags=["preference"],
        limit=10,
    )
    print(f"找到 {len(memories)} 条偏好记忆")


# ========== 场景 2: 对话记忆管理 ==========

async def example_conversation_memory():
    """对话记忆管理示例"""
    print("\n=== 示例 2: 对话记忆管理 ===\n")
    
    agent = AINativeAgent(
        name="assistant",
        llm_config=LLMConfig(provider="openai", model="gpt-4"),
    )
    
    memory_client = KernelMemoryClient(endpoint="localhost:50051")
    memory_mgr = ConversationMemoryManager(agent_id="user-123", client=memory_client)
    
    # 使用上下文管理器自动保存对话
    async with memory_mgr.conversation("conv-001") as conv:
        # 用户消息
        user_message = "我喜欢深色主题"
        conv.add_user(user_message)
        
        # AI 回复
        response = "好的，我已经记住了您喜欢深色主题。"
        conv.add_assistant(response)
        
        print(f"对话已保存到 Kernel Memory")
    
    # 加载历史对话
    history = await memory_client.get_conversation_history(
        agent_id="user-123",
        conversation_id="conv-001",
        limit=50,
    )
    
    print(f"历史对话轮数：{len(history)}")
    for turn in history:
        print(f"  {turn['role']}: {turn['content']}")


# ========== 场景 3: 从对话中提取知识 ==========

async def example_knowledge_extraction():
    """从对话中提取知识并保存"""
    print("\n=== 示例 3: 从对话中提取知识 ===\n")
    
    agent = AINativeAgent(
        name="assistant",
        llm_config=LLMConfig(provider="openai", model="gpt-4"),
    )
    
    memory_client = KernelMemoryClient(endpoint="localhost:50051")
    
    # 模拟一段对话
    conversation_text = """
    User: 我在北京工作
    Assistant: 北京是个好城市，您做什么工作？
    User: 我是软件工程师，主要做 Python 开发
    Assistant: 很棒！Python 是一门很流行的语言。
    User: 我平时喜欢用 Django 和 FastAPI 框架
    Assistant: 这些都是很好的框架选择。
    """
    
    # 1. 保存原始对话
    conversation_id = "conv-002"
    turns = [
        {"role": "user", "content": "我在北京工作"},
        {"role": "assistant", "content": "北京是个好城市，您做什么工作？"},
        {"role": "user", "content": "我是软件工程师，主要做 Python 开发"},
        {"role": "assistant", "content": "很棒！Python 是一门很流行的语言。"},
        {"role": "user", "content": "我平时喜欢用 Django 和 FastAPI 框架"},
        {"role": "assistant", "content": "这些都是很好的框架选择。"},
    ]
    
    await memory_client.save_conversation(
        agent_id="user-123",
        conversation_id=conversation_id,
        turns=turns,
    )
    
    # 2. 从对话中提取知识
    # 注意：这里应该调用 LLM 来提取，当前示例手动创建
    extracted_knowledge = [
        {
            "key": "user_location",
            "value": json.dumps({"city": "北京", "country": "中国"}),
            "category": "personal_info",
            "confidence": 0.95,
            "tags": ["location", "personal"],
        },
        {
            "key": "user_profession",
            "value": json.dumps({"role": "软件工程师", "languages": ["Python"]}),
            "category": "professional_info",
            "confidence": 0.98,
            "tags": ["profession", "skills"],
        },
        {
            "key": "user_tech_stack",
            "value": json.dumps({"frameworks": ["Django", "FastAPI"]}),
            "category": "technical_skills",
            "confidence": 0.95,
            "tags": ["technology", "frameworks"],
        },
    ]
    
    # 3. 保存提取的知识
    memory_ids = await memory_client.save_extracted_knowledge(
        agent_id="user-123",
        knowledge_items=extracted_knowledge,
    )
    
    print(f"保存了 {len(memory_ids)} 条知识:")
    for i, knowledge in enumerate(extracted_knowledge):
        print(f"  {i+1}. {knowledge['key']}: {knowledge['value']}")
    
    # 4. 搜索特定知识
    location_memories = await memory_client.search(
        agent_id="user-123",
        tags=["location"],
        min_importance=0.9,
    )
    
    print(f"\n找到 {len(location_memories)} 条位置相关记忆")


# ========== 场景 4: 完整的 Agent 对话流程 ==========

class AgentWithMemory:
    """带记忆功能的 Agent"""
    
    def __init__(self, agent_id: str, llm_config: LLMConfig):
        self.agent_id = agent_id
        self.agent = AINativeAgent(
            name="assistant",
            llm_config=llm_config,
        )
        self.memory = KernelMemoryClient(endpoint="localhost:50051")
        self.memory_mgr = ConversationMemoryManager(
            agent_id=agent_id,
            client=self.memory,
        )
    
    async def chat(self, conversation_id: str, user_message: str) -> str:
        """
        与 Agent 对话，自动保存对话和提取知识
        
        流程:
        1. 加载对话历史
        2. 检索相关记忆
        3. 生成回复
        4. 保存对话
        5. 提取并保存知识
        """
        # 1. 加载对话历史
        history = await self.memory.get_conversation_history(
            self.agent_id,
            conversation_id,
            limit=10,
        )
        
        # 2. 检索相关记忆（用户偏好、个人信息等）
        preferences = await self.memory.search(
            self.agent_id,
            tags=["preference"],
            limit=5,
        )
        
        personal_info = await self.memory.search(
            self.agent_id,
            tags=["personal_info"],
            limit=5,
        )
        
        # 构建上下文
        context_parts = []
        
        if preferences:
            context_parts.append("用户偏好:")
            for pref in preferences:
                context_parts.append(f"  - {pref['value']}")
        
        if personal_info:
            context_parts.append("\n个人信息:")
            for info in personal_info:
                context_parts.append(f"  - {info['value']}")
        
        context = "\n".join(context_parts)
        
        # 3. 生成回复（使用 LLM）
        messages = []
        
        # 添加系统消息（带上下文）
        if context:
            messages.append({
                "role": "system",
                "content": f"你是一个有帮助的助手。以下是用户的相关信息:\n{context}",
            })
        
        # 添加历史对话
        for turn in history[-5:]:  # 最近 5 轮
            messages.append(turn)
        
        # 添加当前消息
        messages.append({"role": "user", "content": user_message})
        
        # 调用 LLM
        response = await self.agent.llm.chat(messages=messages)
        response_text = response.content
        
        # 4. 保存对话
        async with self.memory_mgr.conversation(conversation_id) as conv:
            conv.add_user(user_message)
            conv.add_assistant(response_text)
        
        # 5. 提取并保存知识
        knowledge_items = await self._extract_knowledge_from_conversation(
            user_message,
            response_text,
        )
        
        if knowledge_items:
            await self.memory.save_extracted_knowledge(
                self.agent_id,
                knowledge_items,
            )
            print(f"从对话中提取了 {len(knowledge_items)} 条知识")
        
        return response_text
    
    async def _extract_knowledge_from_conversation(
        self,
        user_message: str,
        response: str,
    ) -> List[Dict[str, Any]]:
        """
        从对话中提取知识
        
        实际应该调用 LLM 来提取，这里简单示例
        """
        knowledge_items = []
        
        # 简单的关键词匹配示例
        if "喜欢" in user_message or "偏好" in user_message:
            knowledge_items.append({
                "key": f"preference:{datetime.now().timestamp()}",
                "value": json.dumps({"message": user_message}),
                "category": "preference",
                "confidence": 0.8,
                "tags": ["preference"],
            })
        
        if "我在" in user_message or "我是" in user_message:
            knowledge_items.append({
                "key": f"personal:{datetime.now().timestamp()}",
                "value": json.dumps({"message": user_message}),
                "category": "personal_info",
                "confidence": 0.9,
                "tags": ["personal_info"],
            })
        
        return knowledge_items


async def example_full_agent_chat():
    """完整 Agent 对话示例"""
    print("\n=== 示例 4: 完整 Agent 对话流程 ===\n")
    
    # 创建带记忆的 Agent
    agent = AgentWithMemory(
        agent_id="user-123",
        llm_config=LLMConfig(provider="openai", model="gpt-4"),
    )
    
    # 对话 1
    print("User: 我在北京工作")
    response1 = await agent.chat("conv-003", "我在北京工作")
    print(f"Assistant: {response1}\n")
    
    # 对话 2
    print("User: 我喜欢深色主题")
    response2 = await agent.chat("conv-003", "我喜欢深色主题")
    print(f"Assistant: {response2}\n")
    
    # 对话 3 - Agent 会使用之前学到的知识
    print("User: 推荐一个适合我的框架")
    response3 = await agent.chat("conv-003", "推荐一个适合我的框架")
    print(f"Assistant: {response3}\n")


# ========== 主函数 ==========

async def main():
    """运行所有示例"""
    print("="*60)
    print("NeuroFlow Agent Memory 使用示例")
    print("="*60)
    
    # 注意：这些示例需要 Kernel Memory 服务运行
    # 启动服务：cargo run --bin neuroflow-kernel
    
    try:
        # 示例 1: 基础记忆使用
        # await example_basic_memory()
        
        # 示例 2: 对话记忆管理
        # await example_conversation_memory()
        
        # 示例 3: 从对话中提取知识
        # await example_knowledge_extraction()
        
        # 示例 4: 完整 Agent 对话流程
        await example_full_agent_chat()
        
        print("\n" + "="*60)
        print("示例运行完成!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 示例运行失败：{e}")
        print("\n请确保 Kernel Memory 服务已启动:")
        print("  cd kernel && cargo run --bin neuroflow-kernel")


if __name__ == "__main__":
    asyncio.run(main())
