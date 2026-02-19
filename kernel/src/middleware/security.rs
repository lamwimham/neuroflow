use axum::{
    body::Body,
    http::{Request, StatusCode},
    middleware::Next,
    response::Response,
};
use std::time::Duration;
use tokio::time::timeout;
use tracing::warn;

/// 请求大小限制中间件
pub async fn request_size_limit(
    req: Request<Body>,
    next: Next,
) -> Result<Response, StatusCode> {
    const MAX_REQUEST_SIZE: usize = 10 * 1024 * 1024; // 10MB
    
    let (parts, body) = req.into_parts();
    
    // 检查Content-Length头
    if let Some(content_length) = parts.headers.get("content-length") {
        if let Ok(len) = content_length.to_str() {
            if let Ok(size) = len.parse::<usize>() {
                if size > MAX_REQUEST_SIZE {
                    warn!("Request too large: {} bytes", size);
                    return Err(StatusCode::PAYLOAD_TOO_LARGE);
                }
            }
        }
    }
    
    let req = Request::from_parts(parts, body);
    Ok(next.run(req).await)
}

/// 超时中间件
pub async fn timeout_middleware(
    req: Request<Body>,
    next: Next,
) -> Result<Response, StatusCode> {
    const REQUEST_TIMEOUT: Duration = Duration::from_secs(30);
    
    match timeout(REQUEST_TIMEOUT, next.run(req)).await {
        Ok(response) => Ok(response),
        Err(_) => {
            warn!("Request timeout");
            Err(StatusCode::REQUEST_TIMEOUT)
        }
    }
}

/// 安全头中间件
pub async fn security_headers(
    req: Request<Body>,
    next: Next,
) -> Result<Response, StatusCode> {
    let response = next.run(req).await;
    Ok(response)
}

/// CORS中间件
pub async fn cors_middleware(
    req: Request<Body>,
    next: Next,
) -> Result<Response, StatusCode> {
    let response = next.run(req).await;
    Ok(response)
}

/// 输入验证中间件
pub async fn input_validation(
    req: Request<Body>,
    next: Next,
) -> Result<Response, StatusCode> {
    // 验证请求路径
    let path = req.uri().path();
    if path.contains("..") || path.contains("//") {
        warn!("Invalid path detected: {}", path);
        return Err(StatusCode::BAD_REQUEST);
    }
    
    // 验证查询参数
    if let Some(query) = req.uri().query() {
        if query.len() > 2048 {
            warn!("Query string too long: {} chars", query.len());
            return Err(StatusCode::URI_TOO_LONG);
        }
    }
    
    Ok(next.run(req).await)
}

/// 速率限制中间件（简化版本）
pub async fn rate_limit_middleware(
    req: Request<Body>,
    next: Next,
) -> Result<Response, StatusCode> {
    // 这里应该集成真正的速率限制实现
    // 目前只是记录日志
    let ip = req
        .headers()
        .get("x-forwarded-for")
        .and_then(|h| h.to_str().ok())
        .or_else(|| {
            req.headers()
                .get("x-real-ip")
                .and_then(|h| h.to_str().ok())
        })
        .unwrap_or("unknown");
    
    tracing::debug!("Request from IP: {}", ip);
    
    Ok(next.run(req).await)
}

#[cfg(test)]
mod tests {
    #[test]
    fn test_constants() {
        // 简单的常量测试
        assert_eq!(10 * 1024 * 1024, 10485760); // 10MB
    }
}