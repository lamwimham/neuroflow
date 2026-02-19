# ${agent_name} - Advanced Template

**模板**: Advanced  
**描述**: ${description}  
**版本**: v0.4.1

---

## 🎯 适用场景

Advanced 模板适用于：
- ✅ 多 Agent 协作场景
- ✅ 复杂任务处理
- ✅ 生产环境部署
- ✅ 需要完整 MCP 功能

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
export OPENAI_API_KEY="your-api-key"
export ANTHROPIC_API_KEY="your-api-key"  # 如使用
```

### 3. 配置协作者 Agent

编辑 `config.yaml`，修改 `collaborators` 部分：

```yaml
collaborators:
  - name: data_analyst
    endpoint: "http://your-server:8081/agent/data_analyst"
```

### 4. 运行

```bash
python ${agent_name}.py
```

---

## 📁 项目结构

```
.
├── ${agent_name}.py          # Agent 主文件
├── config.yaml               # 配置文件
├── requirements.txt          # 依赖
├── AGENT.md                  # 本文件
├── workspace/                # 工作目录
├── scripts/                  # 脚本目录
├── data/                     # 数据目录
└── tests/                    # 测试目录
```

---

## ⚙️ 核心功能

### 1. 多 Agent 协作

```python
# 请求其他 Agent 协助
result = await agent.handle("分析这个数据并生成报告")
# 自动协调 data_analyst 和 code_reviewer
```

### 2. 完整 MCP 集成

- **filesystem**: 文件读写（允许删除操作）
- **memory**: 长期记忆（支持语义搜索）
- **terminal**: 命令执行（受限模式）

### 3. 高级安全

- API Key 环境变量管理
- 审计日志（DEBUG 级别）
- 速率限制
- 输入验证
- 输出过滤

### 4. 可观测性

- OpenTelemetry 追踪
- Prometheus 指标
- 详细日志

---

## 🔧 自定义配置

### 启用/禁用 MCP 服务器

```yaml
mcp:
  enabled: true
  
  servers:
    - name: filesystem
      enabled: true  # 修改这里
    - name: terminal
      enabled: false  # 禁用 Terminal
```

### 添加协作者 Agent

```yaml
collaborators:
  - name: new_agent
    description: "新 Agent 描述"
    capabilities:
      - text_generation
      - translation
    endpoint: "http://server:port/agent/new_agent"
```

### 调整性能配置

```yaml
performance:
  caching:
    enabled: true
    cache_size: 2000  # 增加缓存
  parallel_execution:
    max_workers: 8  # 增加工作线程
```

---

## 🧪 测试

```bash
# 运行测试
python ${agent_name}.py

# 测试 MCP 连接
neuroflow agent validate ${agent_name}

# 测试协作
neuroflow agent run ${agent_name} "请协调其他 Agent 完成这个任务"
```

---

## 📊 监控

### 查看指标

```bash
# Prometheus 指标
curl http://localhost:8000/metrics
```

### 查看追踪

```bash
# Jaeger UI
open http://localhost:16686
```

### 查看日志

```bash
tail -f workspace/agent.log
tail -f workspace/audit.log
```

---

## 🔒 安全最佳实践

1. **API Key**
   - ✅ 使用环境变量
   - ❌ 不要提交到 Git

2. **Terminal**
   - ✅ 使用受限模式
   - ✅ 设置资源限制
   - ❌ 不要启用危险命令

3. **文件访问**
   - ✅ 限制在 workspace 内
   - ✅ 定期审计日志

4. **协作**
   - ✅ 验证协作者身份
   - ✅ 使用 HTTPS

---

## 🆘 故障排除

### 问题 1: 协作者连接失败

```bash
# 检查协作者是否运行
curl http://localhost:8081/agent/data_analyst

# 检查网络
ping localhost
```

### 问题 2: MCP 连接失败

```bash
# 检查配置
cat config.yaml | grep -A 10 "mcp:"

# 检查路径权限
ls -la workspace/
```

### 问题 3: 性能问题

```bash
# 查看指标
curl http://localhost:8000/metrics

# 查看缓存命中率
grep "cache" workspace/agent.log
```

---

## 📚 相关文档

- [CLI 使用指南](../../../docs/CLI_COMPLETE_GUIDE.md)
- [多 Agent 协作](../../../docs-site/docs/guides/multi-agent-collaboration.md)
- [MCP 配置指南](../../../docs-site/docs/guides/mcp-configuration.md)
- [性能优化](../../../docs-site/docs/best-practices/performance.md)

---

**创建者**: NeuroFlow CLI  
**许可证**: MIT
