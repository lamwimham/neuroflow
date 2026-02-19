import asyncio
import json
import logging
from typing import Dict, Any, Optional
from .agent import BaseAgent, tool_registry, tool
from .context import Context, set_context

logger = logging.getLogger(__name__)

class AgentWorker:
    """Agent工作进程，运行在沙箱内"""
    
    def __init__(self, agent_class: type):
        self.agent: BaseAgent = agent_class()
        self.running = False
        
    async def start(self):
        """启动工作进程"""
        self.running = True
        logger.info(f"Agent worker started for {self.agent.__class__.__name__}")
        
        # 注册所有工具
        self._register_tools()
        
        # 这里应该连接到Rust内核的gRPC服务
        # 暂时使用简单的循环来模拟
        while self.running:
            await asyncio.sleep(1)
            
    async def stop(self):
        """停止工作进程"""
        self.running = False
        logger.info("Agent worker stopped")
        
    def _register_tools(self):
        """注册Agent类中的所有工具方法"""
        # 注册Agent实例的方法
        for name in dir(self.agent):
            attr = getattr(self.agent, name)
            if callable(attr) and hasattr(attr, '_tool_metadata'):
                tool_registry.register(attr)
        
        # 注册类级别的工具函数
        for name, attr in vars(self.agent.__class__).items():
            if callable(attr) and hasattr(attr, '_tool_metadata'):
                tool_registry.register(attr)
                
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理来自内核的请求"""
        try:
            # 设置上下文
            context = Context(
                trace_id=request_data.get('trace_id', ''),
                user_id=request_data.get('user_id'),
                metadata=request_data.get('metadata', {})
            )
            set_context(context)
            
            # 调用Agent的handle方法
            result = await self.agent.handle(request_data.get('payload', {}))
            
            return {
                'success': True,
                'data': result,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
            
    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具函数"""
        try:
            tool_func = tool_registry.get_tool(tool_name)
            if not tool_func:
                raise ValueError(f"Tool {tool_name} not found")
                
            result = await tool_func(**args)
            
            return {
                'success': True,
                'data': result,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }

# 示例Agent实现
class ExampleAgent(BaseAgent):
    """示例Agent"""
    
    async def handle(self, request: Dict[str, Any], context: Context) -> Dict[str, Any]:
        """处理请求"""
        logger.info(f"Handling request: {request}")
        logger.info(f"Context: {context}")
        
        # 模拟一些处理逻辑
        message = request.get('message', 'Hello')
        response = {
            'message': f"Echo: {message}",
            'agent': self.metadata.name if self.metadata else 'unknown',
            'trace_id': context.trace_id
        }
        
        return response
        
    @tool(name="add", description="Add two numbers")
    async def add_tool(self, a: int, b: int) -> int:
        """加法工具"""
        return a + b
        
    @tool(name="multiply", description="Multiply two numbers")
    async def multiply_tool(self, a: int, b: int) -> int:
        """乘法工具"""
        return a * b

if __name__ == "__main__":
    # 简单的测试
    logging.basicConfig(level=logging.INFO)
    
    async def test_worker():
        worker = AgentWorker(ExampleAgent)
        result = await worker.handle_request({
            'trace_id': 'test-123',
            'payload': {'message': 'Hello World'}
        })
        print(f"Result: {result}")
        
    asyncio.run(test_worker())