"""
Phase 3 高级功能示例

展示 Phase 3 新增的高级功能:
1. A2A 协作
2. 技能学习
3. 向量记忆

运行:
    python examples/ai_native/phase3_example.py
"""

import asyncio
import os
from neuroflow import (
    AINativeAgent, 
    LLMConfig,
    AgentRegistry,
    AgentInfo,
    AgentCapability,
    CollaborativeOrchestrator,
    SkillLearner,
    SkillExample,
    VectorMemoryStore,
    MemoryType,
)


async def demo_a2a_collaboration():
    """演示 A2A 协作"""
    print("\n" + "="*60)
    print("Phase 3 示例 1: A2A 协作")
    print("="*60 + "\n")
    
    # 创建 Agent 注册表
    registry = AgentRegistry()
    
    # 注册模拟 Agent
    registry.register_agent(AgentInfo(
        id="agent-1",
        name="data_analyst",
        description="数据分析专家",
        capabilities=[
            AgentCapability.DATA_ANALYSIS,
            AgentCapability.MATH,
        ],
        endpoint="http://localhost:8081/agent1",
        tools=["analyze", "calculate_stats"],
    ))
    
    registry.register_agent(AgentInfo(
        id="agent-2",
        name="visualizer",
        description="数据可视化专家",
        capabilities=[
            AgentCapability.IMAGE_PROCESSING,
            AgentCapability.DATA_ANALYSIS,
        ],
        endpoint="http://localhost:8082/agent2",
        tools=["create_chart", "generate_graph"],
    ))
    
    registry.register_agent(AgentInfo(
        id="agent-3",
        name="report_writer",
        description="报告撰写专家",
        capabilities=[
            AgentCapability.TEXT_GENERATION,
            AgentCapability.TRANSLATION,
        ],
        endpoint="http://localhost:8083/agent3",
        tools=["write_report", "summarize"],
    ))
    
    print(f"已注册 {len(registry.list_agents())} 个 Agent:")
    for agent in registry.list_agents():
        print(f"  - {agent.name}: {agent.description}")
        print(f"    能力：{[c.value for c in agent.capabilities]}")
    
    # 创建主 Agent
    main_agent = AINativeAgent(
        name="coordinator",
        description="协调员",
        llm_config=LLMConfig(
            provider="openai",
            model="gpt-4",
        ) if os.getenv("OPENAI_API_KEY") else None,
    )
    
    # 创建协作编排器
    collaborator = CollaborativeOrchestrator(
        llm_orchestrator=main_agent.orchestrator,
        agent_registry=registry,
    )
    
    if os.getenv("OPENAI_API_KEY"):
        # 分析协作需求
        plan = await collaborator.analyze_collaboration_need(
            "帮我分析这个数据集，生成可视化图表，并写一份报告"
        )
        
        print(f"\n协作计划:")
        print(f"  需要协作：{plan.needs_collaboration}")
        print(f"  目标 Agent: {[a.name for a in plan.target_agents]}")
        print(f"  任务：{plan.tasks}")
        print(f"  推理：{plan.reasoning}")
    else:
        print("\n⚠️  需要 OPENAI_API_KEY 才能运行完整示例")
        
        # 演示 Agent 选择
        best = await registry.select_best_agent(
            "分析销售数据",
            required_capabilities=[AgentCapability.DATA_ANALYSIS],
        )
        
        if best:
            print(f"\n为'分析销售数据'任务推荐 Agent: {best.name}")
    
    await registry.close()


async def demo_skill_learning():
    """演示技能学习"""
    print("\n" + "="*60)
    print("Phase 3 示例 2: 技能学习")
    print("="*60 + "\n")
    
    # 创建 LLM 客户端
    llm = LLMClient(
        LLMConfig(
            provider="openai",
            model="gpt-4",
        )
    ) if os.getenv("OPENAI_API_KEY") else None
    
    if not llm:
        print("⚠️  需要 OPENAI_API_KEY 才能运行技能学习示例")
        print("\n演示预定义技能学习流程...")
        
        # 模拟学习结果
        from neuroflow import LearnedSkill, ToolParameter
        
        skill = LearnedSkill(
            id="learned:morse",
            name="text_to_morse",
            description="将文本转换为摩尔斯电码",
            implementation_code="def text_to_morse(text):\n    morse = {...}\n    return ' '.join(morse.get(c, '') for c in text.upper())",
            parameters=[
                ToolParameter(
                    name="text",
                    parameter_type="string",
                    description="要转换的文本",
                    required=True,
                )
            ],
            return_type="string",
            confidence=0.95,
        )
        
        print(f"\n学习到的技能:")
        print(f"  名称：{skill.name}")
        print(f"  描述：{skill.description}")
        print(f"  参数：{[p.name for p in skill.parameters]}")
        print(f"  置信度：{skill.confidence}")
        return
    
    # 创建技能学习器
    learner = SkillLearner(llm)
    
    # 学习新技能
    print("正在学习新技能：将文本转换为摩尔斯电码...")
    
    skill = await learner.learn_skill(
        skill_description="将文本转换为摩尔斯电码",
        examples=[
            SkillExample(
                input={"text": "HELLO"},
                expected_output=".... . .-.. .-.. ---",
            ),
            SkillExample(
                input={"text": "HI"},
                expected_output=".... ..",
            ),
            SkillExample(
                input={"text": "SOS"},
                expected_output="... --- ...",
            ),
        ],
    )
    
    print(f"\n学习到的技能:")
    print(f"  名称：{skill.name}")
    print(f"  描述：{skill.description}")
    print(f"  参数：{[p.name for p in skill.parameters]}")
    print(f"  置信度：{skill.confidence}")
    print(f"  代码:\n{skill.implementation_code}")
    
    # 生成工具定义
    tool_def = await learner.generate_tool_definition(skill)
    print(f"\n工具定义:")
    print(f"  ID: {tool_def.id}")
    print(f"  来源：{tool_def.source.value}")
    
    # 验证技能
    print("\n验证技能...")
    validation = await learner.validate_skill(skill)
    print(f"  总计：{validation['total']} 测试")
    print(f"  通过：{validation['passed']} 测试")
    print(f"  成功率：{validation['success_rate']*100:.1f}%")


async def demo_vector_memory():
    """演示向量记忆"""
    print("\n" + "="*60)
    print("Phase 3 示例 3: 向量记忆")
    print("="*60 + "\n")
    
    # 创建向量记忆存储
    store = VectorMemoryStore(max_memories=100)
    
    # 存储记忆
    print("存储记忆...")
    
    await store.store(
        key="user_name",
        value="张三",
        memory_type=MemoryType.LONG_TERM,
        tags=["user", "profile"],
        importance=0.9,
    )
    
    await store.store(
        key="user_preference",
        value="喜欢简洁的回答，不喜欢冗长的解释",
        memory_type=MemoryType.LONG_TERM,
        tags=["user", "preference"],
        importance=0.8,
    )
    
    await store.store(
        key="project_info",
        value="NeuroFlow 是一个 AI Native Agent 框架",
        memory_type=MemoryType.SEMANTIC,
        tags=["project", "description"],
        importance=0.7,
    )
    
    await store.store(
        key="meeting_note",
        value="下周一上午 10 点开项目评审会",
        memory_type=MemoryType.EPISODIC,
        tags=["meeting", "schedule"],
        importance=0.6,
        ttl_seconds=86400 * 7,  # 7 天后过期
    )
    
    # 检索记忆
    print("\n检索记忆...")
    
    # 按键检索
    user_name = await store.retrieve("user_name")
    print(f"  user_name: {user_name}")
    
    # 按标签检索
    user_memories = await store.search_by_tags(["user"])
    print(f"\n用户相关记忆 ({len(user_memories)} 条):")
    for mem in user_memories:
        print(f"  - {mem.key}: {mem.value}")
    
    # 按类型检索
    long_term = await store.search_by_type(MemoryType.LONG_TERM)
    print(f"\n长期记忆 ({len(long_term)} 条):")
    for mem in long_term:
        print(f"  - {mem.key}: {mem.value}")
    
    # 语义检索（如果没有嵌入函数，使用关键词搜索）
    print("\n语义搜索：'用户喜欢什么？'")
    results = await store.semantic_search("用户喜欢什么？", top_k=2)
    for mem, score in results:
        print(f"  - {mem.key} (相似度：{score:.2f}): {mem.value}")
    
    # 获取统计信息
    stats = await store.get_stats()
    print(f"\n记忆统计:")
    print(f"  总记忆数：{stats['total_memories']}")
    print(f"  按类型：{stats['by_type']}")
    print(f"  按标签：{stats['by_tag']}")
    
    # 演示记忆清理
    print("\n添加更多记忆以触发清理...")
    for i in range(150):
        await store.store(
            key=f"temp_{i}",
            value=f"临时数据 {i}",
            memory_type=MemoryType.SHORT_TERM,
            importance=0.1,  # 低重要性
        )
    
    stats_after = await store.get_stats()
    print(f"清理后记忆数：{stats_after['total_memories']}")


async def main():
    """运行所有示例"""
    print("🚀 Phase 3 高级功能示例")
    print("="*60)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  未设置 OPENAI_API_KEY 环境变量")
        print("部分示例将使用模拟模式运行")
        print("="*60)
    
    try:
        await demo_a2a_collaboration()
    except Exception as e:
        print(f"A2A 协作示例失败：{e}")
    
    try:
        await demo_skill_learning()
    except Exception as e:
        print(f"技能学习示例失败：{e}")
    
    try:
        await demo_vector_memory()
    except Exception as e:
        print(f"向量记忆示例失败：{e}")
    
    print("\n" + "="*60)
    print("所有示例运行完成！")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
