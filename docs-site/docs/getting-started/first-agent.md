# 创建你的第一个 Agent

本教程将带你一步步创建、测试和部署第一个生产级 AI Agent。

## 📋 前提条件

- ✅ 已完成 [安装指南](installation.md)
- ✅ NeuroFlow SDK v0.3.0+
- ✅ 基础 Python 知识

## ⏱️ 时间安排

- **理解 Agent 概念**: 10 分钟
- **创建 Agent**: 15 分钟
- **测试 Agent**: 10 分钟
- **部署 Agent**: 5 分钟

## 步骤 1: 理解 Agent 基础 (10 分钟)

### 什么是 Agent?

Agent 是 NeuroFlow 中的核心组件，负责:
- 接收请求
- 处理业务逻辑
- 调用工具
- 返回响应

### Agent 生命周期

```
请求 → Agent 初始化 → 处理请求 → 调用工具 → 返回响应 → 清理资源
```

### Agent 基本结构

```python
from neuroflow import agent

@agent(name="my_agent", description="我的 Agent")
class MyAgent:
    async def handle(self, request: dict) -> dict:
        """处理请求的主要方法"""
        # 1. 解析请求
        # 2. 业务逻辑
        # 3. 返回响应
        pass
```

## 步骤 2: 创建项目 (5 分钟)

### 2.1 创建新项目

```bash
# 创建工作目录
mkdir -p ~/projects/first-agent
cd ~/projects/first-agent

# 使用 CLI 创建项目
neuroflow new weather-agent --template basic

# 或使用基础模板
neuroflow new weather-agent
```

### 2.2 项目结构

```
weather-agent/
├── agents/
│   ├── __init__.py
│   └── weather_agent.py      # 我们将在这里创建天气 Agent
├── tools/
│   ├── __init__.py
│   └── basic_tools.py        # 基础工具
├── config/
│   └── neuroflow.yaml        # 配置文件
├── tests/
│   └── test_agents.py        # 测试文件
├── requirements.txt          # 依赖
└── README.md                # 项目说明
```

### 2.3 安装依赖

```bash
# 激活虚拟环境 (如果未激活)
cd weather-agent
source venv/bin/activate  # Windows: .\venv\Scripts\Activate

# 安装依赖
pip install -r requirements.txt
```

## 步骤 3: 创建天气 Agent (15 分钟)

### 3.1 定义工具

首先，我们需要创建获取天气数据的工具。

编辑 `tools/weather_tools.py`:

```python
"""天气相关工具"""
from neuroflow import tool
import random
from datetime import datetime

@tool(name="get_weather", description="获取指定城市的天气")
async def get_weather(city: str) -> dict:
    """
    获取天气信息
    
    Args:
        city: 城市名称
        
    Returns:
        包含温度、湿度、天气状况的字典
    """
    # 模拟天气数据 (实际应用中应调用天气 API)
    weather_conditions = ["晴天", "多云", "阴天", "小雨", "大雨"]
    
    return {
        "city": city,
        "temperature": random.randint(15, 35),
        "humidity": random.randint(40, 90),
        "condition": random.choice(weather_conditions),
        "timestamp": datetime.now().isoformat()
    }

@tool(name="get_weather_forecast", description="获取天气预报")
async def get_weather_forecast(city: str, days: int = 3) -> list:
    """
    获取天气预报
    
    Args:
        city: 城市名称
        days: 预报天数 (1-7)
        
    Returns:
        包含每天预报的列表
    """
    if days > 7:
        days = 7
    
    forecast = []
    weather_conditions = ["晴天", "多云", "阴天", "小雨", "大雨"]
    
    for i in range(days):
        forecast.append({
            "date": f"第{i+1}天",
            "city": city,
            "temperature_high": random.randint(25, 35),
            "temperature_low": random.randint(15, 25),
            "condition": random.choice(weather_conditions)
        })
    
    return forecast
```

### 3.2 创建 Agent

编辑 `agents/weather_agent.py`:

```python
"""天气查询 Agent"""
from neuroflow import agent, tool
from typing import Dict, Any

@agent(name="weather_agent", description="天气查询助手")
class WeatherAgent:
    """天气查询 Agent，提供天气信息查询服务"""
    
    def __init__(self):
        """初始化 Agent"""
        self.name = "weather_agent"
        self.description = "我可以帮你查询天气信息"
    
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理天气查询请求
        
        Args:
            request: 包含查询参数的字典
            
        Returns:
            包含天气信息的响应
        """
        from neuroflow import NeuroFlowSDK
        
        # 创建 SDK 实例
        sdk = await NeuroFlowSDK.create()
        
        try:
            # 解析请求
            action = request.get("action", "current")
            city = request.get("city", "北京")
            days = request.get("days", 3)
            
            # 根据动作执行不同逻辑
            if action == "current":
                # 查询当前天气
                weather = await sdk.execute_tool("get_weather", city=city)
                return {
                    "success": True,
                    "data": weather,
                    "message": f"已获取 {city} 的天气信息"
                }
            
            elif action == "forecast":
                # 查询天气预报
                forecast = await sdk.execute_tool(
                    "get_weather_forecast",
                    city=city,
                    days=days
                )
                return {
                    "success": True,
                    "data": forecast,
                    "message": f"已获取 {city} 的{days}天天气预报"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"未知动作：{action}",
                    "message": "支持的动作：current, forecast"
                }
        
        finally:
            # 清理资源
            await sdk.shutdown()
```

## 步骤 4: 测试 Agent (10 分钟)

### 4.1 编写单元测试

创建 `tests/test_weather_agent.py`:

```python
"""天气 Agent 测试"""
import pytest
import asyncio
from neuroflow import NeuroFlowSDK


@pytest.mark.asyncio
async def test_weather_agent_current():
    """测试当前天气查询"""
    from agents.weather_agent import WeatherAgent
    
    # 创建 Agent 实例
    agent = WeatherAgent()
    
    # 准备测试请求
    request = {
        "action": "current",
        "city": "北京"
    }
    
    # 执行请求
    response = await agent.handle(request)
    
    # 验证响应
    assert response["success"] is True
    assert "data" in response
    assert "city" in response["data"]
    assert response["data"]["city"] == "北京"
    assert "temperature" in response["data"]


@pytest.mark.asyncio
async def test_weather_agent_forecast():
    """测试天气预报查询"""
    from agents.weather_agent import WeatherAgent
    
    agent = WeatherAgent()
    
    request = {
        "action": "forecast",
        "city": "上海",
        "days": 5
    }
    
    response = await agent.handle(request)
    
    assert response["success"] is True
    assert "data" in response
    assert isinstance(response["data"], list)
    assert len(response["data"]) == 5


@pytest.mark.asyncio
async def test_weather_agent_invalid_action():
    """测试无效动作"""
    from agents.weather_agent import WeatherAgent
    
    agent = WeatherAgent()
    
    request = {
        "action": "invalid_action",
        "city": "深圳"
    }
    
    response = await agent.handle(request)
    
    assert response["success"] is False
    assert "error" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 4.2 运行测试

```bash
# 运行测试
pytest tests/test_weather_agent.py -v
```

**预期输出**:
```
============================= test session starts ==============================
tests/test_weather_agent.py::test_weather_agent_current PASSED
tests/test_weather_agent.py::test_weather_agent_forecast PASSED
tests/test_weather_agent.py::test_weather_agent_invalid_action PASSED

============================== 3 passed in 0.5s ================================
```

### 4.3 手动测试

```bash
# 启动开发服务器
neuroflow run

# 在另一个终端发送测试请求
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "weather_agent",
    "payload": {
      "action": "current",
      "city": "北京"
    }
  }'
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "city": "北京",
    "temperature": 28,
    "humidity": 65,
    "condition": "晴天",
    "timestamp": "2024-02-25T10:30:00"
  },
  "message": "已获取 北京 的天气信息"
}
```

## 步骤 5: 部署 Agent (5 分钟)

### 5.1 本地部署

```bash
# 生产模式运行
neuroflow run --port 8080 --log-level info
```

### 5.2 Docker 部署

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["neuroflow", "run", "--port", "8080"]
```

构建和运行:

```bash
# 构建镜像
docker build -t weather-agent:latest .

# 运行容器
docker run -p 8080:8080 weather-agent:latest
```

### 5.3 健康检查

```bash
# 检查服务状态
curl http://localhost:8080/health

# 预期响应
{
  "status": "healthy",
  "version": "0.3.0",
  "port": 8080
}
```

## 🎯 练习题目

### 练习 1: 添加温度转换工具

创建一个工具，支持摄氏度和华氏度转换:

```python
@tool(name="convert_temperature", description="温度单位转换")
async def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """
    转换温度单位
    
    Args:
        value: 温度值
        from_unit: 原单位 (C 或 F)
        to_unit: 目标单位 (C 或 F)
        
    Returns:
        转换后的温度值
    """
    # TODO: 实现转换逻辑
    pass
```

### 练习 2: 添加城市别名支持

修改天气 Agent，支持城市别名:

```python
CITY_ALIASES = {
    "Beijing": "北京",
    "Shanghai": "上海",
    "Shenzhen": "深圳",
    "Guangzhou": "广州"
}

# 在 handle 方法中添加别名转换逻辑
```

### 练习 3: 添加缓存功能

为天气查询添加缓存，减少重复请求:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_weather_cached(city: str) -> dict:
    # 实现缓存逻辑
    pass
```

## 📚 参考答案

### 练习 1 答案

```python
@tool(name="convert_temperature", description="温度单位转换")
async def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    if from_unit == to_unit:
        return value
    
    if from_unit == "C" and to_unit == "F":
        return (value * 9/5) + 32
    elif from_unit == "F" and to_unit == "C":
        return (value - 32) * 5/9
    else:
        raise ValueError(f"Unsupported units: {from_unit}, {to_unit}")
```

## ❓ 常见问题

### Q1: 工具未被识别？

**A**: 确保工具使用了 `@tool` 装饰器，并且在 `__init__.py` 中导出。

### Q2: Agent 无法启动？

**A**: 检查以下几点:
1. 依赖是否安装完整
2. 端口是否被占用
3. 查看错误日志

### Q3: 测试失败？

**A**: 确保:
1. 虚拟环境已激活
2. pytest 已安装
3. 测试函数以 `test_` 开头

## 📞 获取帮助

- 📖 [概念指南](../concepts/agents.md) - 深入理解 Agent
- 💬 [Discord 社区](https://discord.gg/neuroflow)
- 🐛 [GitHub Issues](https://github.com/lamwimham/neuroflow/issues)

## 🎓 下一步

完成本教程后，你可以:

1. **[学习工具系统](../concepts/tools.md)** - 深入理解工具开发
2. **[使用 MCP 服务](../guides/using-mcp.md)** - 集成外部 API
3. **[查看进阶示例](../examples/advanced.md)** - 学习复杂场景

---

**继续学习**: [概念指南 - Agent 基础](../concepts/agents.md) →
