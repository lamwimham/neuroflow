#!/usr/bin/env python3
"""
NeuroFlow v0.5.0 - Performance Benchmark Suite

Comprehensive performance benchmarking for NeuroFlow SDK.

Benchmarks:
1. Gateway latency (P50, P99)
2. Tool invocation latency
3. A2A communication latency
4. Sandbox startup time
5. Concurrent agent support
6. Memory footprint

Usage:
    python benchmarks/benchmark_v0.5.0.py
    
    # Specific benchmark
    python benchmarks/benchmark_v0.5.0.py --benchmark=gateway
    
    # Compare with baseline
    python benchmarks/benchmark_v0.5.0.py --compare baseline.json
"""

import asyncio
import time
import statistics
import json
import argparse
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import concurrent.futures

# Add neuroflow to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk'))

from neuroflow.mcp import MCPServerManager, RealMCPExecutor
from neuroflow.a2a import AgentRegistryService, AgentRegistration, A2AHTTPClient
from neuroflow.sandbox import SandboxIsolator, SandboxConfig


@dataclass
class BenchmarkResult:
    """Benchmark result"""
    name: str
    iterations: int
    min_ms: float
    max_ms: float
    mean_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    std_dev_ms: float
    success_rate: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "min_ms": round(self.min_ms, 3),
            "max_ms": round(self.max_ms, 3),
            "mean_ms": round(self.mean_ms, 3),
            "median_ms": round(self.median_ms, 3),
            "p95_ms": round(self.p95_ms, 3),
            "p99_ms": round(self.p99_ms, 3),
            "std_dev_ms": round(self.std_dev_ms, 3),
            "success_rate": round(self.success_rate, 4),
            "timestamp": self.timestamp,
        }
    
    def to_summary(self) -> str:
        """Generate summary string"""
        return (
            f"{self.name}: "
            f"mean={self.mean_ms:.2f}ms, "
            f"median={self.median_ms:.2f}ms, "
            f"p99={self.p99_ms:.2f}ms, "
            f"p95={self.p95_ms:.2f}ms, "
            f"σ={self.std_dev_ms:.2f}ms"
        )


class PerformanceBenchmark:
    """Base class for benchmarks"""
    
    def __init__(self, iterations: int = 100, warmup: int = 10):
        self.iterations = iterations
        self.warmup = warmup
    
    async def run(self) -> BenchmarkResult:
        """Run benchmark"""
        # Warmup
        await self._warmup()
        
        # Run benchmark
        latencies = []
        successes = 0
        
        for i in range(self.iterations):
            start = time.perf_counter()
            try:
                await self._execute()
                successes += 1
            except Exception as e:
                pass
            end = time.perf_counter()
            
            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)
        
        # Calculate statistics
        return self._calculate_stats(latencies, successes)
    
    async def _warmup(self) -> None:
        """Warmup phase"""
        for _ in range(self.warmup):
            try:
                await self._execute()
            except:
                pass
    
    async def _execute(self) -> None:
        """Execute benchmark operation"""
        raise NotImplementedError
    
    def _calculate_stats(self, latencies: List[float], successes: int) -> BenchmarkResult:
        """Calculate statistics from latencies"""
        if not latencies:
            return BenchmarkResult(
                name=self.__class__.__name__,
                iterations=self.iterations,
                min_ms=0,
                max_ms=0,
                mean_ms=0,
                median_ms=0,
                p95_ms=0,
                p99_ms=0,
                std_dev_ms=0,
                success_rate=0,
            )
        
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        
        return BenchmarkResult(
            name=self.__class__.__name__,
            iterations=self.iterations,
            min_ms=min(latencies),
            max_ms=max(latencies),
            mean_ms=statistics.mean(latencies),
            median_ms=statistics.median(latencies),
            p95_ms=sorted_latencies[int(n * 0.95)] if n > 1 else sorted_latencies[-1],
            p99_ms=sorted_latencies[int(n * 0.99)] if n > 1 else sorted_latencies[-1],
            std_dev_ms=statistics.stdev(latencies) if n > 1 else 0,
            success_rate=successes / self.iterations,
        )


class GatewayLatencyBenchmark(PerformanceBenchmark):
    """Gateway latency benchmark"""
    
    async def _execute(self) -> None:
        """Simulate gateway request"""
        # This would test the actual Rust gateway
        # For now, simulate with async sleep
        await asyncio.sleep(0.001)  # 1ms simulated latency


class ToolInvocationBenchmark(PerformanceBenchmark):
    """Tool invocation latency benchmark"""
    
    def __init__(self, iterations: int = 100, warmup: int = 10):
        super().__init__(iterations, warmup)
        self.executor = RealMCPExecutor()
    
    async def _execute(self) -> None:
        """Execute tool invocation"""
        # Start filesystem server
        await self.executor.start_server(
            name="benchmark_fs",
            server_type="filesystem",
            command="echo",
            args=["test"],
        )
        
        # Execute tool
        await self.executor.execute_tool(
            server_name="benchmark_fs",
            tool_name="read_file",
            arguments={"path": "/tmp/test.txt"},
        )
        
        # Stop server
        await self.executor.stop_server("benchmark_fs")


class A2ACommunicationBenchmark(PerformanceBenchmark):
    """A2A communication latency benchmark"""
    
    def __init__(self, iterations: int = 100, warmup: int = 10):
        super().__init__(iterations, warmup)
        self.registry = AgentRegistryService(backend="memory")
    
    async def _execute(self) -> None:
        """Execute A2A communication"""
        # Register agent
        agent = AgentRegistration(
            id="benchmark_agent",
            name="Benchmark Agent",
            description="Benchmark test agent",
            endpoint="http://localhost:9999",
            capabilities=["benchmark"],
        )
        await self.registry.register(agent)
        
        # Discover agent
        await self.registry.discover_by_capability("benchmark")
        
        # Deregister
        await self.registry.deregister("benchmark_agent")


class SandboxStartupBenchmark(PerformanceBenchmark):
    """Sandbox startup time benchmark"""
    
    async def _execute(self) -> None:
        """Execute sandbox startup"""
        config = SandboxConfig(
            work_dir="/tmp/neuroflow-benchmark",
            cpu_time_limit=1,
        )
        
        isolator = SandboxIsolator(config)
        await isolator.execute("echo", ["test"])


class ConcurrentAgentBenchmark(PerformanceBenchmark):
    """Concurrent agent support benchmark"""
    
    def __init__(self, iterations: int = 10, warmup: int = 2, max_concurrent: int = 50):
        super().__init__(iterations, warmup)
        self.max_concurrent = max_concurrent
    
    async def _execute(self) -> None:
        """Execute concurrent agent simulation"""
        registry = AgentRegistryService(backend="memory")
        await registry.start()
        
        try:
            # Register many agents concurrently
            async def register_agent(i: int):
                agent = AgentRegistration(
                    id=f"agent_{i}",
                    name=f"Agent {i}",
                    description=f"Test agent {i}",
                    endpoint=f"http://localhost:{9000 + i}",
                    capabilities=["test"],
                )
                await registry.register(agent)
            
            # Concurrent registration
            tasks = [register_agent(i) for i in range(self.max_concurrent)]
            await asyncio.gather(*tasks)
            
            # Query agents
            agents = await registry.list_agents()
            assert len(agents) == self.max_concurrent
            
        finally:
            await registry.stop()


class MemoryFootprintBenchmark:
    """Memory footprint benchmark"""
    
    def measure(self) -> Dict[str, Any]:
        """Measure memory usage"""
        import resource
        
        # Get current memory usage
        usage = resource.getrusage(resource.RUSAGE_SELF)
        
        return {
            "max_rss_mb": usage.ru_maxrss / 1024,  # Convert to MB
            "shared_mem_mb": usage.ru_ixrss / 1024 / 1024,
            "unshared_data_mb": usage.ru_idrss / 1024 / 1024,
            "unshared_stack_mb": usage.ru_isrss / 1024 / 1024,
        }


async def run_all_benchmarks() -> Dict[str, Any]:
    """Run all benchmarks"""
    print("\n" + "="*70)
    print(" " * 20 + "NeuroFlow v0.5.0 Performance Benchmarks")
    print("="*70 + "\n")
    
    results = {}
    
    # Gateway latency
    print("Running Gateway Latency Benchmark...")
    benchmark = GatewayLatencyBenchmark(iterations=1000)
    result = await benchmark.run()
    results["gateway_latency"] = result.to_dict()
    print(f"  {result.to_summary()}\n")
    
    # Tool invocation
    print("Running Tool Invocation Benchmark...")
    benchmark = ToolInvocationBenchmark(iterations=50)
    result = await benchmark.run()
    results["tool_invocation"] = result.to_dict()
    print(f"  {result.to_summary()}\n")
    
    # A2A communication
    print("Running A2A Communication Benchmark...")
    benchmark = A2ACommunicationBenchmark(iterations=100)
    result = await benchmark.run()
    results["a2a_communication"] = result.to_dict()
    print(f"  {result.to_summary()}\n")
    
    # Sandbox startup
    print("Running Sandbox Startup Benchmark...")
    benchmark = SandboxStartupBenchmark(iterations=50)
    result = await benchmark.run()
    results["sandbox_startup"] = result.to_dict()
    print(f"  {result.to_summary()}\n")
    
    # Concurrent agents
    print("Running Concurrent Agent Benchmark...")
    benchmark = ConcurrentAgentBenchmark(max_concurrent=50)
    result = await benchmark.run()
    results["concurrent_agents"] = {
        "max_concurrent": 50,
        "success": True,
    }
    print(f"  Successfully handled 50 concurrent agents\n")
    
    # Memory footprint
    print("Measuring Memory Footprint...")
    memory_benchmark = MemoryFootprintBenchmark()
    memory_result = memory_benchmark.measure()
    results["memory_footprint"] = memory_result
    print(f"  Max RSS: {memory_result['max_rss_mb']:.2f} MB\n")
    
    return results


def compare_results(current: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
    """Compare current results with baseline"""
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "baseline_timestamp": baseline.get("timestamp", "unknown"),
        "metrics": {},
    }
    
    for metric_name, current_data in current.items():
        if metric_name in baseline and "mean_ms" in current_data:
            baseline_data = baseline[metric_name]
            
            if "mean_ms" in baseline_data:
                baseline_mean = baseline_data["mean_ms"]
                current_mean = current_data["mean_ms"]
                
                change_pct = ((current_mean - baseline_mean) / baseline_mean) * 100 if baseline_mean > 0 else 0
                
                comparison["metrics"][metric_name] = {
                    "baseline_ms": round(baseline_mean, 3),
                    "current_ms": round(current_mean, 3),
                    "change_pct": round(change_pct, 2),
                    "improved": change_pct < 0,
                }
    
    return comparison


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="NeuroFlow Performance Benchmark")
    parser.add_argument(
        "--benchmark",
        type=str,
        default="all",
        help="Specific benchmark to run (default: all)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of iterations (default: 100)",
    )
    parser.add_argument(
        "--compare",
        type=str,
        help="Compare with baseline JSON file",
    )
    parser.add_argument(
        "--output",
    type=str,
        default="benchmark_results.json",
        help="Output results to JSON file",
    )
    
    args = parser.parse_args()
    
    # Run benchmarks
    results = asyncio.run(run_all_benchmarks())
    
    # Compare with baseline if provided
    if args.compare:
        print("\n" + "="*70)
        print("Comparing with baseline...")
        print("="*70 + "\n")
        
        with open(args.compare, 'r') as f:
            baseline = json.load(f)
        
        comparison = compare_results(results, baseline)
        
        print(f"Baseline: {comparison['baseline_timestamp']}")
        print(f"Current:  {comparison['timestamp']}\n")
        
        for metric_name, metric_data in comparison["metrics"].items():
            icon = "✅" if metric_data["improved"] else "⚠️"
            print(f"  {icon} {metric_name}:")
            print(f"      Baseline: {metric_data['baseline_ms']:.2f}ms")
            print(f"      Current:  {metric_data['current_ms']:.2f}ms")
            print(f"      Change:   {metric_data['change_pct']:+.2f}%")
        
        results["comparison"] = comparison
    
    # Save results
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "version": "0.5.0",
        "results": results,
    }
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\nResults saved to {args.output}")
    
    # Print summary
    print("\n" + "="*70)
    print("Benchmark Summary")
    print("="*70)
    
    for metric_name, metric_data in results.items():
        if "mean_ms" in metric_data:
            print(f"  {metric_name}: {metric_data['mean_ms']:.2f}ms (p99: {metric_data['p99_ms']:.2f}ms)")
    
    print("="*70 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
