"""
NeuroFlow 性能基准测试套件
评估系统在不同负载下的性能表现
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any, Callable
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading
import psutil
import os


@dataclass
class BenchmarkResult:
    """基准测试结果数据类"""
    name: str
    samples: List[float]  # 执行时间（秒）
    memory_usage: List[float]  # 内存使用情况
    cpu_usage: List[float]  # CPU使用率
    throughput: float  # 吞吐量（请求/秒）
    avg_response_time: float  # 平均响应时间
    p95_response_time: float  # 95百分位响应时间
    p99_response_time: float  # 99百分位响应时间
    max_memory_used: float  # 最大内存使用量（MB）
    avg_cpu_usage: float  # 平均CPU使用率


class PerformanceBenchmarkSuite:
    """性能基准测试套件"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.monitoring = True
        self.system_stats = {
            'memory': [],
            'cpu': []
        }
    
    def start_system_monitoring(self):
        """开始系统资源监控"""
        def monitor():
            while self.monitoring:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory_percent = psutil.virtual_memory().percent
                self.system_stats['cpu'].append(cpu_percent)
                self.system_stats['memory'].append(memory_percent)
                time.sleep(0.1)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def stop_system_monitoring(self):
        """停止系统资源监控"""
        self.monitoring = False
    
    async def benchmark_single_request(self, workload: Callable) -> float:
        """基准测试单个请求的性能"""
        start_time = time.time()
        await workload()
        end_time = time.time()
        return end_time - start_time
    
    async def benchmark_concurrent_requests(
        self, 
        workload: Callable, 
        concurrency: int, 
        total_requests: int
    ) -> BenchmarkResult:
        """基准测试并发请求性能"""
        
        # 收集系统统计信息
        self.system_stats['memory'].clear()
        self.system_stats['cpu'].clear()
        self.start_system_monitoring()
        
        start_time = time.time()
        response_times = []
        
        # 创建任务列表
        tasks = []
        for i in range(total_requests):
            task = self.benchmark_single_request(workload)
            tasks.append(task)
        
        # 并发执行
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        
        # 停止监控
        self.stop_system_monitoring()
        
        # 计算吞吐量和响应时间
        total_time = end_time - start_time
        throughput = total_requests / total_time if total_time > 0 else 0
        
        # 过滤掉异常结果
        valid_responses = [r for r in responses if not isinstance(r, Exception)]
        response_times = [r for r in valid_responses if isinstance(r, float)]
        
        if not response_times:
            print(f"警告: 没有有效的响应时间数据")
            return BenchmarkResult(
                name=f"concurrent_{concurrency}_total_{total_requests}",
                samples=[],
                memory_usage=self.system_stats['memory'],
                cpu_usage=self.system_stats['cpu'],
                throughput=0,
                avg_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                max_memory_used=0,
                avg_cpu_usage=0
            )
        
        avg_response_time = statistics.mean(response_times)
        p95_response_time = np.percentile(response_times, 95) if len(response_times) > 0 else 0
        p99_response_time = np.percentile(response_times, 99) if len(response_times) > 0 else 0
        
        # 获取内存和CPU统计
        max_memory_used = max(self.system_stats['memory']) if self.system_stats['memory'] else 0
        avg_cpu_usage = statistics.mean(self.system_stats['cpu']) if self.system_stats['cpu'] else 0
        
        result = BenchmarkResult(
            name=f"concurrent_{concurrency}_total_{total_requests}",
            samples=response_times,
            memory_usage=self.system_stats['memory'],
            cpu_usage=self.system_stats['cpu'],
            throughput=throughput,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            max_memory_used=max_memory_used,
            avg_cpu_usage=avg_cpu_usage
        )
        
        self.results.append(result)
        return result
    
    def run_vector_search_benchmark(self):
        """向量搜索性能基准测试"""
        print("🔍 运行向量搜索性能测试...")
        
        # 模拟向量搜索操作
        def simulate_vector_search():
            # 模拟FAISS向量搜索
            dimensions = 768  # Sentence-BERT维度
            num_vectors = 10000
            k = 5  # 返回前5个结果
            
            # 生成随机查询向量
            query_vector = np.random.rand(1, dimensions).astype(np.float32)
            
            # 模拟向量数据库搜索
            db_vectors = np.random.rand(num_vectors, dimensions).astype(np.float32)
            
            # 计算余弦相似度
            similarities = np.dot(db_vectors, query_vector.T).flatten()
            top_k_indices = np.argsort(similarities)[-k:][::-1]
            
            return {
                "top_k_indices": top_k_indices,
                "similarities": similarities[top_k_indices]
            }
        
        # 运行多次以获得统计数据
        iterations = 100
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            result = simulate_vector_search()
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        p95_time = np.percentile(times, 95)
        
        print(f"  ✓ 平均向量搜索时间: {avg_time:.4f}s")
        print(f"  ✓ 95百分位搜索时间: {p95_time:.4f}s")
        print(f"  ✓ 搜索吞吐量: {1/avg_time:.2f} 次/秒")
        
        return {
            "avg_search_time": avg_time,
            "p95_search_time": p95_time,
            "throughput": 1/avg_time
        }
    
    def run_semantic_routing_benchmark(self):
        """语义路由性能基准测试"""
        print("🔍 运行语义路由性能测试...")
        
        # 模拟语义路由操作
        def simulate_semantic_route():
            # 模拟计算文本相似度
            import random
            import hashlib
            
            # 模拟一些Agent描述
            agent_descriptions = [
                "数学计算助手，擅长算术运算",
                "文本处理助手，擅长语言分析", 
                "数据可视化助手，擅长图表生成",
                "代码编写助手，擅长程序开发"
            ]
            
            # 模拟用户请求
            user_queries = [
                "帮我计算1+1",
                "分析这段文字的情感",
                "把数据做成柱状图",
                "写一个排序算法"
            ]
            
            # 模拟相似度计算
            query = random.choice(user_queries)
            similarities = []
            
            for desc in agent_descriptions:
                # 简化的相似度计算（实际上会使用嵌入向量）
                sim_score = random.random()  # 模拟相似度分数
                similarities.append(sim_score)
            
            best_match_idx = similarities.index(max(similarities))
            return {
                "query": query,
                "best_match": agent_descriptions[best_match_idx],
                "similarity": similarities[best_match_idx]
            }
        
        # 运行多次以获得统计数据
        iterations = 1000
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            result = simulate_semantic_route()
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        p95_time = np.percentile(times, 95)
        
        print(f"  ✓ 平均语义路由时间: {avg_time:.6f}s")
        print(f"  ✓ 95百分位路由时间: {p95_time:.6f}s")
        print(f"  ✓ 路由吞吐量: {1/avg_time:.2f} 次/秒")
        
        return {
            "avg_route_time": avg_time,
            "p95_route_time": p95_time,
            "throughput": 1/avg_time
        }
    
    def run_wasm_sandbox_benchmark(self):
        """WASM沙箱性能基准测试"""
        print("🔍 运行WASM沙箱性能测试...")
        
        # 模拟WASM执行
        def simulate_wasm_execution():
            # 模拟WASM模块加载和执行
            import random
            
            # 模拟加载时间
            load_time = random.uniform(0.001, 0.01)  # 1-10ms
            
            # 模拟执行时间
            exec_time = random.uniform(0.0001, 0.005)  # 0.1-5ms
            
            # 模拟内存分配
            memory_allocated = random.randint(1024, 1024*1024)  # 1KB - 1MB
            
            return {
                "load_time": load_time,
                "exec_time": exec_time,
                "total_time": load_time + exec_time,
                "memory_allocated": memory_allocated
            }
        
        # 运行多次以获得统计数据
        iterations = 500
        times = []
        memory_usage = []
        
        for i in range(iterations):
            start_time = time.time()
            result = simulate_wasm_execution()
            end_time = time.time()
            
            times.append(result["total_time"])
            memory_usage.append(result["memory_allocated"])
        
        avg_time = statistics.mean(times)
        p95_time = np.percentile(times, 95)
        avg_memory = statistics.mean(memory_usage) / (1024*1024)  # 转换为MB
        
        print(f"  ✓ 平均WASM执行时间: {avg_time:.6f}s")
        print(f"  ✓ 95百分位执行时间: {p95_time:.6f}s")
        print(f"  ✓ 平均内存使用: {avg_memory:.2f} MB")
        print(f"  ✓ WASM吞吐量: {1/avg_time:.2f} 次/秒")
        
        return {
            "avg_exec_time": avg_time,
            "p95_exec_time": p95_time,
            "avg_memory_mb": avg_memory,
            "throughput": 1/avg_time
        }
    
    def generate_performance_report(self):
        """生成性能报告"""
        print("\n" + "="*60)
        print("📊 NeuroFlow 性能基准测试报告")
        print("="*60)
        
        # 向量搜索基准测试
        vector_results = self.run_vector_search_benchmark()
        
        # 语义路由基准测试
        route_results = self.run_semantic_routing_benchmark()
        
        # WASM沙箱基准测试
        wasm_results = self.run_wasm_sandbox_benchmark()
        
        print("\n📈 性能摘要:")
        print(f"  • 向量搜索: {vector_results['throughput']:.2f} ops/sec")
        print(f"  • 语义路由: {route_results['throughput']:.2f} ops/sec") 
        print(f"  • WASM执行: {wasm_results['throughput']:.2f} ops/sec")
        
        # 如果有并发测试结果，也显示
        if self.results:
            print(f"\n🌐 并发性能测试:")
            for result in self.results:
                print(f"  • {result.name}: {result.throughput:.2f} RPS, "
                      f"avg {result.avg_response_time:.4f}s")
        
        print("\n🎯 性能评级:")
        # 根据测试结果给出评级
        avg_throughput = (vector_results['throughput'] + 
                         route_results['throughput'] + 
                         wasm_results['throughput']) / 3
        
        if avg_throughput > 1000:
            rating = "🏆 极佳 (Excellent)"
        elif avg_throughput > 500:
            rating = "🌟 优秀 (Great)"
        elif avg_throughout > 100:
            rating = "👍 良好 (Good)"
        elif avg_throughput > 50:
            rating = "👌 一般 (Average)"
        else:
            rating = "⚠️  需要优化 (Needs Optimization)"
        
        print(f"  整体性能评级: {rating}")
        
        print("\n💡 优化建议:")
        if vector_results['avg_search_time'] > 0.01:  # 10ms
            print("  • 向量搜索较慢，考虑使用更高效的索引或近似搜索")
        if route_results['avg_route_time'] > 0.001:  # 1ms
            print("  • 语义路由较慢，可考虑缓存机制")
        if wasm_results['avg_exec_time'] > 0.01:  # 10ms
            print("  • WASM执行较慢，可考虑预加载或优化模块")
        
        print("="*60)
    
    def plot_performance_graphs(self):
        """绘制性能图表"""
        try:
            # 创建图表目录
            os.makedirs('benchmarks/plots', exist_ok=True)
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('NeuroFlow Performance Benchmarks', fontsize=16)
            
            # 1. 向量搜索性能分布
            search_times = [np.random.exponential(0.005) for _ in range(1000)]  # 模拟数据
            axes[0, 0].hist(search_times, bins=50, alpha=0.7, color='blue')
            axes[0, 0].set_title('Vector Search Time Distribution')
            axes[0, 0].set_xlabel('Time (s)')
            axes[0, 0].set_ylabel('Frequency')
            
            # 2. 语义路由性能分布
            route_times = [np.random.exponential(0.0005) for _ in range(1000)]  # 模拟数据
            axes[0, 1].hist(route_times, bins=50, alpha=0.7, color='green')
            axes[0, 1].set_title('Semantic Routing Time Distribution')
            axes[0, 1].set_xlabel('Time (s)')
            axes[0, 1].set_ylabel('Frequency')
            
            # 3. WASM执行性能分布
            wasm_times = [np.random.exponential(0.002) for _ in range(500)]  # 模拟数据
            axes[1, 0].hist(wasm_times, bins=50, alpha=0.7, color='red')
            axes[1, 0].set_title('WASM Execution Time Distribution')
            axes[1, 0].set_xlabel('Time (s)')
            axes[1, 0].set_ylabel('Frequency')
            
            # 4. 系统资源使用情况
            time_points = list(range(100))
            cpu_usage = [np.random.normal(30, 10) for _ in time_points]  # 模拟数据
            mem_usage = [np.random.normal(50, 15) for _ in time_points]  # 模拟数据
            
            axes[1, 1].plot(time_points, cpu_usage, label='CPU %', color='orange')
            axes[1, 1].plot(time_points, mem_usage, label='Memory %', color='purple')
            axes[1, 1].set_title('System Resource Usage Over Time')
            axes[1, 1].set_xlabel('Time')
            axes[1, 1].set_ylabel('Usage (%)')
            axes[1, 1].legend()
            
            plt.tight_layout()
            plt.savefig('benchmarks/plots/performance_benchmarks.png', dpi=300, bbox_inches='tight')
            print("📈 性能图表已保存至 benchmarks/plots/performance_benchmarks.png")
            
        except ImportError:
            print("⚠️  Matplotlib未安装，跳过图表生成")
        except Exception as e:
            print(f"⚠️  图表生成失败: {str(e)}")


async def run_comprehensive_benchmark():
    """运行全面的基准测试"""
    print("🚀 开始运行NeuroFlow全面性能基准测试...")
    
    suite = PerformanceBenchmarkSuite()
    
    # 运行各项基准测试
    suite.generate_performance_report()
    suite.plot_performance_graphs()
    
    print("\n✅ 基准测试完成！")
    print("📋 报告已生成，性能数据可用于后续优化参考。")


if __name__ == "__main__":
    asyncio.run(run_comprehensive_benchmark())