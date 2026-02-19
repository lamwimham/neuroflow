# NeuroFlow 故障排除指南

**版本**: v0.4.0  
**最后更新**: 2026-02-19

---

## ❌ 常见错误及解决方案

### 错误 1: AINativeAgentConfig.__init__() missing 1 required positional argument: 'name'

**错误信息**:
```
❌ 运行失败：AINativeAgentConfig.__init__() missing 1 required positional argument: 'name'
```

**原因**: 创建 `AINativeAgentConfig` 时缺少必需的 `name` 参数。

**解决方案 1**: 使用 `neuroflow agent create` 命令创建 Agent

```bash
# 正确方式：使用 CLI 创建
neuroflow agent create assistant --description="智能助手"
```

这会自动生成正确的 Agent 代码模板。

**解决方案 2**: 手动修复 Agent 文件

确保你的 Agent 类正确初始化：

```python
# ❌ 错误示例
class MyAgent(AINativeAgent):
    def __init__(self):
        # 错误：缺少 name 参数
        super().__init__(AINativeAgentConfig())

# ✅ 正确示例
class MyAgent(AINativeAgent):
    def __init__(self):
        # 正确：提供所有必需参数
        super().__init__(
            AINativeAgentConfig(
                name="my_agent",           # 必需
                description="我的 Agent",   # 可选
                llm_config=LLMConfig(      # 可选
                    provider="openai",
                    model="gpt-4",
                ),
            )
        )
```

**完整示例** (`agents/assistant.py`):
```python
"""
Assistant Agent

智能助手 Agent
"""
import asyncio
from neuroflow import AINativeAgent, AINativeAgentConfig, LLMConfig


class AssistantAgent(AINativeAgent):
    """智能助手 Agent"""
    
    def __init__(self):
        super().__init__(
            AINativeAgentConfig(
                name="assistant",
                description="智能助手",
                llm_config=LLMConfig(
                    provider="openai",
                    model="gpt-4",
                ),
            )
        )
        
        # 注册工具
        self._register_tools()
    
    def _register_tools(self):
        """注册 Agent 专用工具"""
        
        @self.tool(name="greet", description="问候用户")
        async def greet(name: str) -> str:
            """问候用户"""
            return f"你好，{name}! 我是 assistant，很高兴为你服务。"
    
    async def handle_request(self, user_message: str) -> dict:
        """处理用户请求"""
        return await self.handle(user_message)


async def main():
    """测试 Agent"""
    agent = AssistantAgent()
    
    # 测试
    print("=" * 50)
    print(f"测试：{agent.config.description}")
    print("=" * 50)
    
    result = await agent.handle_request("你好")
    print(f"响应：{result['response']}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

### 错误 2: ModuleNotFoundError: No module named 'neuroflow'

**错误信息**:
```
❌ 运行失败：No module named 'neuroflow'
```

**原因**: NeuroFlow SDK 未安装或未正确安装。

**解决方案**:
```bash
# 进入 SDK 目录
cd sdk

# 重新安装
pip install -e .

# 验证安装
neuroflow --version
```

---

### 错误 3: OPENAI_API_KEY not found

**错误信息**:
```
❌ 运行失败：OPENAI_API_KEY not found
```

**原因**: 未设置 LLM API Key 环境变量。

**解决方案**:
```bash
# 设置环境变量
export OPENAI_API_KEY="your-api-key"

# 或添加到 ~/.bashrc 或 ~/.zshrc
echo 'export OPENAI_API_KEY="your-api-key"' >> ~/.bashrc
source ~/.bashrc
```

---

### 错误 4: Agent 'xxx' not found

**错误信息**:
```
❌ Agent 'xxx' 未找到
   位置：agents/xxx.py
```

**原因**: Agent 文件不存在或路径错误。

**解决方案**:
```bash
# 1. 查看所有 Agent
neuroflow agent list

# 2. 创建 Agent
neuroflow agent create assistant --description="智能助手"

# 3. 确认文件存在
ls -la agents/
```

---

### 错误 5: 未找到 main() 函数

**警告信息**:
```
⚠️  警告：未找到 main() 函数
💡 提示：在脚本中添加 async def main(): 函数
```

**原因**: 脚本中没有 `main()` 函数。

**解决方案**: 添加 `main()` 函数

```python
# 添加这个函数到你的脚本中
async def main():
    """主函数"""
    # 你的代码
    pass


if __name__ == "__main__":
    asyncio.run(main())
```

---

### 错误 6: neuroflow: command not found

**错误信息**:
```
bash: neuroflow: command not found
```

**原因**: CLI 未安装或不在 PATH 中。

**解决方案**:
```bash
# 1. 重新安装
cd sdk
pip install -e .

# 2. 检查安装位置
which neuroflow

# 3. 添加到 PATH (如果需要)
export PATH=$PATH:$(python3 -m site --user-base)/bin
```

---

### 错误 7: Skill 'xxx' already exists

**错误信息**:
```
❌ Skill 'xxx' 已存在
   使用 --force 选项覆盖
```

**原因**: Skill 已存在。

**解决方案**:
```bash
# 方案 1: 使用不同的名称
neuroflow skill create my-skill-v2 --description="新版本"

# 方案 2: 覆盖已存在的 Skill
neuroflow skill create xxx --description="新描述" --force
```

---

### 错误 8: 权限错误 (Permission Denied)

**错误信息**:
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**原因**: 没有写入系统 Python 目录的权限。

**解决方案**:
```bash
# 方案 1: 使用 --user 安装
pip install --user -e .

# 方案 2: 使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -e .

# 方案 3: 使用 sudo (不推荐)
sudo pip install -e .
```

---

## 🔍 调试技巧

### 启用详细模式

```bash
# 大多数命令支持 -v 选项
neuroflow agent run assistant "你好" --verbose
neuroflow run app.py --verbose
neuroflow skill validate my-skill --verbose
```

### 查看堆栈跟踪

```bash
# 使用 --verbose 显示完整堆栈
neuroflow agent run assistant "你好" --verbose

# 或使用 Python 直接运行
python3 agents/assistant.py
```

### 检查环境变量

```bash
# 检查 API Key
echo $OPENAI_API_KEY

# 检查 Python 路径
echo $PYTHONPATH

# 检查 neuroflow 安装
which neuroflow
neuroflow --version
```

---

## 📚 相关文档

- [CLI 完整使用指南](CLI_COMPLETE_GUIDE.md)
- [Skills 使用指南](SKILLS_GUIDE.md)
- [架构与迭代讨论](ARCHITECTURE_AND_ITERATION.md)

---

## 🆘 获取帮助

如果以上方法都无法解决问题：

1. **查看日志**: 使用 `--verbose` 查看详细错误信息
2. **搜索 Issue**: [GitHub Issues](https://github.com/neuroflow/neuroflow/issues)
3. **提交 Issue**: 提供错误信息、环境信息、复现步骤

---

**版本**: v0.4.0  
**最后更新**: 2026-02-19
