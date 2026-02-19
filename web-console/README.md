# NeuroFlow Web Console

NeuroFlow Web Console 是一个基于 React + TypeScript 的 Web 管理界面，用于管理和监控 NeuroFlow Agent 系统。

## 功能特性

- ✅ **Dashboard** - 实时显示系统状态和指标
- ✅ **Agent 管理** - 创建、查看、删除 Agent
- ✅ **对话调试** - 实时与 Agent 对话测试
- ✅ **Skill 管理** - 查看和管理 Skills
- ✅ **监控面板** - 性能指标和日志查看
- ✅ **系统设置** - 配置系统参数

## 技术栈

- **前端**: React 18 + TypeScript
- **状态管理**: TanStack Query (React Query)
- **路由**: React Router v6
- **UI 组件**: TailwindCSS + Lucide Icons
- **图表**: Recharts
- **后端**: FastAPI (Python)

## 快速开始

### 1. 安装依赖

```bash
cd web-console
npm install
```

### 2. 启动开发服务器

```bash
# 启动前端
npm run dev

# 启动后端 (另一个终端)
python server.py
```

访问 http://localhost:3000

### 3. 构建生产版本

```bash
npm run build
```

## 项目结构

```
web-console/
├── src/
│   ├── api.ts              # API 客户端
│   ├── App.tsx             # 主应用组件
│   ├── main.tsx            # 入口文件
│   ├── index.css           # 全局样式
│   ├── components/
│   │   └── Layout.tsx      # 布局组件
│   └── pages/
│       ├── Dashboard.tsx   # Dashboard 页面
│       ├── Agents.tsx      # Agent 列表
│       ├── AgentDetail.tsx # Agent 详情
│       ├── Skills.tsx      # Skills 管理
│       ├── Monitoring.tsx  # 监控面板
│       └── Settings.tsx    # 设置页面
├── server.py               # 后端 API 服务
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/agents` | GET | 获取所有 Agent |
| `/api/agents/:id` | GET | 获取单个 Agent |
| `/api/agents` | POST | 创建 Agent |
| `/api/agents/:id` | DELETE | 删除 Agent |
| `/api/agents/:id/execute` | POST | 执行 Agent |
| `/api/skills` | GET | 获取所有 Skills |
| `/api/monitoring/metrics` | GET | 获取性能指标 |
| `/api/monitoring/logs` | GET | 获取日志 |
| `/api/mcp/servers` | GET | 获取 MCP 服务器 |

## 截图预览

### Dashboard
- 系统概览
- 实时指标
- 最近活动

### Agent 管理
- Agent 列表
- Agent 详情
- 对话调试

### 监控面板
- 性能图表
- 错误率
- 日志查看

## 开发

### 代码规范

```bash
npm run lint
```

### 类型检查

```bash
npx tsc --noEmit
```

## 部署

### Docker 部署

```bash
docker build -t neuroflow-web-console .
docker run -p 3000:3000 -p 8000:8000 neuroflow-web-console
```

### 生产环境

1. 构建前端：`npm run build`
2. 配置反向代理（Nginx/Apache）
3. 启动后端服务

## 许可证

MIT License

---

**NeuroFlow Team** | v0.5.0
