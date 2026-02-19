#!/usr/bin/env python3
"""
NeuroFlow 全量测试脚本
"""

import asyncio
import sys

print('='*60)
print('NeuroFlow 全量测试')
print('='*60)

# ========== Phase 1 测试 ==========
print('\n' + '='*60)
print('Phase 1 核心功能测试')
print('='*60)

async def test_phase1():
    from neuroflow import (
        AINativeAgent, LLMConfig,
        UnifiedToolRegistry, ToolDefinition, ToolParameter,
        ToolSource, LocalFunctionExecutor, ToolCall
    )
    
    tests_passed = 0
    tests_failed = 0
    
    # 测试 1: 工具注册表
    print('\n1. 测试工具注册表...')
    try:
        registry = UnifiedToolRegistry()
        executor = LocalFunctionExecutor()
        
        tool = ToolDefinition(
            id="test_add",
            name="add",
            description="Add two numbers",
            source=ToolSource.LOCAL_FUNCTION,
            parameters=[
                ToolParameter("a", "number", "First number", True),
                ToolParameter("b", "number", "Second number", True),
            ],
        )
        
        registry.register_tool(tool)
        registry.register_executor(ToolSource.LOCAL_FUNCTION, executor)
        
        async def add_func(a: int, b: int) -> int:
            return a + b
        
        executor.register_function(add_func, tool)
        
        call = ToolCall(
            tool_id="add",
            tool_name="add",
            arguments={"a": 10, "b": 20},
        )
        
        result = await registry.execute(call)
        
        if result.success and result.result == 30:
            print('  ✓ 工具注册表测试通过')
            tests_passed += 1
        else:
            print(f'  ✗ 工具执行失败')
            tests_failed += 1
    except Exception as e:
        print(f'  ✗ 工具注册表测试失败：{e}')
        tests_failed += 1
    
    # 测试 2: Agent 创建
    print('\n2. 测试 Agent 创建...')
    try:
        from neuroflow.agent import AINativeAgentConfig
        
        agent = AINativeAgent(
            AINativeAgentConfig(
                name="test_agent",
                description="Test Agent",
            )
        )
        
        @agent.tool(name="greet", description="Greet someone")
        async def greet(name: str) -> str:
            return f"Hello, {name}!"
        
        tools = agent.list_available_tools()
        if "greet" in tools:
            print('  ✓ Agent 创建测试通过')
            tests_passed += 1
        else:
            print('  ✗ Agent 工具注册失败')
            tests_failed += 1
    except Exception as e:
        print(f'  ✗ Agent 创建测试失败：{e}')
        tests_failed += 1
    
    # 测试 3: 记忆管理
    print('\n3. 测试记忆管理...')
    try:
        agent.store_memory("test_key", "test_value", tags=["test"])
        value = agent.retrieve_memory("test_key")
        
        if value == "test_value":
            print('  ✓ 记忆管理测试通过')
            tests_passed += 1
        else:
            print('  ✗ 记忆检索失败')
            tests_failed += 1
    except Exception as e:
        print(f'  ✗ 记忆管理测试失败：{e}')
        tests_failed += 1
    
    return tests_passed, tests_failed

phase1_results = asyncio.run(test_phase1())

# ========== Phase 3 测试 ==========
print('\n' + '='*60)
print('Phase 3 A2A/学习/记忆测试')
print('='*60)

async def test_phase3():
    from neuroflow import (
        AgentRegistry, AgentInfo, AgentCapability,
        VectorMemoryStore, MemoryType,
        SkillExample,
    )
    
    tests_passed = 0
    tests_failed = 0
    
    # 测试 1: Agent Registry
    print('\n1. 测试 Agent Registry...')
    try:
        registry = AgentRegistry()
        
        agent = AgentInfo(
            id="test-1",
            name="test_agent",
            description="Test Agent",
            capabilities=[AgentCapability.TEXT_GENERATION],
            endpoint="http://localhost:8080",
        )
        
        registry.register_agent(agent)
        agents = registry.list_agents()
        
        if len(agents) == 1:
            print('  ✓ Agent Registry 测试通过')
            tests_passed += 1
        else:
            print('  ✗ Agent Registry 失败')
            tests_failed += 1
    except Exception as e:
        print(f'  ✗ Agent Registry 测试失败：{e}')
        tests_failed += 1
    
    # 测试 2: Vector Memory Store
    print('\n2. 测试 Vector Memory Store...')
    try:
        store = VectorMemoryStore()
        
        await store.store(
            key="test_key",
            value="test_value",
            memory_type=MemoryType.SHORT_TERM,
            tags=["test"],
            importance=0.5,
        )
        
        value = await store.retrieve("test_key")
        
        if value == "test_value":
            print('  ✓ Vector Memory Store 测试通过')
            tests_passed += 1
        else:
            print('  ✗ Vector Memory Store 失败')
            tests_failed += 1
    except Exception as e:
        print(f'  ✗ Vector Memory Store 测试失败：{e}')
        tests_failed += 1
    
    return tests_passed, tests_failed

phase3_results = asyncio.run(test_phase3())

# ========== 汇总 ==========
print('\n' + '='*60)
print('测试汇总')
print('='*60)

total_passed = phase1_results[0] + phase3_results[0]
total_failed = phase1_results[1] + phase3_results[1]

print(f'\nPhase 1: {phase1_results[0]} 通过，{phase1_results[1]} 失败')
print(f'Phase 3: {phase3_results[0]} 通过，{phase3_results[1]} 失败')
print(f'\n总计：{total_passed} 通过，{total_failed} 失败')
print('='*60)

if total_failed == 0:
    print('\n✓ 所有测试通过!')
    sys.exit(0)
else:
    print(f'\n✗ {total_failed} 个测试失败')
    sys.exit(1)
