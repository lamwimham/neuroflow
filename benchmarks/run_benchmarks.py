#!/usr/bin/env python3
"""
NeuroFlow 基准测试执行器
用于运行和管理性能基准测试
"""

import asyncio
import sys
import os
import argparse
from benchmarks.performance_benchmarks import run_comprehensive_benchmark


def main():
    parser = argparse.ArgumentParser(description='NeuroFlow Performance Benchmark Suite')
    parser.add_argument('--benchmark', '-b', 
                       choices=['all', 'vector-search', 'semantic-routing', 'wasm', 'concurrent'],
                       default='all',
                       help='选择要运行的基准测试类型')
    parser.add_argument('--iterations', '-i', 
                       type=int, 
                       default=100,
                       help='基准测试迭代次数')
    parser.add_argument('--output', '-o', 
                       type=str, 
                       default='./benchmarks/results',
                       help='基准测试结果输出目录')
    
    args = parser.parse_args()
    
    print(f"🚀 启动 NeuroFlow 基准测试...")
    print(f"📋 测试类型: {args.benchmark}")
    print(f"🔄 迭代次数: {args.iterations}")
    print(f"📊 输出目录: {args.output}")
    
    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    
    # 运行基准测试
    try:
        asyncio.run(run_comprehensive_benchmark())
        print("\n✅ 基准测试执行完成！")
    except KeyboardInterrupt:
        print("\n⚠️  基准测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 基准测试执行失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()