# NeuroFlow Skills使用手册

## 目录
1. [概述](#概述)
2. [快速开始](#快速开始)
3. [Skills文件结构](#skills文件结构)
4. [SKILL.md文件格式](#skillmd文件格式)
5. [开发Skills](#开发skills)
6. [注册和使用Skills](#注册和使用skills)
7. [最佳实践](#最佳实践)
8. [安全指南](#安全指南)

## 概述

NeuroFlow Skills是一种将领域知识和专业技能打包成可重用组件的机制。Skills使Agent能够：
- 扩展核心能力
- 执行专业任务
- 访问外部资源
- 集成自定义逻辑

Skills采用渐进式披露设计，分为三个层次：
1. **元数据层**：技能基本信息，始终加载
2. **说明层**：详细说明，按需加载
3. **资源层**：脚本和数据，按需访问

## 快速开始

### 创建第一个Skill

1. 创建技能目录结构：
```bash
mkdir -p my_skills/hello_world
```

2. 创建SKILL.md文件：
```bash
cat > my_skills/hello_world/SKILL.md << EOF
---
name: "hello_world"
description: "简单的问候技能"
version: "1.0.0"
author: "Your Name"
parameters:
  - name: "name"
    type: "string"
    required: true
    description: "被问候的人的名字"
---
# Hello World技能

## 功能描述
此技能用于向指定的人发送问候。

## 使用方法
1. 提供用户名字
2. 技能将返回问候语

## 示例
输入: {"name": "Alice"}
输出: "Hello, Alice! Welcome to NeuroFlow."
EOF
```

3. 在Python中使用：
```python
from neuroflow import BaseAgent, tool

class MyAgent(BaseAgent):
    pass

# 创建Agent实例
agent = MyAgent("my_agent", "My custom agent")

# 注册技能（如果需要）
# agent.register_skill(hello_world_function)

# 使用技能
result = await agent.execute_tool("hello_world", name="Alice")
print(result)  # 输出问候语
```

## Skills文件结构

### 标准目录结构

```
skills/
├── skill_name/              # 技能名称目录
│   ├── SKILL.md            # 技能定义文件（必需）
│   ├── config.json         # 配置文件（可选）
│   ├── scripts/            # 脚本文件
│   │   ├── main.py
│   │   └── utils.sh
│   ├── resources/          # 资源文件
│   │   ├── templates/
│   │   └── data/
│   └── examples/           # 示例文件
│       ├── example1.json
│       └── example2.json
```

### 文件说明

- **SKILL.md**：技能的核心定义文件，包含元数据和说明
- **config.json**：技能配置参数
- **scripts/**：可执行脚本文件
- **resources/**：技能使用的资源文件
- **examples/**：使用示例

## SKILL.md文件格式

### YAML前言

SKILL.md文件必须以YAML前言开始：

```yaml
---
name: "skill_identifier"           # 技能唯一标识符（必需）
description: "技能描述"           # 技能描述（必需）
version: "1.0.0"                 # 版本号（必需）
author: "开发者姓名"              # 作者（可选）
license: "许可证"                 # 许可证（可选）
tags: ["tag1", "tag2"]           # 标签（可选）
parameters:                      # 参数定义（可选）
  - name: "param_name"          # 参数名
    type: "string"              # 参数类型
    required: true              # 是否必需
    description: "参数描述"      # 参数描述
    default_value: "default"    # 默认值（可选）
---
```

### 参数类型

- `string`：字符串类型
- `number`：数值类型
- `boolean`：布尔类型
- `array`：数组类型
- `object`：对象类型

### 完整示例

```yaml
---
name: "data_analyzer"
description: "数据分析技能，支持多种数据格式的分析"
version: "1.0.0"
author: "Data Team"
license: "MIT"
tags: ["data", "analysis", "csv", "json"]
parameters:
  - name: "input_file"
    type: "string"
    required: true
    description: "输入数据文件路径"
  - name: "analysis_type"
    type: "string"
    required: false
    description: "分析类型：basic, detailed, statistical"
    default_value: "basic"
  - name: "output_format"
    type: "string"
    required: false
    description: "输出格式：json, csv, text"
    default_value: "json"
---
# 数据分析技能

## 功能描述
此技能提供数据分析能力，支持CSV、JSON等格式的数据分析。

## 支持的数据格式
- CSV文件
- JSON文件
- Excel文件

## 分析类型
- **basic**: 基础统计信息
- **detailed**: 详细分析报告
- **statistical**: 统计分析

## 使用方法
1. 准备数据文件
2. 选择分析类型
3. 执行技能

## 示例
```json
{
  "input_file": "/data/sales.csv",
  "analysis_type": "detailed",
  "output_format": "json"
}
```

## 限制
- 文件大小不超过100MB
- 支持的最大行数：100万行
```

## 开发Skills

### 1. Python技能开发

```python
from neuroflow import skill
import pandas as pd
import json

@skill(
    name="csv_analyzer",
    description="CSV文件分析技能",
    parameters={
        "file_path": {
            "type": "string",
            "required": True,
            "description": "CSV文件路径"
        },
        "columns": {
            "type": "array",
            "required": False,
            "description": "要分析的列名列表"
        }
    }
)
async def csv_analyzer(file_path: str, columns: list = None):
    """
    CSV文件分析技能实现
    """
    try:
        # 读取CSV文件
        df = pd.read_csv(file_path)
        
        # 如果指定了列，则只分析指定列
        if columns:
            df = df[columns]
        
        # 执行基本统计分析
        analysis_result = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "describe": df.describe().to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "sample_rows": df.head().to_dict('records')
        }
        
        return analysis_result
        
    except Exception as e:
        return {"error": str(e)}
```

### 2. 外部脚本技能

对于复杂的技能，可以使用外部脚本：

```python
@skill(
    name="external_analyzer",
    description="外部脚本分析技能",
    parameters={
        "input_file": {
            "type": "string",
            "required": True,
            "description": "输入文件路径"
        },
        "script_args": {
            "type": "string",
            "required": False,
            "description": "脚本参数"
        }
    }
)
async def external_analyzer(input_file: str, script_args: str = ""):
    """
    执行外部分析脚本
    """
    import subprocess
    import tempfile
    import os
    
    # 假设脚本位于skills目录下的scripts子目录
    script_path = os.path.join(
        os.path.dirname(__file__), 
        "skills", 
        "external_analyzer", 
        "scripts", 
        "analyzer.py"
    )
    
    try:
        result = subprocess.run([
            "python", script_path, input_file, script_args
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"error": result.stderr}
            
    except subprocess.TimeoutExpired:
        return {"error": "Script execution timed out"}
    except Exception as e:
        return {"error": str(e)}
```

### 3. 配置驱动的技能

```python
@skill(
    name="configurable_processor",
    description="可配置的数据处理器",
    parameters={
        "input_file": {
            "type": "string",
            "required": True,
            "description": "输入文件路径"
        },
        "config_file": {
            "type": "string",
            "required": False,
            "description": "配置文件路径"
        }
    }
)
async def configurable_processor(input_file: str, config_file: str = None):
    """
    使用配置文件进行数据处理
    """
    import json
    
    # 加载配置
    if config_file and os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        # 默认配置
        config = {
            "delimiter": ",",
            "encoding": "utf-8",
            "operations": ["clean", "transform", "validate"]
        }
    
    # 执行配置的操作
    result = {"input_file": input_file, "config": config, "steps": []}
    
    for operation in config.get("operations", []):
        step_result = await execute_operation(operation, input_file, config)
        result["steps"].append(step_result)
    
    return result

async def execute_operation(operation: str, input_file: str, config: dict):
    """
    执行单个操作
    """
    # 实现具体操作逻辑
    return {"operation": operation, "status": "completed"}
```

## 注册和使用Skills

### 1. 自动注册

Skills可以通过装饰器自动注册：

```python
from neuroflow import skill, BaseAgent

@skill(
    name="web_scraper",
    description="网页抓取技能",
    parameters={
        "url": {
            "type": "string",
            "required": True,
            "description": "目标URL"
        }
    }
)
async def web_scraper(url: str):
    """
    网页抓取实现
    """
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            return {
                "url": url,
                "status": response.status,
                "content_length": len(content),
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }

class WebAgent(BaseAgent):
    pass

# 使用技能
agent = WebAgent("web_agent", "Web scraping agent")
result = await agent.execute_tool("web_scraper", url="https://example.com")
```

### 2. 手动注册

```python
# 手动注册技能
agent.register_tool(web_scraper, 
                   name="web_scraper_manual",
                   description="手动注册的网页抓取技能")
```

### 3. 从目录加载Skills

```python
from neuroflow.skills import SkillsManager

# 创建技能管理器
skills_manager = SkillsManager()

# 从目录加载所有技能
await skills_manager.load_skills_from_directory("./my_skills")

# 列出可用技能
available_skills = skills_manager.list_available_skills()
print(f"Available skills: {available_skills}")

# 执行技能
result = await skills_manager.execute_skill("data_analyzer", 
                                         input_file="/data/sample.csv")
```

## 最佳实践

### 1. 从小开始
- 从简单的技能开始
- 逐步添加复杂功能
- 频繁测试和迭代

### 2. 结构化设计
- 合理组织文件结构
- 使用清晰的命名约定
- 保持技能职责单一

### 3. 详细文档
- 提供清晰的描述
- 包含使用示例
- 说明限制和约束

### 4. 错误处理
- 实现健壮的错误处理
- 提供有意义的错误信息
- 记录执行日志

### 5. 性能优化
- 优化资源使用
- 实现缓存机制
- 考虑并发处理

### 6. 安全考虑
- 验证输入参数
- 限制资源访问
- 实施权限控制

## 安全指南

### 1. 信任来源
- 仅安装来自可信源的技能
- 仔细审计第三方技能代码
- 避免使用未经验证的技能

### 2. 权限控制
- 实施最小权限原则
- 限制文件系统访问
- 控制网络连接

### 3. 输入验证
- 验证所有输入参数
- 防止注入攻击
- 实施参数范围检查

### 4. 监控和审计
- 记录技能执行日志
- 监控异常行为
- 实施资源使用限制

### 5. 代码扫描
- 自动扫描恶意代码
- 限制危险函数调用
- 实施白名单机制

## 故障排除

### 常见问题

1. **技能无法加载**
   - 检查SKILL.md格式是否正确
   - 验证YAML前言语法
   - 确认文件路径正确

2. **参数验证失败**
   - 检查参数类型是否匹配
   - 验证必需参数是否提供
   - 确认参数值在有效范围内

3. **执行超时**
   - 优化技能实现
   - 调整超时设置
   - 检查资源使用情况

4. **权限错误**
   - 检查文件访问权限
   - 验证网络访问设置
   - 确认安全策略配置

## 高级主题

### 1. 复合Skills

```python
@skill(
    name="data_pipeline",
    description="数据处理流水线",
    parameters={
        "input_file": {"type": "string", "required": True},
        "steps": {"type": "array", "required": True}
    }
)
async def data_pipeline(input_file: str, steps: list):
    """
    执行数据处理流水线
    """
    current_data = input_file
    
    for step in steps:
        step_name = step.get("name")
        step_params = step.get("params", {})
        
        # 根据步骤名称执行相应技能
        if step_name == "clean":
            current_data = await clean_data(current_data, **step_params)
        elif step_name == "transform":
            current_data = await transform_data(current_data, **step_params)
        elif step_name == "validate":
            current_data = await validate_data(current_data, **step_params)
    
    return {"final_data": current_data, "steps_executed": len(steps)}
```

### 2. 条件Skills

```python
@skill(
    name="conditional_processor",
    description="条件处理器",
    parameters={
        "input_data": {"type": "object", "required": True},
        "conditions": {"type": "array", "required": True}
    }
)
async def conditional_processor(input_data: dict, conditions: list):
    """
    根据条件执行不同处理
    """
    for condition in conditions:
        if evaluate_condition(input_data, condition):
            action = condition.get("action")
            params = condition.get("params", {})
            return await execute_action(action, input_data, **params)
    
    return {"message": "No conditions matched", "input": input_data}
```

### 3. 异步Skills

```python
@skill(
    name="async_processor",
    description="异步处理器",
    parameters={
        "tasks": {"type": "array", "required": True}
    }
)
async def async_processor(tasks: list):
    """
    并行执行多个任务
    """
    import asyncio
    
    async def execute_single_task(task):
        # 执行单个任务
        await asyncio.sleep(0.1)  # 模拟异步操作
        return {"task_id": task.get("id"), "status": "completed"}
    
    # 并行执行所有任务
    results = await asyncio.gather(
        *[execute_single_task(task) for task in tasks],
        return_exceptions=True
    )
    
    return {"results": results, "total_tasks": len(tasks)}
```

通过遵循本手册的指导，您将能够有效地开发、注册和使用NeuroFlow Skills，从而扩展Agent的能力并创建更强大的AI应用。