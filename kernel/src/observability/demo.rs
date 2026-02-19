//! 可观测性功能演示

use crate::observability::{ObservabilityService, ObservabilityConfig, SimpleMetrics, RequestTimer};
use std::time::Duration;
use tokio::time::sleep;

/// 演示可观测性功能
pub async fn demo_observability() -> Result<(), Box<dyn std::error::Error>> {
    println!("=== NeuroFlow 可观测性功能演示 ===\n");
    
    // 创建可观测性服务
    let config = ObservabilityConfig {
        service_name: "neuroflow-demo".to_string(),
        tracing_enabled: false, // 避免测试环境中的全局追踪器冲突
        metrics_enabled: true,
        ..Default::default()
    };
    
    let service = ObservabilityService::new(config)?;
    println!("✓ 可观测性服务初始化成功");
    
    // 演示指标收集
    println!("\n--- 指标收集演示 ---");
    
    // 模拟HTTP请求计数
    service.metrics.inc_counter("http_requests_total");
    service.metrics.inc_counter("http_requests_total");
    service.metrics.inc_counter("http_requests_total");
    
    // 模拟系统资源指标
    service.metrics.set_gauge("memory_usage_bytes", 1024.0 * 1024.0 * 150.0); // 150MB
    service.metrics.set_gauge("cpu_usage_percent", 35.2);
    
    // 模拟请求处理时间
    {
        let _timer = RequestTimer::new((*service.metrics).clone(), "http_request_duration_seconds".to_string());
        sleep(Duration::from_millis(50)).await;
    }
    
    {
        let _timer = RequestTimer::new((*service.metrics).clone(), "http_request_duration_seconds".to_string());
        sleep(Duration::from_millis(75)).await;
    }
    
    // 显示收集到的指标
    println!("收集到的指标:");
    let metrics_text = service.get_metrics_text()?;
    println!("{}", metrics_text);
    
    // 显示直方图统计
    if let Some(stats) = service.metrics.get_histogram_stats("http_request_duration_seconds") {
        println!("请求处理时间统计:");
        println!("  总次数: {}", stats.count);
        println!("  总耗时: {:.3}秒", stats.sum);
        println!("  平均耗时: {:.3}秒", stats.avg);
        println!("  最小耗时: {:.3}秒", stats.min);
        println!("  最大耗时: {:.3}秒", stats.max);
    }
    
    // 模拟系统指标更新
    println!("\n--- 系统指标更新演示 ---");
    service.update_system_metrics()?;
    
    let updated_metrics = service.get_metrics_text()?;
    println!("更新后的系统指标:");
    for line in updated_metrics.lines() {
        if line.contains("system_") {
            println!("  {}", line);
        }
    }
    
    println!("\n=== 演示完成 ===");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_observability_demo() {
        // 运行演示但不检查输出，只确保不panic
        let result = demo_observability().await;
        assert!(result.is_ok());
    }
}