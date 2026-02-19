# NeuroFlow 快速开始指南

## 30 分钟快速入门

### 1. 安装依赖 (5 分钟)

```bash
# 克隆项目
cd /path/to/NeuroFlow/sdk

# 安装 SDK
pip install -e .

# 验证安装
python -c "from neuroflow import NeuroFlowSDK; print('✓ 安装成功')"
```

### 2. 运行示例 (5 分钟)

```bash
# 运行最小可用示例
cd /path/to/NeuroFlow
python examples/minimal_working_example.py
```

**预期输出**:
```
============================================================
NeuroFlow 最小可用示例
============================================================

============================================================
示例 1: 基础 SDK 使用
============================================================
计算结果：14.0
回显结果：Hello, NeuroFlow!

============================================================
示例 2: 使用全局 SDK 实例
============================================================
问候结果：Hello, Developer! Welcome to NeuroFlow.

...

============================================================
所有示例运行完成!
============================================================
```

### 3. 创建你的第一个 Agent (15 分钟)

创建文件 `my_first_agent.py`:

```python
import asyncio
from neuroflow import NeuroFlowSDK, agent, tool

# 定义工具
@tool(name="calculate_bmi", description="计算 BMI 指数")
async def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """计算 BMI"""
    return weight_kg / (height_m ** 2)

# 定义 Agent
@agent(name="bmi_agent", description="BMI 计算助手")
class BMIAgent:
    def __init__(self, sdk):
        self.sdk = sdk
    
    async def handle(self, request: dict) -> dict:
        weight = request.get("weight", 70)
        height = request.get("height", 1.75)
        
        bmi = await self.sdk.execute_tool(
            "calculate_bmi",
            weight_kg=weight,
            height_m=height
        )
        
        # BMI 分类
        if bmi < 18.5:
            category = "偏瘦"
        elif bmi < 25:
            category = "正常"
        else:
            category = "偏胖"
        
        return {
            "bmi": round(bmi, 2),
            "category": category
        }

async def main():
    # 创建 SDK
    sdk = await NeuroFlowSDK.create()
    
    # 创建 Agent
    agent = BMIAgent(sdk)
    
    # 测试
    result = await agent.handle({
        "weight": 75,
        "height": 1.80
    })
    
    print(f"BMI: {result['bmi']} ({result['category']})")
    
    await sdk.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

运行:
```bash
python my_first_agent.py
```

**输出**:
```
BMI: 23.15 (正常)
```

### 4. 下一步 (5 分钟)

- 查看 [examples/minimal_working_example.py](examples/minimal_working_example.py) 更多示例
- 阅读 [ITERATION_PLAN.md](ITERATION_PLAN.md) 了解发展路线
- 查看 [docs/](docs/) 详细文档

## 核心概念

### SDK (NeuroFlowSDK)
- 统一的 SDK 入口
- 显式初始化，避免异步陷阱
- 管理工具和 Agent 注册

### 工具 (@tool)
- 可复用的功能单元
- 自动类型检查
- 支持异步执行

### Agent (@agent)
- 独立的业务逻辑单元
- 可以组合多个工具
- 支持上下文管理

## 常见问题

### Q: 为什么需要显式初始化？
A: 避免模块加载时的异步初始化陷阱，让初始化流程更清晰可控。

### Q: 如何调试？
A: 设置环境变量 `NEUROFLOW_LOG_LEVEL=debug`

### Q: 性能如何？
A: 当前版本网关延迟 < 10ms, 支持 10+ 并发沙箱。查看性能报告了解更多。

## 获取帮助

- 查看 [ITERATION_PLAN.md](ITERATION_PLAN.md)
- 提交 Issue
- 参与 Discussion
