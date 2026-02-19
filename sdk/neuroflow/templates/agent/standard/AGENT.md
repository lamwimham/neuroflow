# ${agent_name} Agent

**版本**: v0.4.1  
**创建日期**: $(date +%Y-%m-%d)  
**描述**: ${description}

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 设置 LLM API Key
export OPENAI_API_KEY="your-api-key"
# 或者使用 Anthropic
# export ANTHROPIC_API_KEY="your-api-key"
```

### 3. 运行 Agent

```bash
# 直接运行
python ${agent_name}.py

# 或使用 CLI
neuroflow agent run ${agent_name} "你好"
```

---

## 📁 项目结构

```
.
├── ${agent_name}.py          # Agent 主文件
├── config.yaml               # 配置文件
├── requirements.txt          # Python 依赖
├── AGENT.md                  # 本文件
├── workspace/                # 工作目录
│   └── .gitkeep
└── scripts/                  # 脚本目录
    └── .gitkeep
```

---

## ⚙️ 配置说明

### MCP 服务器

#### filesystem (已启用 ✅)

提供安全的文件读写能力：

- **允许路径**: `./${workspace_name}`, `./docs`
- **允许操作**: read, write, list
- **禁止操作**: delete, chmod
- **文件大小限制**: 10MB

#### memory (已启用 ✅)

提供长期记忆存储：

- **数据库路径**: `./${workspace_name}/memory.db`
- **最大记忆数**: 1000
- **自动清理**: 已启用

#### terminal (已禁用 ❌)

命令执行功能，**默认禁用**以确保安全。

如需启用，编辑 `config.yaml`:

```yaml
mcp:
  servers:
    - name: terminal
      enabled: true  # 修改这里
      config:
        mode: restricted
        allowed_commands:
          - ls
          - cat
          - grep
```

⚠️ **安全警告**: 启用 Terminal 前请仔细阅读安全文档。

---

## 🛠️ 自定义工具

编辑 `${agent_name}.py`，在 `_register_tools` 方法中添加：

```python
def _register_tools(self):
    """注册 Agent 专用工具"""
    
    @self.tool(name="greet", description="问候用户")
    async def greet(name: str) -> str:
        return f"你好，{name}!"
    
    # 添加你的工具
    @self.tool(name="my_tool", description="我的工具")
    async def my_tool(param: str) -> dict:
        # 实现逻辑
        return {"result": "success"}
```

---

## 📊 监控与日志

### 日志文件

- **Agent 日志**: `./${workspace_name}/agent.log`
- **审计日志**: `./${workspace_name}/audit.log`

### 查看日志

```bash
# 实时查看
tail -f workspace/agent.log

# 查看审计日志
tail -f workspace/audit.log
```

---

## 🔒 安全最佳实践

1. **API Key 管理**
   - ✅ 使用环境变量
   - ❌ 不要硬编码在代码中

2. **文件访问**
   - ✅ 限制在 workspace 目录内
   - ❌ 不要访问系统目录

3. **Terminal 使用**
   - ✅ 使用白名单模式
   - ✅ 设置资源限制
   - ❌ 不要启用危险命令

4. **审计日志**
   - ✅ 保持启用
   - ✅ 定期检查

---

## 🧪 测试

```bash
# 运行内置测试
python ${agent_name}.py

# 测试 MCP 连接
neuroflow agent validate ${agent_name}

# 测试工具
neuroflow tool test greet
```

---

## 📚 相关文档

- [CLI 使用指南](../../../docs/CLI_COMPLETE_GUIDE.md)
- [MCP 配置指南](../../../docs-site/docs/guides/mcp-configuration.md)
- [Terminal 安全文档](../../../docs-site/docs/guides/terminal-security.md)

---

## 🆘 故障排除

### 问题 1: MCP 连接失败

```bash
# 检查配置
cat config.yaml | grep -A 5 "filesystem"

# 检查路径权限
ls -la workspace/
```

### 问题 2: API Key 错误

```bash
# 检查环境变量
echo $OPENAI_API_KEY

# 重新设置
export OPENAI_API_KEY="sk-..."
```

### 问题 3: 工具执行失败

```bash
# 查看详细日志
tail -f workspace/agent.log
```

---

## 📝 更新日志

### v0.4.1 (2026-02-19)
- ✅ 初始版本
- ✅ 集成 filesystem MCP
- ✅ 集成 memory MCP
- ✅ Terminal 默认禁用

---

**创建者**: NeuroFlow CLI  
**许可证**: MIT
