# 安全实践

NeuroFlow 安全最佳实践指南。

## 安全原则

1. **最小权限原则** - Agent 只拥有必要的权限
2. **沙箱隔离** - Agent 代码在沙箱中运行
3. **输入验证** - 所有输入都需要验证
4. **安全通信** - 使用加密通信

## Agent 安全

### 1. 权限控制

```python
from neuroflow import AINativeAgent, AINativeAgentConfig

# 限制 Agent 权限
config = AINativeAgentConfig(
    name="restricted_agent",
    enable_memory=True,  # 只启用必要的功能
    max_memory_items=100,  # 限制记忆数量
)

agent = AINativeAgent(config)
```

### 2. 工具安全

```python
# 验证工具输入
@agent.tool(name="safe_calculate", description="安全计算器")
async def safe_calculate(expression: str) -> float:
    # 只允许数字和基本运算符
    allowed = set('0123456789+-*/(). ')
    if not all(c in allowed for c in expression):
        raise ValueError("Invalid characters")
    return float(eval(expression, {"__builtins__": {}}, {}))
```

### 3. 资源限制

```python
# 设置超时
from neuroflow.tools import ToolCall

call = ToolCall(
    tool_id="tool_1",
    tool_name="my_tool",
    arguments={},
    timeout_ms=5000,  # 5 秒超时
)
```

## 沙箱安全

### WASM 沙箱

```rust
// Rust Kernel 中的沙箱配置
let config = SandboxConfig {
    memory_limit_mb: 256,
    cpu_limit: 0.5,
    timeout_ms: 30000,
    allowed_hosts: vec!["localhost".to_string()],
    allowed_paths: vec!["/tmp".to_string()],
};
```

### Python 沙箱

```python
# 安全的执行环境
def create_safe_globals():
    return {
        '__builtins__': {
            'len': len,
            'str': str,
            # 只允许安全的内置函数
        }
    }
```

## 通信安全

### 1. API 鉴权

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer

app = FastAPI()
security = HTTPBearer()

async def verify_token(credentials: HTTPBearer = Depends(security)):
    token = credentials.credentials
    if not is_valid_token(token):
        raise HTTPException(status_code=401)
    return token
```

### 2. 速率限制

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/tools/invoke")
@limiter.limit("100/minute")  # 每分钟 100 次
async def invoke_tool(request: Request):
    pass
```

### 3. 输入验证

```python
from pydantic import BaseModel, validator

class ToolInvokeRequest(BaseModel):
    tool_name: str
    arguments: dict
    timeout_ms: int = 30000
    
    @validator('tool_name')
    def validate_tool_name(cls, v):
        if not v.isidentifier():
            raise ValueError("Invalid tool name")
        return v
    
    @validator('timeout_ms')
    def validate_timeout(cls, v):
        if v < 0 or v > 60000:
            raise ValueError("Timeout must be 0-60000ms")
        return v
```

## 数据安全

### 1. 敏感数据处理

```python
# 不记录敏感数据
import logging

logger = logging.getLogger(__name__)

def process_sensitive_data(data):
    # 脱敏处理
    sanitized = {k: "***" if k in ["password", "token"] else v 
                 for k, v in data.items()}
    logger.info(f"Processing: {sanitized}")
```

### 2. 数据加密

```python
from cryptography.fernet import Fernet

# 加密记忆数据
key = Fernet.generate_key()
cipher = Fernet(key)

encrypted = cipher.encrypt(b"sensitive_data")
decrypted = cipher.decrypt(encrypted)
```

## 审计日志

```python
import logging
import json

# 配置审计日志
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)

def log_audit_event(event_type, user_id, action, result):
    audit_logger.info(json.dumps({
        'event_type': event_type,
        'user_id': user_id,
        'action': action,
        'result': result,
        'timestamp': datetime.utcnow().isoformat(),
    }))
```

## 安全检查清单

- [ ] Agent 权限最小化
- [ ] 工具输入验证
- [ ] 资源限制设置
- [ ] API 鉴权启用
- [ ] 速率限制配置
- [ ] 敏感数据脱敏
- [ ] 审计日志启用

---

**相关文档**: [Agent 设计](agent-design.md) | [配置管理](../concepts/configuration.md)
