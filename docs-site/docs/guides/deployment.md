# 部署指南

## 本地部署

### 开发模式

```bash
# 启动开发服务器
neuroflow run --reload --log-level debug
```

### 生产模式

```bash
# 使用 Gunicorn
pip install gunicorn

gunicorn neuroflow.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8080
```

## Docker 部署

### 创建 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 复制依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["neuroflow", "run", "--port", "8080"]
```

### 构建和运行

```bash
# 构建镜像
docker build -t my-agent:latest .

# 运行容器
docker run -p 8080:8080 my-agent:latest

# 后台运行
docker run -d -p 8080:8080 --name my-agent my-agent:latest
```

## Kubernetes 部署

### 创建部署配置

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: neuroflow-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: neuroflow-agent
  template:
    metadata:
      labels:
        app: neuroflow-agent
    spec:
      containers:
      - name: agent
        image: my-agent:latest
        ports:
        - containerPort: 8080
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "250m"
```

### 部署

```bash
# 应用配置
kubectl apply -f k8s/deployment.yaml

# 查看状态
kubectl get pods

# 查看日志
kubectl logs -f deployment/neuroflow-agent
```

## 监控和日志

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8080/health

# 检查指标
curl http://localhost:8080/metrics
```

### 日志收集

```bash
# 查看实时日志
neuroflow logs --follow

# 查看错误日志
neuroflow logs --level error

# 导出日志
neuroflow logs --output logs.txt
```

## 最佳实践

### 1. 使用环境变量

```yaml
# docker-compose.yml
services:
  agent:
    image: my-agent:latest
    environment:
      - NEUROFLOW_LOG_LEVEL=info
      - NEUROFLOW_PORT=8080
```

### 2. 配置健康检查

```yaml
# docker-compose.yml
services:
  agent:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 3. 资源限制

```yaml
# k8s/deployment.yaml
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "250m"
```

## 相关文档

- [配置管理](../concepts/configuration.md)
- [性能优化](../best-practices/performance.md)
