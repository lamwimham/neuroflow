//! 安全测试模块
//! 提供渗透测试、漏洞扫描等安全测试功能

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};
use tracing::{info, warn, error, debug};
use regex::Regex;
use reqwest::Client;
use std::time::Duration;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecurityTestConfig {
    /// 目标URL
    pub target_url: String,
    /// 测试类型列表
    pub test_types: Vec<String>,
    /// 测试深度 (low, medium, high)
    pub depth: String,
    /// 超时时间（秒）
    pub timeout_secs: u64,
    /// 是否包含破坏性测试
    pub include_exploitative: bool,
}

impl Default for SecurityTestConfig {
    fn default() -> Self {
        Self {
            target_url: "http://localhost:8080".to_string(),
            test_types: vec![
                "input_validation".to_string(),
                "auth_bypass".to_string(),
                "injection".to_string(),
                "csrf".to_string(),
            ],
            depth: "medium".to_string(),
            timeout_secs: 30,
            include_exploitative: false,
        }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct SecurityTestResult {
    pub test_name: String,
    pub severity: SecuritySeverity,
    pub description: String,
    pub recommendation: String,
    pub vulnerable: bool,
    pub details: Option<String>,
    pub timestamp: std::time::SystemTime,
}

#[derive(Debug, Clone, Serialize)]
pub enum SecuritySeverity {
    Low,
    Medium,
    High,
    Critical,
}

pub struct SecurityTester {
    config: SecurityTestConfig,
    client: Client,
}

impl SecurityTester {
    pub fn new(config: SecurityTestConfig) -> Self {
        Self {
            client: Client::new(),
            config,
        }
    }

    /// 执行安全测试套件
    pub async fn run_security_tests(&self) -> Result<Vec<SecurityTestResult>, Box<dyn std::error::Error>> {
        info!("Starting security tests on: {}", self.config.target_url);
        
        let mut results = Vec::new();
        
        for test_type in &self.config.test_types {
            match test_type.as_str() {
                "input_validation" => {
                    results.extend(self.test_input_validation().await);
                },
                "auth_bypass" => {
                    results.extend(self.test_authentication_bypass().await);
                },
                "injection" => {
                    results.extend(self.test_injection_attacks().await);
                },
                "csrf" => {
                    results.extend(self.test_csrf_vulnerabilities().await);
                },
                "headers" => {
                    results.extend(self.test_security_headers().await);
                },
                "cors" => {
                    results.extend(self.test_cors_policy().await);
                },
                "rate_limit" => {
                    results.extend(self.test_rate_limiting().await);
                },
                _ => {
                    warn!("Unknown test type: {}", test_type);
                }
            }
        }
        
        info!("Completed {} security tests", results.len());
        Ok(results)
    }

    /// 测试输入验证
    async fn test_input_validation(&self) -> Vec<SecurityTestResult> {
        let mut results = Vec::new();
        
        // 测试SQL注入
        let sql_payloads = vec![
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "%27%20OR%20%271%27=%271", // URL encoded
        ];
        
        for payload in sql_payloads {
            let test_result = self.test_payload_on_endpoint("/invoke", &payload).await;
            if test_result.vulnerable {
                results.push(SecurityTestResult {
                    test_name: "SQL Injection".to_string(),
                    severity: SecuritySeverity::High,
                    description: "Application appears vulnerable to SQL injection attacks".to_string(),
                    recommendation: "Use parameterized queries and input validation".to_string(),
                    vulnerable: true,
                    details: Some(format!("Payload '{}' caused unusual behavior", payload)),
                    timestamp: std::time::SystemTime::now(),
                });
                break; // Found vulnerability, no need to test other payloads
            }
        }
        
        // 测试XSS
        let xss_payloads = vec![
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ];
        
        for payload in xss_payloads {
            let test_result = self.test_payload_on_endpoint("/invoke", &payload).await;
            if test_result.vulnerable {
                results.push(SecurityTestResult {
                    test_name: "Cross-Site Scripting (XSS)".to_string(),
                    severity: SecuritySeverity::High,
                    description: "Application appears vulnerable to XSS attacks".to_string(),
                    recommendation: "Sanitize user inputs and use Content Security Policy".to_string(),
                    vulnerable: true,
                    details: Some(format!("Payload '{}' was reflected in response", payload)),
                    timestamp: std::time::SystemTime::now(),
                });
                break; // Found vulnerability, no need to test other payloads
            }
        }
        
        // 如果没有发现漏洞，添加一个"未发现漏洞"的结果
        if !results.iter().any(|r| r.test_name == "SQL Injection" || r.test_name == "Cross-Site Scripting (XSS)") {
            results.push(SecurityTestResult {
                test_name: "Input Validation".to_string(),
                severity: SecuritySeverity::Low,
                description: "Input validation tests completed".to_string(),
                recommendation: "Continue regular security testing".to_string(),
                vulnerable: false,
                details: Some("No obvious input validation vulnerabilities found".to_string()),
                timestamp: std::time::SystemTime::now(),
            });
        }
        
        results
    }

    /// 测试认证绕过
    async fn test_authentication_bypass(&self) -> Vec<SecurityTestResult> {
        let mut results = Vec::new();
        
        // 尝试常见的认证绕过技术
        let auth_bypass_attempts = vec![
            // 测试未授权访问
            ("GET", "/admin", None),
            ("GET", "/api/admin/users", None),
            ("POST", "/api/admin/settings", Some(r#"{"setting": "value"}"#.to_string())),
        ];
        
        for (method, endpoint, body) in auth_bypass_attempts {
            let url = format!("{}{}", self.config.target_url, endpoint);
            
            let response = match method {
                "GET" => {
                    self.client.get(&url)
                        .timeout(Duration::from_secs(self.config.timeout_secs))
                        .send().await
                },
                "POST" => {
                    let mut request_builder = self.client.post(&url)
                        .timeout(Duration::from_secs(self.config.timeout_secs));
                    
                    if let Some(ref body_content) = body {
                        request_builder = request_builder.body(body_content.clone());
                    }
                    
                    request_builder.send().await
                },
                _ => continue,
            };
            
            if let Ok(resp) = response {
                let status = resp.status();
                // 如果能够访问受保护的资源而无需认证，则可能存在认证绕过
                if status.is_success() && (endpoint.contains("admin") || endpoint.contains("protected")) {
                    results.push(SecurityTestResult {
                        test_name: "Authentication Bypass".to_string(),
                        severity: SecuritySeverity::Critical,
                        description: format!("Potentially accessible admin endpoint without authentication: {}", endpoint),
                        recommendation: "Implement proper authentication checks on all sensitive endpoints".to_string(),
                        vulnerable: true,
                        details: Some(format!("Status: {}, Endpoint: {}", status, endpoint)),
                        timestamp: std::time::SystemTime::now(),
                    });
                    break; // Found vulnerability
                }
            }
        }
        
        if results.is_empty() {
            results.push(SecurityTestResult {
                test_name: "Authentication Bypass".to_string(),
                severity: SecuritySeverity::Low,
                description: "Authentication bypass tests completed".to_string(),
                recommendation: "Ensure all sensitive endpoints require proper authentication".to_string(),
                vulnerable: false,
                details: Some("No obvious authentication bypasses found".to_string()),
                timestamp: std::time::SystemTime::now(),
            });
        }
        
        results
    }

    /// 测试注入攻击
    async fn test_injection_attacks(&self) -> Vec<SecurityTestResult> {
        let mut results = Vec::new();
        
        // 测试命令注入
        let cmd_injection_payloads = vec![
            "; ls",
            "| ls",
            "&& ls",
            "`ls`",
            "$(ls)",
        ];
        
        for payload in cmd_injection_payloads {
            // 尝试在可能易受攻击的参数中注入命令
            let test_url = format!("{}{}", self.config.target_url, "/invoke");
            let test_payload = serde_json::json!({
                "agent": "test",
                "payload": {
                    "param": format!("normal_value{}", payload)
                }
            });
            
            let response = self.client
                .post(&test_url)
                .timeout(Duration::from_secs(self.config.timeout_secs))
                .json(&test_payload)
                .send()
                .await;
                
            // 检查响应中是否包含命令执行的迹象
            if let Ok(resp) = response {
                let text = resp.text().await.unwrap_or_default();
                
                // 检查是否包含典型的命令输出特征
                if text.contains("total ") || text.contains(".txt") || text.contains(".log") {
                    results.push(SecurityTestResult {
                        test_name: "Command Injection".to_string(),
                        severity: SecuritySeverity::Critical,
                        description: "Application appears vulnerable to command injection".to_string(),
                        recommendation: "Never pass user input directly to system commands. Use safe APIs.".to_string(),
                        vulnerable: true,
                        details: Some("Response may contain command execution output".to_string()),
                        timestamp: std::time::SystemTime::now(),
                    });
                    break; // Found vulnerability
                }
            }
        }
        
        if results.is_empty() {
            results.push(SecurityTestResult {
                test_name: "Injection Attacks".to_string(),
                severity: SecuritySeverity::Low,
                description: "Injection attack tests completed".to_string(),
                recommendation: "Continue to validate all inputs and use safe APIs".to_string(),
                vulnerable: false,
                details: Some("No obvious injection vulnerabilities found".to_string()),
                timestamp: std::time::SystemTime::now(),
            });
        }
        
        results
    }

    /// 测试CSRF漏洞
    async fn test_csrf_vulnerabilities(&self) -> Vec<SecurityTestResult> {
        let mut results = Vec::new();
        
        // CSRF通常涉及测试是否验证了适当的CSRF令牌或来源头部
        let csrf_test_endpoints = vec![
            "/api/user/update",
            "/api/account/delete",
            "/api/settings/change",
        ];
        
        for endpoint in csrf_test_endpoints {
            let url = format!("{}{}", self.config.target_url, endpoint);
            
            // 发送缺少适当CSRF防护的请求
            let response = self.client
                .post(&url)
                .header("Origin", "https://malicious-site.com")
                .header("Referer", "https://malicious-site.com")
                .timeout(Duration::from_secs(self.config.timeout_secs))
                .send()
                .await;
                
            if let Ok(resp) = response {
                let status = resp.status();
                // 如果敏感操作可以在没有适当验证的情况下从外部站点发起，
                // 则可能存在CSRF漏洞
                if status.is_success() {
                    results.push(SecurityTestResult {
                        test_name: "CSRF Vulnerability".to_string(),
                        severity: SecuritySeverity::Medium,
                        description: format!("Endpoint {} may be vulnerable to CSRF", endpoint),
                        recommendation: "Implement CSRF tokens or SameSite cookies".to_string(),
                        vulnerable: true,
                        details: Some(format!("Request to {} succeeded without CSRF validation", endpoint)),
                        timestamp: std::time::SystemTime::now(),
                    });
                    break; // Found vulnerability
                }
            }
        }
        
        if results.is_empty() {
            results.push(SecurityTestResult {
                test_name: "CSRF Vulnerability".to_string(),
                severity: SecuritySeverity::Low,
                description: "CSRF tests completed".to_string(),
                recommendation: "Consider implementing CSRF protection for sensitive actions".to_string(),
                vulnerable: false,
                details: Some("No obvious CSRF vulnerabilities found".to_string()),
                timestamp: std::time::SystemTime::now(),
            });
        }
        
        results
    }

    /// 测试安全头部
    async fn test_security_headers(&self) -> Vec<SecurityTestResult> {
        let mut results = Vec::new();
        
        let response = self.client
            .get(&self.config.target_url)
            .timeout(Duration::from_secs(self.config.timeout_secs))
            .send()
            .await;
            
        if let Ok(resp) = response {
            let headers = resp.headers();
            let mut missing_headers = Vec::new();
            
            // 检查重要的安全头部
            let required_headers = [
                ("X-Content-Type-Options", "nosniff"),
                ("X-Frame-Options", "DENY"),
                ("X-XSS-Protection", "1; mode=block"),
                ("Strict-Transport-Security", "max-age=31536000"),
            ];
            
            for (header_name, expected_value) in &required_headers {
                if !headers.contains_key(*header_name) {
                    missing_headers.push((*header_name).to_string());
                } else {
                    // 检查值是否符合预期
                    if let Some(header_value) = headers.get(*header_name) {
                        if let Ok(value_str) = header_value.to_str() {
                            if !value_str.contains(expected_value) {
                                results.push(SecurityTestResult {
                                    test_name: format!("Security Header - {}", header_name),
                                    severity: SecuritySeverity::Medium,
                                    description: format!("Security header {} has unexpected value", header_name),
                                    recommendation: format!("Set {} header to recommended value: {}", header_name, expected_value),
                                    vulnerable: true,
                                    details: Some(format!("Expected '{}', got '{}'", expected_value, value_str)),
                                    timestamp: std::time::SystemTime::now(),
                                });
                            }
                        }
                    }
                }
            }
            
            if !missing_headers.is_empty() {
                results.push(SecurityTestResult {
                    test_name: "Missing Security Headers".to_string(),
                    severity: SecuritySeverity::Medium,
                    description: "Several important security headers are missing".to_string(),
                    recommendation: format!("Add security headers: {}", missing_headers.join(", ")),
                    vulnerable: true,
                    details: Some(format!("Missing headers: {}", missing_headers.join(", "))),
                    timestamp: std::time::SystemTime::now(),
                });
            }
        }
        
        if results.is_empty() {
            results.push(SecurityTestResult {
                test_name: "Security Headers".to_string(),
                severity: SecuritySeverity::Low,
                description: "Security headers check completed".to_string(),
                recommendation: "Maintain current security headers".to_string(),
                vulnerable: false,
                details: Some("Required security headers are present".to_string()),
                timestamp: std::time::SystemTime::now(),
            });
        }
        
        results
    }

    /// 测试CORS策略
    async fn test_cors_policy(&self) -> Vec<SecurityTestResult> {
        let mut results = Vec::new();
        
        let response = self.client
            .get(&self.config.target_url)
            .header("Origin", "https://malicious-site.com")
            .timeout(Duration::from_secs(self.config.timeout_secs))
            .send()
            .await;
            
        if let Ok(resp) = response {
            let headers = resp.headers();
            
            if let Some(cors_header) = headers.get("Access-Control-Allow-Origin") {
                if let Ok(cors_value) = cors_header.to_str() {
                    // 检查是否存在过于宽松的CORS策略
                    if cors_value == "*" {
                        results.push(SecurityTestResult {
                            test_name: "CORS Policy".to_string(),
                            severity: SecuritySeverity::High,
                            description: "CORS policy allows all origins ('*')".to_string(),
                            recommendation: "Restrict CORS policy to specific trusted domains only".to_string(),
                            vulnerable: true,
                            details: Some("Access-Control-Allow-Origin set to '*'".to_string()),
                            timestamp: std::time::SystemTime::now(),
                        });
                    } else if cors_value.contains("malicious-site.com") {
                        results.push(SecurityTestResult {
                            test_name: "CORS Policy".to_string(),
                            severity: SecuritySeverity::Critical,
                            description: "CORS policy allows malicious origin".to_string(),
                            recommendation: "Review and restrict CORS policy immediately".to_string(),
                            vulnerable: true,
                            details: Some(format!("Access-Control-Allow-Origin includes malicious domain: {}", cors_value)),
                            timestamp: std::time::SystemTime::now(),
                        });
                    }
                }
            } else {
                // 如果没有CORS头部，对于API通常是好的
                results.push(SecurityTestResult {
                    test_name: "CORS Policy".to_string(),
                    severity: SecuritySeverity::Low,
                    description: "No CORS headers present (appropriate for backend services)".to_string(),
                    recommendation: "Maintain restrictive CORS policy".to_string(),
                    vulnerable: false,
                    details: Some("No CORS headers detected, which is appropriate for backend services".to_string()),
                    timestamp: std::time::SystemTime::now(),
                });
            }
        }
        
        results
    }

    /// 测试速率限制
    async fn test_rate_limiting(&self) -> Vec<SecurityTestResult> {
        let mut results = Vec::new();
        
        // 快速发送多个请求以测试速率限制
        let mut success_count = 0;
        let mut error_count = 0;
        
        for i in 0..50 {  // 发送50个请求
            let response = self.client
                .get(&self.config.target_url)
                .timeout(Duration::from_secs(self.config.timeout_secs))
                .send()
                .await;
                
            if let Ok(resp) = response {
                let status = resp.status();
                if status.is_success() {
                    success_count += 1;
                } else if status.as_u16() == 429 {  // Too Many Requests
                    error_count += 1;
                    break;  // Found rate limiting
                } else if status.is_client_error() || status.is_server_error() {
                    error_count += 1;
                }
            } else {
                error_count += 1;
            }
            
            // 短暂延迟以避免过于激进的请求
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
        
        // 如果没有遇到429错误，速率限制可能不足
        if error_count == 0 && success_count > 40 {
            results.push(SecurityTestResult {
                test_name: "Rate Limiting".to_string(),
                severity: SecuritySeverity::Medium,
                description: "Rate limiting may be insufficient".to_string(),
                recommendation: "Implement appropriate rate limiting to prevent abuse".to_string(),
                vulnerable: true,
                details: Some(format!("{} successful requests out of 50 tested, no rate limiting detected", success_count)),
                timestamp: std::time::SystemTime::now(),
            });
        } else if error_count > 0 {
            results.push(SecurityTestResult {
                test_name: "Rate Limiting".to_string(),
                severity: SecuritySeverity::Low,
                description: "Rate limiting appears to be active".to_string(),
                recommendation: "Ensure rate limits are appropriate for your use case".to_string(),
                vulnerable: false,
                details: Some(format!("Detected rate limiting after {} requests", success_count + error_count)),
                timestamp: std::time::SystemTime::now(),
            });
        }
        
        results
    }

    /// 辅助方法：测试特定载荷在端点上的行为
    async fn test_payload_on_endpoint(&self, endpoint: &str, payload: &str) -> SecurityTestResult {
        let url = format!("{}{}", self.config.target_url, endpoint);
        
        let test_payload = serde_json::json!({
            "agent": "test",
            "payload": {
                "input": payload
            }
        });
        
        let response = self.client
            .post(&url)
            .timeout(Duration::from_secs(self.config.timeout_secs))
            .json(&test_payload)
            .send()
            .await;
            
        match response {
            Ok(resp) => {
                let status = resp.status();
                let text = resp.text().await.unwrap_or_default();
                
                // 检查响应中是否包含可能表示漏洞的特征
                let has_vulnerability_indicators = 
                    text.contains(payload) ||  // 反射输入
                    text.contains("error") ||  // 错误消息
                    text.contains("exception") ||  // 异常
                    text.to_lowercase().contains("sql") ||  // SQL错误
                    status.is_server_error();  // 服务器错误
                
                SecurityTestResult {
                    test_name: "Payload Test".to_string(),
                    severity: if has_vulnerability_indicators { 
                        SecuritySeverity::Medium 
                    } else { 
                        SecuritySeverity::Low 
                    },
                    description: format!("Payload '{}' test on endpoint '{}'", payload, endpoint),
                    recommendation: "Review input handling and sanitization".to_string(),
                    vulnerable: has_vulnerability_indicators,
                    details: Some(format!("Status: {}, Contains indicators: {}", status, has_vulnerability_indicators)),
                    timestamp: std::time::SystemTime::now(),
                }
            },
            Err(_) => SecurityTestResult {
                test_name: "Payload Test".to_string(),
                severity: SecuritySeverity::Low,
                description: format!("Could not test payload '{}' on endpoint '{}'", payload, endpoint),
                recommendation: "".to_string(),
                vulnerable: false,
                details: Some("Request failed".to_string()),
                timestamp: std::time::SystemTime::now(),
            }
        }
    }
}

/// 安全扫描器
pub struct SecurityScanner {
    testers: HashMap<String, Arc<SecurityTester>>,
}

impl SecurityScanner {
    pub fn new() -> Self {
        Self {
            testers: HashMap::new(),
        }
    }

    pub fn add_tester(&mut self, name: String, tester: SecurityTester) {
        self.testers.insert(name, Arc::new(tester));
    }

    pub async fn run_scan(&self, scan_config: &SecurityTestConfig) -> ScanReport {
        info!("Starting security scan with config: {:?}", scan_config);
        
        let mut all_results = Vec::new();
        
        for (_, tester) in &self.testers {
            match tester.run_security_tests().await {
                Ok(results) => {
                    all_results.extend(results);
                }
                Err(e) => {
                    error!("Security test failed: {}", e);
                    all_results.push(SecurityTestResult {
                        test_name: "General Security Test".to_string(),
                        severity: SecuritySeverity::High,
                        description: format!("Security test failed: {}", e),
                        recommendation: "Check server availability and configuration".to_string(),
                        vulnerable: true,
                        details: Some(e.to_string()),
                        timestamp: std::time::SystemTime::now(),
                    });
                }
            }
        }
        
        ScanReport::new(all_results)
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct ScanReport {
    pub results: Vec<SecurityTestResult>,
    pub summary: ScanSummary,
    pub timestamp: std::time::SystemTime,
}

#[derive(Debug, Clone, Serialize)]
pub struct ScanSummary {
    pub total_tests: usize,
    pub vulnerabilities_found: usize,
    pub critical_vulnerabilities: usize,
    pub high_vulnerabilities: usize,
    pub medium_vulnerabilities: usize,
    pub low_vulnerabilities: usize,
    pub passed_tests: usize,
}

impl ScanReport {
    pub fn new(results: Vec<SecurityTestResult>) -> Self {
        let mut critical = 0;
        let mut high = 0;
        let mut medium = 0;
        let mut low = 0;
        let mut passed = 0;
        
        for result in &results {
            match result.severity {
                SecuritySeverity::Critical => critical += 1,
                SecuritySeverity::High => high += 1,
                SecuritySeverity::Medium => medium += 1,
                SecuritySeverity::Low => low += 1,
            }
            
            if !result.vulnerable {
                passed += 1;
            }
        }
        
        let vulnerabilities_found = critical + high + medium + low;
        
        Self {
            results,
            summary: ScanSummary {
                total_tests: results.len(),
                vulnerabilities_found,
                critical_vulnerabilities: critical,
                high_vulnerabilities: high,
                medium_vulnerabilities: medium,
                low_vulnerabilities: low,
                passed_tests: passed,
            },
            timestamp: std::time::SystemTime::now(),
        }
    }
    
    pub fn print_summary(&self) {
        println!("🛡️  Security Scan Summary");
        println!("=========================");
        println!("Total Tests: {}", self.summary.total_tests);
        println!("Passed: {}", self.summary.passed_tests);
        println!("Vulnerabilities Found: {}", self.summary.vulnerabilities_found);
        println!("  Critical: {}", self.summary.critical_vulnerabilities);
        println!("  High: {}", self.summary.high_vulnerabilities);
        println!("  Medium: {}", self.summary.medium_vulnerabilities);
        println!("  Low: {}", self.summary.low_vulnerabilities);
        println!();
        
        if self.summary.vulnerabilities_found > 0 {
            println!("⚠️  Vulnerabilities Detected:");
            for result in &self.results {
                if result.vulnerable {
                    let severity = match result.severity {
                        SecuritySeverity::Critical => "🚨 CRITICAL",
                        SecuritySeverity::High => "🔴 HIGH",
                        SecuritySeverity::Medium => "🟡 MEDIUM",
                        SecuritySeverity::Low => "🟢 LOW",
                    };
                    println!("  {} {}: {}", severity, result.test_name, result.description);
                }
            }
        } else {
            println!("✅ No vulnerabilities detected!");
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_security_tester_creation() {
        let config = SecurityTestConfig::default();
        let tester = SecurityTester::new(config);
        
        assert_eq!(tester.config.test_types.len(), 4);
        assert_eq!(tester.config.depth, "medium");
    }

    #[tokio::test]
    async fn test_scan_report_creation() {
        let results = vec![
            SecurityTestResult {
                test_name: "Test 1".to_string(),
                severity: SecuritySeverity::High,
                description: "Test description".to_string(),
                recommendation: "Fix it".to_string(),
                vulnerable: true,
                details: Some("Details".to_string()),
                timestamp: std::time::SystemTime::now(),
            }
        ];
        
        let report = ScanReport::new(results);
        
        assert_eq!(report.summary.total_tests, 1);
        assert_eq!(report.summary.vulnerabilities_found, 1);
        assert_eq!(report.summary.high_vulnerabilities, 1);
    }
}