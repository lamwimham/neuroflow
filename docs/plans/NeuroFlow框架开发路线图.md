## 🎯 NeuroFlow 框架 MVP 范围定义

### ✅ MVP 核心目标
> **让一个Python编写的Agent，能在NeuroFlow中：被路由→被隔离执行→被监控→被热更新**

### 📦 MVP 模块拆解（按依赖顺序）

| 模块 | 技术栈 | 核心功能 | 优先级 | 预估工时 |
|------|--------|----------|--------|----------|
| **1. Rust 内核骨架** | Rust + Tokio | 异步HTTP/gRPC网关、请求生命周期管理 | 🔴 P0 | 2周 |
| **2. 沙箱运行时** | WASMTime / Docker SDK | 启动隔离环境、注入Python代码、资源限制(CPU/Mem) | 🔴 P0 | 3周 |
| **3. 语义路由原型** | Python + SentenceTransformer + FAISS | 基于Embedding的请求→Agent技能匹配 | 🟡 P1 | 1.5周 |
| **4. 可观测性代理** | eBPF + OpenTelemetry | 采集请求延迟、Token消耗、异常日志 | 🟡 P1 | 2周 |
| **5. 热更新引擎** | Rust + inotify + 版本快照 | 监听代码变更→原子替换→触发重载 | 🟢 P2 | 2周 |
| **6. 护栏系统基础** | Python + 规则引擎 | PII检测、简单Prompt注入防御、白名单拦截 | 🟢 P2 | 1周 |

> ⏱️ **MVP 总周期**：并行开发约 **8-10周**（2-2.5个月），3人全栈团队可交付

### ❌ MVP 明确不包含（留待V2迭代）
- 自愈工作流（Diagnoser/Coder/Tester 三Agent协同）
- 多Agent协作通信总线
- 复杂风控规则引擎（先支持硬编码规则）
- 图形化运维控制台（先提供CLI + API）

---

## 🏗️ 技术架构细化（MVP版本）

```
┌─────────────────────────────────┐
│  接入层 (Rust/Tokio)             │
│  • HTTP/WebSocket 网关           │
│  • 请求鉴权 + 限流 + 日志        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  路由层 (Python Plugin)          │
│  • 加载Embedding模型 (ONNX加速)  │
│  • 向量检索匹配Agent技能         │
│  • 降级策略：匹配失败→默认Agent  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  沙箱编排器 (Rust Core)          │
│  • WASMTime 优先（轻量/秒级启动）│
│  • 资源配额：cgroups + seccomp   │
│  • 网络策略：仅允许白名单域名    │
│  • 通信通道：stdin/stdout + gRPC │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Agent 执行环境 (Python)         │
│  • 预装基础库：httpx, pydantic   │
│  • 注入上下文：session, config   │
│  • 暴露API：emit_metric, log     │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  可观测性管道                    │
│  • eBPF采集：系统调用/网络延迟   │
│  • OTel导出：Trace/Metric/Log    │
│  • 简单告警：阈值触发Webhook     │
└─────────────────────────────────┘
```

---

## 🚀 分阶段实施计划

### Phase 1：内核与沙箱（Week 1-4）🔴 关键路径
```
目标：能手动加载一个"Hello World" Python Agent 并隔离执行

✅ Week 1-2: Rust网关原型
   - [ ] Tokio异步HTTP服务器
   - [ ] 请求→路由层 的gRPC桥接
   - [ ] 基础日志中间件

✅ Week 3-4: WASM沙箱PoC
   - [ ] WASMTime嵌入Rust，加载Python编译的WASM模块
   - [ ] 实现CPU/Memory硬限制
   - [ ] 定义Agent入口规范：`async def handle(request) -> response`
   - [ ] 端到端测试：HTTP请求 → Rust → WASM-Python → 响应

🎯 验收标准：
   • curl发送请求，能触发沙箱内Python代码执行
   • 沙箱CPU超限自动终止，不影响主进程
   • 单次请求端到端延迟 < 50ms（不含业务逻辑）
```

### Phase 2：路由与可观测（Week 5-7）🟡
```
目标：支持多Agent注册，基于语义自动分发，并采集基础指标

✅ Week 5: 语义路由原型
   - [x] Python插件加载Sentence-BERT（ONNX格式）
   - [x] FAISS向量索引：Agent技能描述→embedding
   - [x] 请求query编码→相似度匹配→路由决策

✅ Week 6-7: 可观测性集成
   - [x] eBPF采集：系统调用延迟、网络IO
   - [x] OpenTelemetry SDK注入Agent环境
   - [x] 简单Dashboard：Grafana + Prometheus 展示QPS/延迟/错误率

🎯 验收标准：
   • 注册2个Agent（如"echo"和"calc"），自然语言请求能正确路由
   • 每个请求生成TraceID，可追踪完整链路
   • Token消耗/执行时长自动上报
```

### Phase 3：热更新与护栏（Week 8-10）🟢
```
目标：支持Agent代码热替换，基础安全防护

⏳ Week 8-9: 热更新引擎
   - [ ] inotify监听Agent代码目录变更
   - [ ] 版本快照：保留上一稳定版本
   - [ ] 原子替换：新代码验证通过后切换流量
   - [ ] 回滚机制：新版本异常自动切回

⏳ Week 10: 护栏系统基础
   - [ ] 规则引擎：YAML配置拦截规则
   - [ ] PII检测：正则+轻量NER模型
   - [ ] Prompt注入防御：关键词+语义异常检测

🎯 验收标准：
   • 修改Agent Python文件，30秒内生效，无服务重启
   • 恶意prompt（如"忽略之前指令"）被拦截并告警
   • 热更失败时，自动回滚且告警
```

---

## 👥 团队角色与资源建议

| 角色 | 人数 | 核心职责 | 技能要求 |
|------|------|----------|----------|
| **Rust 系统工程师** | 1-2 | 内核网关、沙箱编排、热更新引擎 | Tokio, WASMTime, eBPF, Linux syscall |
| **Python/AI 工程师** | 1 | 路由逻辑、护栏规则、Agent SDK | PyTorch/ONNX, 向量检索, 安全合规 |
| **DevOps/SRE** | 0.5 | 可观测性 pipeline、CI/CD、压测 | Prometheus, Grafana, k8s, 压测工具 |
| **技术负责人** | 1 | 架构决策、模块集成、风险控制 | 全栈视野 + 金融/Agent 领域经验 |

> 💡 **启动建议**：初期可2人全职（1 Rust + 1 Python），DevOps由现有基础设施团队支持

---

## ⚠️ 关键风险与应对策略

| 风险点 | 影响 | 缓解措施 |
|--------|------|----------|
| **WASM 对 Python 支持不成熟** | 沙箱方案延期 | ✅ 备选：Docker+gVisor（稍重但稳定）<br>✅ 并行PoC：WASMTime vs Docker，2周内决策 |
| **语义路由准确率不足** | Agent调用错误 | ✅ MVP阶段支持"路由置信度阈值"，低置信度转人工/默认Agent<br>✅ 记录bad case，为后续fine-tune积累数据 |
| **热更新导致状态不一致** | 交易场景致命 | ✅ MVP先支持"无状态Agent"，状态外置到Redis<br>✅ 热更前 draining：等待在飞请求完成 |
| **eBPF 兼容性问题** | 可观测性缺失 | ✅ 优先用OpenTelemetry标准埋点<br>✅ eBPF作为增强选项，非MVP强依赖 |

---

## 📋 下一步行动清单（Week 1）

1. [ ] **技术决策会**：确认沙箱方案（WASMTime vs Docker），本周内PoC对比
2. [ ] **仓库初始化**：
   ```bash
   neuroflow/
   ├── kernel/          # Rust 内核
   ├── plugins/         # Python 路由/护栏插件
   ├── sdk/             # Agent 开发SDK（Python）
   ├── examples/        # 示例Agent
   └── docs/            # 架构设计/API文档
   ```
3. [ ] **定义Agent接口规范**（草案）：
   ```python
   # sdk/neuroflow/agent.py
   class Agent:
       metadata: dict  # name, skills, version
       async def handle(self, request: Request, context: Context) -> Response: ...
       async def on_health_check(self) -> bool: ...
   ```
4. [ ] **搭建CI/CD基础**：GitHub Actions + 多架构Docker构建（为后续k8s部署铺垫）