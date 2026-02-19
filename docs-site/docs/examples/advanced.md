# 进阶示例

NeuroFlow 进阶使用示例。

## 多 Agent 协作

```python
import asyncio
from neuroflow import AINativeAgent, AINativeAgentConfig

# 创建多个专业 Agent
research_agent = AINativeAgent(
    AINativeAgentConfig(name="researcher", description="研究专家")
)

analysis_agent = AINativeAgent(
    AINativeAgentConfig(name="analyst", description="数据分析专家")
)

writing_agent = AINativeAgent(
    AINativeAgentConfig(name="writer", description="内容创作专家")
)

# 协作工作流
async def collaborative_research(topic):
    # 研究
    research_result = await research_agent.handle(f"研究主题：{topic}")
    
    # 分析
    analysis_result = await analysis_agent.handle(
        f"分析研究结果：{research_result['response']}"
    )
    
    # 写作
    final_result = await writing_agent.handle(
        f"根据分析结果撰写报告：{analysis_result['response']}"
    )
    
    return final_result

# 运行
result = await collaborative_research("AI 发展趋势")
print(result["response"])
```

## 工具链

```python
from neuroflow import AINativeAgent

agent = AINativeAgent(
    AINativeAgentConfig(name="data_processor")
)

# 创建工具链
@agent.tool(name="fetch_data", description="获取数据")
async def fetch_data(source: str) -> dict:
    return {"data": [1, 2, 3, 4, 5]}

@agent.tool(name="process_data", description="处理数据")
async def process_data(data: list) -> dict:
    return {"processed": [x * 2 for x in data]}

@agent.tool(name="visualize_data", description="可视化数据")
async def visualize_data(processed: list) -> str:
    return f"Chart: {processed}"

# 工具链执行
async def data_pipeline():
    data = await agent.execute_tool("fetch_data", source="api")
    processed = await agent.execute_tool("process_data", data=data["data"])
    chart = await agent.execute_tool("visualize_data", processed=processed["processed"])
    return chart
```

## 记忆增强

```python
from neuroflow import AINativeAgent, MemoryType

agent = AINativeAgent(
    AINativeAgentConfig(name="memory_agent")
)

# 存储长期记忆
agent.store_memory(
    key="user_preference",
    value="喜欢简洁的回答",
    memory_type=MemoryType.LONG_TERM,
    tags=["user", "preference"],
    importance=0.9,
)

# 存储短期记忆
agent.store_memory(
    key="current_task",
    value="处理数据",
    memory_type=MemoryType.SHORT_TERM,
    tags=["task"],
)

# 检索记忆
preference = agent.retrieve_memory("user_preference")

# 搜索记忆
user_memories = agent.search_memories(tags=["user"])

# 在对话中使用记忆
async def personalized_response(user_message):
    preference = agent.retrieve_memory("user_preference")
    
    if preference and "简洁" in preference:
        prompt = f"请简洁回答：{user_message}"
    else:
        prompt = f"请详细回答：{user_message}"
    
    return await agent.handle(prompt)
```

## 技能学习

```python
from neuroflow import SkillLearner, SkillExample, LLMClient, LLMConfig

# 创建学习器
llm = LLMClient(LLMConfig(provider="openai", model="gpt-4"))
learner = SkillLearner(llm)

# 学习新技能
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
    ],
)

# 验证技能
validation = await learner.validate_skill(skill)
print(f"成功率：{validation['success_rate']*100:.1f}%")

# 注册为工具
tool_def = await learner.generate_tool_definition(skill)
agent.tool_registry.register_tool(tool_def)
```

## A2A 协作

```python
from neuroflow import (
    AgentRegistry,
    AgentInfo,
    AgentCapability,
    CollaborativeOrchestrator,
)

# 创建 Agent 注册表
registry = AgentRegistry()

# 注册 Agent
registry.register_agent(
    AgentInfo(
        id="agent-1",
        name="data_analyst",
        description="数据分析专家",
        capabilities=[AgentCapability.DATA_ANALYSIS],
        endpoint="http://localhost:8081/agent1",
    )
)

registry.register_agent(
    AgentInfo(
        id="agent-2",
        name="report_writer",
        description="报告撰写专家",
        capabilities=[AgentCapability.TEXT_GENERATION],
        endpoint="http://localhost:8082/agent2",
    )
)

# 创建协作编排器
collaborator = CollaborativeOrchestrator(
    llm_orchestrator=agent.orchestrator,
    agent_registry=registry,
)

# 执行协作任务
result = await collaborator.execute_with_collaboration(
    "分析销售数据并生成报告"
)

print(f"协作结果：{result.response}")
print(f"参与 Agent: {result.collaborating_agents}")
```

---

**相关文档**: [基础示例](basic.md) | [构建 Agent](../guides/building-agents.md)
