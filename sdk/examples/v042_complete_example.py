#!/usr/bin/env python3
"""
NeuroFlow v0.4.2 - Complete Example

This example demonstrates:
1. Real MCP integration with filesystem and memory servers
2. A2A communication with agent registry
3. Multi-agent collaboration with depth limiting
4. Health monitoring and circuit breaker

Run this example:
    python examples/v042_complete_example.py
"""

import asyncio
import tempfile
import os
import sys
from pathlib import Path

# Add neuroflow to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from neuroflow.mcp import (
    RealMCPExecutor,
    MCPServerManager,
    MCPHealthMonitor,
    RetryConfig,
)
from neuroflow.a2a import (
    AgentRegistryService,
    AgentRegistration,
    CollaborativeOrchestratorV2,
    CollaborationContext,
)
from neuroflow.orchestrator import LLMOrchestrator, LLMConfig


async def demo_mcp_integration():
    """Demonstrate real MCP integration"""
    print("\n" + "="*60)
    print("Demo 1: Real MCP Integration")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create MCP server manager
        manager = MCPServerManager()
        
        # Create config for filesystem and memory servers
        from neuroflow.mcp.config_parser import MCPConfig, MCPServerConfig
        
        config = MCPConfig(
            enabled=True,
            servers=[
                MCPServerConfig(
                    name="filesystem",
                    enabled=True,
                    config={
                        "allowed_paths": [temp_dir],
                    },
                ),
                MCPServerConfig(
                    name="memory",
                    enabled=True,
                    config={
                        "db_path": os.path.join(temp_dir, "memory.db"),
                    },
                ),
            ],
        )
        
        print("\n1. Starting MCP servers...")
        await manager.start_from_config(config)
        
        # Check server status
        print("\n2. Server status:")
        statuses = manager.get_all_statuses()
        for name, status in statuses.items():
            icon = "✅" if status.connected else "❌"
            print(f"   {icon} {name}: connected={status.connected}, tools={status.tools}")
        
        # Execute filesystem tools
        print("\n3. Executing filesystem tools...")
        test_file = os.path.join(temp_dir, "demo.txt")
        
        # Write file
        result = await manager.execute_tool(
            server_name="filesystem",
            tool_name="write_file",
            arguments={"path": test_file, "content": "Hello from NeuroFlow v0.4.2!"},
        )
        print(f"   Write result: {result['success']}")
        
        # Read file
        result = await manager.execute_tool(
            server_name="filesystem",
            tool_name="read_file",
            arguments={"path": test_file},
        )
        print(f"   Read result: {result['success']}, content: {result.get('result', '')}")
        
        # Execute memory tools
        print("\n4. Executing memory tools...")
        db_path = os.path.join(temp_dir, "memory.db")
        
        # Create memory
        result = await manager.execute_tool(
            server_name="memory",
            tool_name="create_memory",
            arguments={
                "content": "NeuroFlow v0.4.2 is awesome!",
                "tags": ["demo", "v0.4.2"],
                "db_path": db_path,
            },
        )
        print(f"   Create memory result: {result['success']}, ID: {result.get('result', {}).get('id')}")
        
        # Search memories
        result = await manager.execute_tool(
            server_name="memory",
            tool_name="search_memories",
            arguments={
                "query": "NeuroFlow",
                "db_path": db_path,
            },
        )
        print(f"   Search result: {result['success']}, found {len(result.get('result', []))} memories")
        
        # Cleanup
        print("\n5. Stopping MCP servers...")
        await manager.stop_all()
        
        print("\n✅ MCP integration demo completed!")


async def demo_a2a_communication():
    """Demonstrate A2A communication"""
    print("\n" + "="*60)
    print("Demo 2: A2A Communication")
    print("="*60)
    
    # Create registry service
    registry = AgentRegistryService(backend="memory")
    
    try:
        print("\n1. Starting agent registry...")
        await registry.start()
        
        # Register agents
        print("\n2. Registering agents...")
        
        researcher = AgentRegistration(
            id="researcher",
            name="Research Agent",
            description="Specializes in web research and information gathering",
            endpoint="http://localhost:8081",
            capabilities=["web_search", "research", "data_collection"],
            tools=["search_web", "extract_content", "summarize"],
        )
        
        writer = AgentRegistration(
            id="writer",
            name="Writer Agent",
            description="Specializes in content creation and writing",
            endpoint="http://localhost:8082",
            capabilities=["text_generation", "writing", "editing"],
            tools=["write_article", "edit_content", "proofread"],
        )
        
        analyst = AgentRegistration(
            id="analyst",
            name="Data Analyst Agent",
            description="Specializes in data analysis and visualization",
            endpoint="http://localhost:8083",
            capabilities=["data_analysis", "visualization", "statistics"],
            tools=["analyze_data", "create_chart", "generate_report"],
        )
        
        await registry.register(researcher)
        await registry.register(writer)
        await registry.register(analyst)
        
        print(f"   Registered {len(await registry.list_agents())} agents")
        
        # Discover agents by capability
        print("\n3. Discovering agents by capability...")
        
        researchers = await registry.discover_by_capability("web_search")
        print(f"   Found {len(researchers)} researcher(s)")
        
        writers = await registry.discover_by_capability("text_generation")
        print(f"   Found {len(writers)} writer(s)")
        
        # List all active agents
        print("\n4. Listing all active agents...")
        agents = await registry.list_agents(status_filter="active")
        for agent in agents:
            print(f"   - {agent.name}: {agent.capabilities}")
        
        # Update heartbeat
        print("\n5. Updating heartbeat...")
        await registry.update_heartbeat("researcher")
        
        # Get agent details
        agent = await registry.get_agent("researcher")
        print(f"   Researcher status: {agent.status}")
        
        # Deregister an agent
        print("\n6. Deregistering analyst agent...")
        await registry.deregister("analyst")
        
        agents = await registry.list_agents()
        print(f"   Remaining agents: {len(agents)}")
        
        print("\n✅ A2A communication demo completed!")
        
    finally:
        await registry.stop()


async def demo_collaboration_context():
    """Demonstrate collaboration context with depth limiting"""
    print("\n" + "="*60)
    print("Demo 3: Collaboration Context & Depth Limiting")
    print("="*60)
    
    # Create collaboration context
    context = CollaborationContext(
        request_id="demo-request-001",
        current_depth=0,
        max_depth=5,
        timeout_ms=10000,
    )
    
    print("\n1. Initial context:")
    print(f"   Depth: {context.current_depth}/{context.max_depth}")
    print(f"   Can collaborate: {context.can_collaborate('agent1')}")
    
    # Simulate collaboration chain
    print("\n2. Simulating collaboration chain...")
    
    current_context = context
    for i in range(1, 7):
        agent_id = f"agent{i}"
        can_collab = current_context.can_collaborate(agent_id)
        print(f"   Step {i}: agent{agent_id}, depth={current_context.current_depth}, can_collaborate={can_collab}")
        
        if can_collab:
            current_context = current_context.create_child(agent_id)
        else:
            print(f"   ⚠️ Collaboration stopped at depth {current_context.current_depth}")
            break
    
    # Test cycle detection
    print("\n3. Testing cycle detection...")
    context2 = CollaborationContext(
        request_id="demo-request-002",
        current_depth=0,
        max_depth=5,
        visited_agents=["agent1", "agent2"],
    )
    
    print(f"   Can collaborate with agent3: {context2.can_collaborate('agent3')}")
    print(f"   Can collaborate with agent1 (cycle): {context2.can_collaborate('agent1')}")
    
    print("\n✅ Collaboration context demo completed!")


async def demo_health_monitoring():
    """Demonstrate health monitoring"""
    print("\n" + "="*60)
    print("Demo 4: Health Monitoring & Circuit Breaker")
    print("="*60)
    
    from neuroflow.mcp.health_monitor import MCPHealthMonitor, HealthStatus, RetryConfig
    
    # Create executor and monitor
    executor = RealMCPExecutor()
    monitor = MCPHealthMonitor(
        retry_config=RetryConfig(
            max_retries=3,
            initial_delay_ms=100,
            max_delay_ms=2000,
        ),
        check_interval_seconds=5,
        failure_threshold=3,
    )
    
    try:
        print("\n1. Starting health monitoring...")
        await monitor.start_monitoring(executor)
        
        # Start a server
        print("\n2. Starting filesystem server...")
        await executor.start_server(
            name="demo_fs",
            server_type="filesystem",
            command="echo",
            args=["test"],
        )
        
        # Check health
        print("\n3. Checking server health...")
        await asyncio.sleep(1)  # Wait for health check
        
        health = monitor.get_health("demo_fs")
        if health:
            print(f"   Status: {health.status.value}")
            print(f"   Latency: {health.latency_ms:.2f}ms")
            print(f"   Consecutive failures: {health.consecutive_failures}")
        
        # Get statistics
        print("\n4. Health monitoring statistics:")
        stats = monitor.get_statistics()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Test retry logic
        print("\n5. Testing retry with exponential backoff...")
        
        attempt_count = 0
        
        async def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("Simulated failure")
            return "success"
        
        result = await monitor.execute_with_retry(
            flaky_function,
            server_name="demo_fs",
        )
        
        print(f"   Result after {attempt_count} attempts: {result}")
        
        print("\n✅ Health monitoring demo completed!")
        
    finally:
        await monitor.stop_monitoring()
        await executor.stop_all()


async def main():
    """Run all demos"""
    print("\n" + "="*70)
    print(" " * 15 + "NeuroFlow v0.4.2 Feature Demos")
    print("="*70)
    
    try:
        # Run demos
        await demo_mcp_integration()
        await demo_a2a_communication()
        await demo_collaboration_context()
        await demo_health_monitoring()
        
        print("\n" + "="*70)
        print(" " * 20 + "✅ ALL DEMOS COMPLETED!")
        print("="*70)
        print("\nKey Features Demonstrated:")
        print("  1. ✅ Real MCP integration with official SDK")
        print("  2. ✅ A2A communication with agent registry")
        print("  3. ✅ Collaboration depth limiting and cycle detection")
        print("  4. ✅ Health monitoring with circuit breaker")
        print("\nFor more information, see:")
        print("  - docs/RELEASE_NOTES_v0.4.2.md")
        print("  - sdk/examples/")
        print("="*70 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ DEMO FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
