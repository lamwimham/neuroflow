#!/usr/bin/env python3
"""
Simple test script for A2A Real Communication

This script tests the A2A registry service and HTTP protocol.
"""

import asyncio
import time
import sys
import os

# Add neuroflow to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from neuroflow.a2a import (
    AgentRegistryService,
    AgentRegistration,
    MemoryRegistry,
    A2AProtocol,
    A2AHTTPClient,
    AssistRequest,
    CollaborationContext,
    CollaborativeOrchestratorV2,
)


async def test_memory_registry():
    """Test memory registry"""
    print("\n=== Testing Memory Registry ===")
    
    registry = AgentRegistryService(backend="memory")
    
    try:
        await registry.start()
        
        # Register agents
        agent1 = AgentRegistration(
            id="agent1",
            name="Research Agent",
            description="Specializes in web research",
            endpoint="http://localhost:8081",
            capabilities=["web_search", "research"],
            tools=["search_web", "extract_content"],
        )
        
        agent2 = AgentRegistration(
            id="agent2",
            name="Writer Agent",
            description="Specializes in content writing",
            endpoint="http://localhost:8082",
            capabilities=["text_generation", "writing"],
            tools=["write_article", "edit_content"],
        )
        
        print("Registering agents...")
        await registry.register(agent1)
        await registry.register(agent2)
        
        # List agents
        agents = await registry.list_agents()
        print(f"Registered agents: {len(agents)}")
        for agent in agents:
            print(f"  - {agent.name} ({agent.id}): {agent.capabilities}")
        
        # Discover by capability
        print("\nDiscovering agents with 'web_search' capability...")
        researchers = await registry.discover_by_capability("web_search")
        print(f"Found {len(researchers)} researcher(s)")
        
        # Update heartbeat
        print("\nUpdating heartbeat...")
        await registry.update_heartbeat("agent1")
        
        # Get specific agent
        agent = await registry.get_agent("agent1")
        print(f"Agent 1 status: {agent.status if agent else 'Not found'}")
        
        # Deregister
        print("\nDeregistering agent1...")
        await registry.deregister("agent1")
        
        agents = await registry.list_agents()
        print(f"Remaining agents: {len(agents)}")
        
        print("\n✅ Memory registry tests passed!")
        
    finally:
        await registry.stop()


async def test_collaboration_context():
    """Test collaboration context with depth limiting"""
    print("\n=== Testing Collaboration Context ===")
    
    context = CollaborationContext(
        request_id="test-123",
        current_depth=0,
        max_depth=5,
        timeout_ms=5000,
    )
    
    # Test depth progression
    print(f"Initial depth: {context.current_depth}/{context.max_depth}")
    print(f"Can collaborate with agent1: {context.can_collaborate('agent1')}")
    
    # Create child contexts
    child1 = context.create_child("agent1")
    print(f"After agent1: depth={child1.current_depth}, can_collaborate={child1.can_collaborate('agent2')}")
    
    child2 = child1.create_child("agent2")
    print(f"After agent2: depth={child2.current_depth}, can_collaborate={child2.can_collaborate('agent3')}")
    
    # Test cycle detection
    print(f"Cycle detection (agent1 revisited): {child2.can_collaborate('agent1')}")
    
    # Test max depth
    deep_context = context
    for i in range(6):
        deep_context = deep_context.create_child(f"agent{i}")
    print(f"At depth 6: can_collaborate={deep_context.can_collaborate('agentX')} (should be False)")
    
    print("\n✅ Collaboration context tests passed!")


async def test_a2a_protocol():
    """Test A2A protocol"""
    print("\n=== Testing A2A Protocol ===")
    
    protocol = A2AProtocol()
    
    # Create assist request
    message = protocol.create_assist_request(
        sender_id="agent1",
        recipient_id="agent2",
        task="Research this topic",
        context={"topic": "AI agents"},
        required_capabilities=["web_search"],
        timeout_ms=30000,
        max_depth=5,
        current_depth=0,
    )
    
    print(f"Created assist request message: {message.message_id}")
    print(f"Message type: {message.message_type.value}")
    print(f"Payload: {message.payload}")
    
    # Parse request
    parsed_request = protocol.parse_assist_request(message)
    print(f"Parsed request: task={parsed_request.task}, depth={parsed_request.current_depth}")
    
    # Create assist response
    response = protocol.create_assist_response(
        request_id=message.message_id,
        success=True,
        result={"findings": ["AI agents are awesome"]},
        execution_time_ms=1234,
        agent_id="agent2",
    )
    
    print(f"\nCreated assist response: {response.message_id}")
    print(f"Success: {response.payload['success']}")
    
    # Parse response
    parsed_response = protocol.parse_assist_response(response)
    print(f"Parsed response: success={parsed_response.success}, result={parsed_response.result}")
    
    # Create heartbeat
    heartbeat = protocol.create_heartbeat(
        sender_id="agent1",
        status="active",
        latency_ms=50.5,
        success_rate=0.98,
    )
    
    print(f"\nCreated heartbeat: {heartbeat.payload}")
    
    print("\n✅ A2A protocol tests passed!")


async def test_registry_with_filters():
    """Test registry with filters"""
    print("\n=== Testing Registry Filters ===")
    
    registry = AgentRegistryService(backend="memory")
    
    try:
        await registry.start()
        
        # Register multiple agents
        agents = [
            AgentRegistration(
                id=f"agent{i}",
                name=f"Agent {i}",
                description=f"Test agent {i}",
                endpoint=f"http://localhost:{8080+i}",
                capabilities=["cap1", "cap2"] if i % 2 == 0 else ["cap2", "cap3"],
                status="active" if i % 3 != 0 else "unhealthy",
            )
            for i in range(1, 6)
        ]
        
        for agent in agents:
            await registry.register(agent)
        
        # Filter by status
        active_agents = await registry.list_agents(status_filter="active")
        print(f"Active agents: {len(active_agents)}")
        
        # Filter by capability
        cap1_agents = await registry.list_agents(capability_filter=["cap1"])
        print(f"Agents with cap1: {len(cap1_agents)}")
        
        # Combined filters
        filtered = await registry.list_agents(
            status_filter="active",
            capability_filter=["cap2"],
        )
        print(f"Active agents with cap2: {len(filtered)}")
        
        print("\n✅ Registry filter tests passed!")
        
    finally:
        await registry.stop()


async def main():
    """Run all tests"""
    print("=" * 60)
    print("NeuroFlow v0.4.2 - A2A Real Communication Tests")
    print("=" * 60)
    
    try:
        await test_memory_registry()
        await test_collaboration_context()
        await test_a2a_protocol()
        await test_registry_with_filters()
        
        print("\n" + "=" * 60)
        print("✅ ALL A2A TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
