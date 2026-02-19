"""
Test Real MCP Integration

Tests for the real MCP executor and server manager.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path

from neuroflow.mcp import (
    RealMCPExecutor,
    MCPServerManager,
    MCPHealthMonitor,
    RetryConfig,
)
from neuroflow.mcp.config_parser import MCPConfigParser


class TestRealMCPExecutor:
    """Test RealMCPExecutor"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.mark.asyncio
    async def test_filesystem_tool_execution(self, temp_dir):
        """Test filesystem tool execution"""
        executor = RealMCPExecutor()
        
        try:
            # Start filesystem server (using built-in implementation for testing)
            connection = await executor.start_server(
                name="test_filesystem",
                server_type="filesystem",
                command="echo",  # Placeholder - will use built-in
                args=["test"],
            )
            
            # Test write_file
            test_file = os.path.join(temp_dir, "test.txt")
            result = await executor.execute_tool(
                server_name="test_filesystem",
                tool_name="write_file",
                arguments={"path": test_file, "content": "Hello, World!"},
            )
            
            assert result["success"] is True
            assert Path(test_file).exists()
            assert Path(test_file).read_text() == "Hello, World!"
            
            # Test read_file
            result = await executor.execute_tool(
                server_name="test_filesystem",
                tool_name="read_file",
                arguments={"path": test_file},
            )
            
            assert result["success"] is True
            assert result["result"] == "Hello, World!"
            
            # Test list_directory
            result = await executor.execute_tool(
                server_name="test_filesystem",
                tool_name="list_directory",
                arguments={"path": temp_dir},
            )
            
            assert result["success"] is True
            assert len(result["result"]) > 0
            
        finally:
            await executor.stop_all()
    
    @pytest.mark.asyncio
    async def test_memory_tool_execution(self, temp_dir):
        """Test memory tool execution"""
        executor = RealMCPExecutor()
        db_path = os.path.join(temp_dir, "test_memory.db")
        
        try:
            # Start memory server
            connection = await executor.start_server(
                name="test_memory",
                server_type="memory",
                command="echo",
                args=["test"],
            )
            
            # Test create_memory
            result = await executor.execute_tool(
                server_name="test_memory",
                tool_name="create_memory",
                arguments={
                    "content": "Test memory content",
                    "tags": ["test", "demo"],
                    "db_path": db_path,
                },
            )
            
            assert result["success"] is True
            assert result["result"]["content"] == "Test memory content"
            assert result["result"]["tags"] == ["test", "demo"]
            
            # Test search_memories
            result = await executor.execute_tool(
                server_name="test_memory",
                tool_name="search_memories",
                arguments={
                    "query": "Test",
                    "db_path": db_path,
                },
            )
            
            assert result["success"] is True
            assert len(result["result"]) > 0
            assert result["result"][0]["content"] == "Test memory content"
            
        finally:
            await executor.stop_all()
    
    @pytest.mark.asyncio
    async def test_server_lifecycle(self):
        """Test server start/stop lifecycle"""
        executor = RealMCPExecutor()
        
        # Start server
        connection = await executor.start_server(
            name="test_server",
            server_type="filesystem",
            command="echo",
            args=["test"],
        )
        
        assert connection.server_name == "test_server"
        assert connection.server_type == "filesystem"
        
        # List servers
        servers = executor.list_servers()
        assert "test_server" in servers
        
        # Get connection
        conn = executor.get_connection("test_server")
        assert conn is not None
        
        # Stop server
        await executor.stop_server("test_server")
        
        servers = executor.list_servers()
        assert "test_server" not in servers


class TestMCPServerManager:
    """Test MCPServerManager with real executor"""
    
    @pytest.fixture
    def test_config(self, temp_dir):
        """Create a test MCP config"""
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
        return config_file
    
    @pytest.mark.asyncio
    async def test_server_manager_from_config(self, test_config):
        """Test server manager creation from config"""
        parser = MCPConfigParser()
        config = parser.parse_from_file(test_config)
        
        manager = MCPServerManager()
        await manager.start_from_config(config)
        
        # Check servers started
        statuses = manager.get_all_statuses()
        assert "filesystem" in statuses
        assert "memory" in statuses
        
        # Get tools
        tools = manager.get_tools("filesystem")
        assert len(tools) > 0
        
        # Execute tool
        result = await manager.execute_tool(
            server_name="filesystem",
            tool_name="write_file",
            arguments={
                "path": os.path.join(test_config, "test.txt"),
                "content": "Test",
            },
        )
        
        # Cleanup
        await manager.stop_all()


class TestMCPHealthMonitor:
    """Test MCP Health Monitor"""
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self):
        """Test health monitoring"""
        executor = RealMCPExecutor()
        monitor = MCPHealthMonitor(
            retry_config=RetryConfig(max_retries=2),
            check_interval_seconds=1,
        )
        
        try:
            # Start monitoring
            await monitor.start_monitoring(executor)
            
            # Start a server
            await executor.start_server(
                name="test_server",
                server_type="filesystem",
                command="echo",
                args=["test"],
            )
            
            # Wait for health check
            await asyncio.sleep(1.5)
            
            # Check health
            health = monitor.get_health("test_server")
            assert health is not None
            assert health.status.value in ["healthy", "unknown"]
            
            # Get statistics
            stats = monitor.get_statistics()
            assert stats["total_servers"] >= 1
            
        finally:
            await monitor.stop_monitoring()
            await executor.stop_all()
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff(self):
        """Test retry with exponential backoff"""
        executor = RealMCPExecutor()
        monitor = MCPHealthMonitor(
            retry_config=RetryConfig(
                max_retries=3,
                initial_delay_ms=10,
                max_delay_ms=100,
            ),
        )
        
        attempt_count = 0
        
        async def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Simulated failure")
            return "success"
        
        result = await monitor.execute_with_retry(
            failing_function,
            server_name="test",
        )
        
        assert result == "success"
        assert attempt_count == 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        """Test circuit breaker pattern"""
        monitor = MCPHealthMonitor(
            failure_threshold=3,
        )
        
        # Simulate failures
        for i in range(3):
            result = monitor._health_results.get("test_server")
            if result is None:
                from neuroflow.mcp.health_monitor import HealthCheckResult, HealthStatus
                result = monitor._health_results["test_server"] = HealthCheckResult(
                    server_name="test_server",
                    status=HealthStatus.UNHEALTHY,
                    error="Test failure",
                )
            result.consecutive_failures = i + 1
        
        # Circuit breaker should open
        assert monitor.is_circuit_breaker_open("test_server") is True
        
        # Requests should be rejected
        async def test_func():
            return "test"
        
        with pytest.raises(Exception):
            await monitor.execute_with_retry(
                test_func,
                server_name="test_server",
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
