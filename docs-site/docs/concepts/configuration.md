# 配置管理

NeuroFlow 使用 YAML 配置文件管理所有组件。

## 配置文件结构

```yaml
# config/neuroflow.yaml

# 服务器配置
server:
  host: 127.0.0.1
  port: 8080
  max_connections: 100

# 沙箱配置
sandbox:
  max_instances: 10
  memory_limit_mb: 256
  timeout_ms: 30000

# 可观测性配置
observability:
  tracing_enabled: true
  metrics_enabled: true
  log_level: info

# 安全配置
security:
  rate_limit_rpm: 1000
  request_size_limit_kb: 1024
  cors_enabled: true
```

## 环境覆盖

```bash
# 使用环境变量覆盖配置
export NEUROFLOW_PORT=9090
export NEUROFLOW_LOG_LEVEL=debug
```

## 多环境配置

```yaml
# config/development.yaml
server:
  port: 8080
observability:
  log_level: debug

# config/production.yaml
server:
  port: 80
observability:
  log_level: warning
```

## 配置验证

```bash
# 验证配置
neuroflow config validate

# 查看当前配置
neuroflow config show
```

## 最佳实践

### 1. 使用版本控制

```bash
git add config/neuroflow.yaml
```

### 2. 敏感信息使用环境变量

```yaml
# ❌ 坏：硬编码密钥
security:
  api_key: "sk-123456"

# ✅ 好：使用环境变量
security:
  api_key: ${API_KEY}
```

### 3. 环境特定配置

```bash
# 开发环境
neuroflow run --config config/development.yaml

# 生产环境
neuroflow run --config config/production.yaml
```

## 相关文档

- [架构概览](architecture.md)
- [部署指南](../guides/deployment.md)
