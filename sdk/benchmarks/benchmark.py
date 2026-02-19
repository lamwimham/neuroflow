"""
NeuroFlow Python SDK - Performance Benchmarks

性能基准测试框架
"""

import asyncio
import time
import statistics
from typing import Callable, Dict, Any, List
from dataclasses import dataclass, field
import json


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    median_time_ms: float
    std_dev_ms: float
    p95_time_ms: float
    p99_time_ms: float
    success_rate: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time_ms": self.total_time_ms,
            "avg_time_ms": self.avg_time_ms,
            "min_time_ms": self.min_time_ms,
            "max_time_ms": self.max_time_ms,
            "median_time_ms": self.median_time_ms,
            "std_dev_ms": self.std_dev_ms,
            "p95_time_ms": self.p95_time_ms,
            "p99_time_ms": self.p99_time_ms,
            "success_rate": self.success_rate,
            "metadata": self.metadata,
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"Benchmark: {self.name}\n"
            f"  Iterations: {self.iterations}\n"
            f"  Avg: {self.avg_time_ms:.2f}ms\n"
            f"  Min: {self.min_time_ms:.2f}ms\n"
            f"  Max: {self.max_time_ms:.2f}ms\n"
            f"  Median: {self.median_time_ms:.2f}ms\n"
            f"  P95: {self.p95_time_ms:.2f}ms\n"
            f"  P99: {self.p99_time_ms:.2f}ms\n"
            f"  Std Dev: {self.std_dev_ms:.2f}ms\n"
            f"  Success Rate: {self.success_rate*100:.1f}%"
        )


class Benchmark:
    """
    基准测试类
    
    用法:
        benchmark = Benchmark("tool_execution")
        
        async def test_func():
            return await some_function()
        
        result = await benchmark.run(test_func, iterations=100)
        print(result)
    """
    
    def __init__(self, name: str, warmup_iterations: int = 10):
        self.name = name
        self.warmup_iterations = warmup_iterations
    
    async def run(
        self,
        test_func: Callable,
        iterations: int = 100,
        **kwargs,
    ) -> BenchmarkResult:
        """
        运行基准测试
        
        Args:
            test_func: 测试函数
            iterations: 迭代次数
            **kwargs: 传递给测试函数的参数
            
        Returns:
            基准测试结果
        """
        # 预热
        for _ in range(self.warmup_iterations):
            try:
                await test_func(**kwargs)
            except Exception:
                pass
        
        # 正式测试
        times = []
        successes = 0
        errors = []
        
        for i in range(iterations):
            start = time.perf_counter()
            try:
                await test_func(**kwargs)
                successes += 1
            except Exception as e:
                errors.append(str(e))
            
            end = time.perf_counter()
            times.append((end - start) * 1000)  # 转换为毫秒
        
        # 计算统计
        return self._calculate_result(times, successes, iterations)
    
    def _calculate_result(
        self,
        times: List[float],
        successes: int,
        iterations: int,
    ) -> BenchmarkResult:
        """计算统计结果"""
        if not times:
            return BenchmarkResult(
                name=self.name,
                iterations=iterations,
                total_time_ms=0,
                avg_time_ms=0,
                min_time_ms=0,
                max_time_ms=0,
                median_time_ms=0,
                std_dev_ms=0,
                p95_time_ms=0,
                p99_time_ms=0,
                success_rate=0,
            )
        
        sorted_times = sorted(times)
        
        return BenchmarkResult(
            name=self.name,
            iterations=iterations,
            total_time_ms=sum(times),
            avg_time_ms=statistics.mean(times),
            min_time_ms=min(times),
            max_time_ms=max(times),
            median_time_ms=statistics.median(times),
            std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
            p95_time_ms=sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 0 else 0,
            p99_time_ms=sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 0 else 0,
            success_rate=successes / iterations,
        )


class BenchmarkSuite:
    """
    基准测试套件
    
    用法:
        suite = BenchmarkSuite()
        
        @suite.benchmark("tool_execution")
        async def test_tool():
            return await execute_tool()
        
        results = await suite.run()
        suite.report(results)
    """
    
    def __init__(self):
        self._benchmarks: Dict[str, Callable] = {}
        self._iterations: Dict[str, int] = {}
    
    def benchmark(self, name: str, iterations: int = 100):
        """装饰器：注册基准测试"""
        def decorator(func: Callable):
            self._benchmarks[name] = func
            self._iterations[name] = iterations
            return func
        return decorator
    
    async def run(self, filter_names: List[str] = None) -> Dict[str, BenchmarkResult]:
        """
        运行所有基准测试
        
        Args:
            filter_names: 要运行的测试名称列表
            
        Returns:
            测试结果字典
        """
        results = {}
        
        for name, func in self._benchmarks.items():
            if filter_names and name not in filter_names:
                continue
            
            print(f"Running benchmark: {name}...")
            
            benchmark = Benchmark(name)
            iterations = self._iterations.get(name, 100)
            
            result = await benchmark.run(func, iterations=iterations)
            results[name] = result
            
            print(f"  ✓ {result.avg_time_ms:.2f}ms (avg)")
        
        return results
    
    def report(self, results: Dict[str, BenchmarkResult], format: str = "text") -> str:
        """生成报告"""
        if format == "json":
            return json.dumps(
                {name: r.to_dict() for name, r in results.items()},
                indent=2,
            )
        
        # 文本报告
        lines = []
        lines.append("=" * 60)
        lines.append("NeuroFlow Performance Benchmark Report")
        lines.append("=" * 60)
        lines.append("")
        
        for name, result in results.items():
            lines.append(str(result))
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


# ========== 预定义基准测试 ==========

async def run_standard_benchmarks():
    """运行标准基准测试"""
    from neuroflow import (
        AINativeAgent,
        LLMConfig,
        UnifiedToolRegistry,
        ToolDefinition,
        ToolParameter,
        ToolSource,
        LocalFunctionExecutor,
        VectorMemoryStore,
        MemoryType,
    )
    
    suite = BenchmarkSuite()
    
    # 工具注册基准测试
    @suite.benchmark("tool_registration", iterations=1000)
    async def benchmark_tool_registration():
        registry = UnifiedToolRegistry()
        executor = LocalFunctionExecutor()
        
        tool = ToolDefinition(
            id="test_tool",
            name="test_tool",
            description="Test tool",
            source=ToolSource.LOCAL_FUNCTION,
            parameters=[
                ToolParameter("param", "string", "Test parameter"),
            ],
        )
        
        registry.register_tool(tool)
        registry.register_executor(ToolSource.LOCAL_FUNCTION, executor)
    
    # 工具执行基准测试
    @suite.benchmark("tool_execution", iterations=100)
    async def benchmark_tool_execution():
        registry = UnifiedToolRegistry()
        executor = LocalFunctionExecutor()
        
        async def test_func(x: int) -> int:
            return x * 2
        
        tool = ToolDefinition(
            id="double",
            name="double",
            description="Double a number",
            source=ToolSource.LOCAL_FUNCTION,
            parameters=[],
        )
        
        registry.register_tool(tool)
        registry.register_executor(ToolSource.LOCAL_FUNCTION, executor)
        executor.register_function(test_func, tool)
        
        from neuroflow.tools import ToolCall
        call = ToolCall(
            tool_id="double",
            tool_name="double",
            arguments={"x": 21},
        )
        
        await registry.execute(call)
    
    # 记忆存储基准测试
    @suite.benchmark("memory_store", iterations=100)
    async def benchmark_memory_store():
        store = VectorMemoryStore()
        
        await store.store(
            key=f"test_key",
            value={"data": "test"},
            memory_type=MemoryType.SHORT_TERM,
            tags=["test"],
            importance=0.5,
        )
    
    # 记忆检索基准测试
    @suite.benchmark("memory_retrieve", iterations=100)
    async def benchmark_memory_retrieve():
        store = VectorMemoryStore()
        
        # 先存储
        await store.store(
            key="test_key",
            value={"data": "test"},
            memory_type=MemoryType.SHORT_TERM,
            tags=["test"],
            importance=0.5,
        )
        
        # 再检索
        await store.retrieve("test_key")
    
    # 运行测试
    results = await suite.run()
    
    # 生成报告
    print("\n")
    print(suite.report(results))
    
    return results


if __name__ == "__main__":
    asyncio.run(run_standard_benchmarks())
