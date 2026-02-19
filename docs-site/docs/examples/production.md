# 生产示例

NeuroFlow 生产环境部署示例。

## 高可用部署

### Docker Compose 部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  neuroflow-api:
    image: neuroflow/sdk:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=INFO
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  neuroflow-kernel:
    image: neuroflow/kernel:latest
    deploy:
      replicas: 2
    environment:
      - RUST_LOG=info
    ports:
      - "8080:8080"

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf

volumes:
  redis-data:
```

### Nginx 配置

```nginx
# nginx.conf
upstream neuroflow_backend {
    least_conn;
    server neuroflow-api-1:8000;
    server neuroflow-api-2:8000;
    server neuroflow-api-3:8000;
}

server {
    listen 80;
    server_name api.neuroflow.ai;

    location / {
        proxy_pass http://neuroflow_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 30s;
        proxy_read_timeout 30s;
    }

    location /health {
        proxy_pass http://neuroflow_backend/health;
        access_log off;
    }
}
```

## 监控配置

### Prometheus 配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'neuroflow'
    static_configs:
      - targets: ['neuroflow-api:8000']
    metrics_path: '/metrics'

  - job_name: 'neuroflow-kernel'
    static_configs:
      - targets: ['neuroflow-kernel:8080']
    metrics_path: '/metrics'
```

### Grafana 仪表板

```json
{
  "dashboard": {
    "title": "NeuroFlow 监控",
    "panels": [
      {
        "title": "请求速率",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "响应时间",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"
          }
        ]
      },
      {
        "title": "错误率",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
          }
        ]
      }
    ]
  }
}
```

## 日志配置

### 结构化日志

```python
# logging_config.py
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# 配置
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())

logger = logging.getLogger('neuroflow')
logger.setLevel(logging.INFO)
logger.addHandler(handler)
```

### ELK Stack 配置

```yaml
# docker-compose.elk.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"

volumes:
  elasticsearch-data:
```

## 安全配置

### 环境变量

```bash
# .env
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
DATABASE_URL=postgresql://user:pass@localhost/neuroflow
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key
```

### API 鉴权

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    if not is_valid_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return token

@app.get("/api/tools/invoke")
async def invoke_tool(token: str = Depends(verify_token)):
    # 处理请求
    pass
```

## 性能优化

### 缓存配置

```python
from redis import Redis
from functools import wraps

redis = Redis(host='redis', port=6379)

def cache(ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            cached = redis.get(key)
            if cached:
                return json.loads(cached)
            result = await func(*args, **kwargs)
            redis.setex(key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache(ttl=600)
async def get_llm_response(prompt):
    return await llm.complete(prompt)
```

### 连接池

```python
import aiohttp
import asyncio

# 创建全局会话
session = None

async def init_session():
    global session
    session = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
        ),
        timeout=aiohttp.ClientTimeout(total=30),
    )

async def close_session():
    global session
    if session:
        await session.close()
```

---

**相关文档**: [基础示例](basic.md) | [部署应用](../guides/deployment.md)
