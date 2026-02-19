#!/usr/bin/env python3
"""
Simple test script for Real MCP Integration

This script tests the basic functionality without requiring pytest.
"""

import asyncio
import tempfile
import os
import sys
from pathlib import Path

# Add neuroflow to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from neuroflow.mcp import RealMCPExecutor, MCPServerManager


async def test_filesystem_executor():
    """Test filesystem executor"""
    print("\n=== Testing RealMCPExecutor (Filesystem) ===")
    
    executor = RealMCPExecutor()
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Start filesystem server
            print("Starting filesystem server...")
            connection = await executor.start_server(
                name="test_fs",
                server_type="filesystem",
                command="echo",
                args=["test"],
            )
            
            print(f"Connection status: {connection.connected}")
            print(f"Tools available: {[t.name for t in connection.tools]}")
            
            # Test write_file
            test_file = os.path.join(temp_dir, "test.txt")
            print(f"\nWriting to {test_file}...")
            result = await executor.execute_tool(
                server_name="test_fs",
                tool_name="write_file",
                arguments={"path": test_file, "content": "Hello, World!"},
            )
            
            print(f"Write result: {result['success']} - {result.get('result', result.get('error', ''))}")
            assert result["success"], f"Write failed: {result.get('error')}"
            
            # Test read_file
            print(f"\nReading from {test_file}...")
            result = await executor.execute_tool(
                server_name="test_fs",
                tool_name="read_file",
                arguments={"path": test_file},
            )
            
            print(f"Read result: {result['success']} - Content: {result.get('result', '')}")
            assert result["success"], f"Read failed: {result.get('error')}"
            assert result["result"] == "Hello, World!", f"Content mismatch: {result['result']}"
            
            # Test list_directory
            print(f"\nListing directory {temp_dir}...")
            result = await executor.execute_tool(
                server_name="test_fs",
                tool_name="list_directory",
                arguments={"path": temp_dir},
            )
            
            print(f"List result: {result['success']} - Items: {len(result.get('result', []))}")
            assert result["success"], f"List failed: {result.get('error')}"
            
            print("\n✅ Filesystem tests passed!")
            
    finally:
        await executor.stop_all()
        print("Executor stopped")


async def test_memory_executor():
    """Test memory executor"""
    print("\n=== Testing RealMCPExecutor (Memory) ===")
    
    executor = RealMCPExecutor()
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            
            # Start memory server
            print("Starting memory server...")
            connection = await executor.start_server(
                name="test_mem",
                server_type="memory",
                command="echo",
                args=["test"],
            )
            
            print(f"Connection status: {connection.connected}")
            print(f"Tools available: {[t.name for t in connection.tools]}")
            
            # Test create_memory
            print("\nCreating memory...")
            result = await executor.execute_tool(
                server_name="test_mem",
                tool_name="create_memory",
                arguments={
                    "content": "Test memory content",
                    "tags": ["test", "demo"],
                    "db_path": db_path,
                },
            )
            
            print(f"Create result: {result['success']} - ID: {result.get('result', {}).get('id', 'N/A')}")
            assert result["success"], f"Create failed: {result.get('error')}"
            
            # Test search_memories
            print("\nSearching memories...")
            result = await executor.execute_tool(
                server_name="test_mem",
                tool_name="search_memories",
                arguments={
                    "query": "Test",
                    "db_path": db_path,
                },
            )
            
            print(f"Search result: {result['success']} - Found: {len(result.get('result', []))} items")
            assert result["success"], f"Search failed: {result.get('error')}"
            assert len(result["result"]) > 0, "No memories found"
            
            print("\n✅ Memory tests passed!")
            
    finally:
        await executor.stop_all()
        print("Executor stopped")


async def test_server_manager():
    """Test server manager"""
    print("\n=== Testing MCPServerManager ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create config
        config_content = f"""
mcp:
  enabled: true
  servers:
    - name: filesystem
      type: filesystem
      enabled: true
      config:
        allowed_paths:
          - {temp_dir}
    - name: memory
      type: memory
      enabled: true
      config:
        db_path: {os.path.join(temp_dir, 'test.db')}
"""
        config_file = os.path.join(temp_dir, "mcp_config.yaml")
        Path(config_file).write_text(config_content)
        
        from neuroflow.mcp.config_parser import MCPConfigParser
        
        parser = MCPConfigParser()
        config = parser.parse_from_file(config_file)
        
        manager = MCPServerManager()
        
        try:
            print("Starting servers from config...")
            await manager.start_from_config(config)
            
            # Check status
            statuses = manager.get_all_statuses()
            print(f"\nServer statuses:")
            for name, status in statuses.items():
                icon = "✅" if status.connected else "❌"
                print(f"  {icon} {name}: connected={status.connected}, tools={status.tools}")
            
            # Get tools
            tools = manager.get_tools("filesystem")
            print(f"\nFilesystem tools: {tools}")
            
            # Execute tool
            test_file = os.path.join(temp_dir, "manager_test.txt")
            print(f"\nWriting to {test_file}...")
            result = await manager.execute_tool(
                server_name="filesystem",
                tool_name="write_file",
                arguments={"path": test_file, "content": "Test via manager"},
            )
            
            print(f"Result: {result['success']} - {result.get('result', result.get('error', ''))}")
            
            print("\n✅ Server manager tests passed!")
            
        finally:
            await manager.stop_all()
            print("Manager stopped")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("NeuroFlow v0.4.2 - Real MCP Integration Tests")
    print("=" * 60)
    
    try:
        await test_filesystem_executor()
        await test_memory_executor()
        await test_server_manager()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
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
