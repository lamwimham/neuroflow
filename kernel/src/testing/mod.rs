//! 测试模块
//! 提供各种测试功能，包括压力测试、安全测试、自动化测试等

pub mod stress;
pub mod security;
pub mod automation;  // 恢复

pub use stress::{StressTestConfig, StressTestResult, StressTester, PerformanceMonitor, BaselineMetrics, PerformanceAnalysis, StabilityRating};
pub use security::{SecurityTestConfig, SecurityTestResult, SecurityTester, SecuritySeverity, SecurityScanner, ScanReport, ScanSummary};
pub use automation::{AutomationTestConfig, TestSuiteResult, TestCaseResult, TestStatus, TestRunner, TestReportGenerator, TestReport, TestSummary, TestAssert, TestFixture};