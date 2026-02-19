//! NeuroFlow文档生成模块
//! 提供API文档、使用指南、最佳实践等文档生成功能

use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use std::fs;
use std::path::Path;
use tracing::{info, error, debug};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocConfig {
    /// 文档输出目录
    pub output_dir: String,
    /// 文档主题
    pub theme: String,
    /// 是否包含私有API
    pub include_private: bool,
    /// 文档语言
    pub language: String,
}

impl Default for DocConfig {
    fn default() -> Self {
        Self {
            output_dir: "./docs/generated".to_string(),
            theme: "neuroflow".to_string(),
            include_private: false,
            language: "en".to_string(),
        }
    }
}

/// API文档生成器
pub struct ApiDocGenerator {
    config: DocConfig,
}

impl ApiDocGenerator {
    pub fn new(config: DocConfig) -> Self {
        Self { config }
    }

    /// 生成API文档
    pub fn generate_api_docs(&self) -> Result<(), Box<dyn std::error::Error>> {
        info!("Generating API documentation...");
        
        // 创建输出目录
        std::fs::create_dir_all(&self.config.output_dir)?;
        
        // 生成API文档主页
        let index_content = self.generate_index_page();
        let index_path = format!("{}/index.html", self.config.output_dir);
        std::fs::write(&index_path, index_content)?;
        debug!("Generated API index: {}", index_path);
        
        // 生成各模块文档
        self.generate_module_docs()?;
        
        // 生成配置文档
        self.generate_config_docs()?;
        
        // 生成CLI命令文档
        self.generate_cli_docs()?;
        
        info!("API documentation generated successfully in: {}", self.config.output_dir);
        Ok(())
    }

    fn generate_index_page(&self) -> String {
        format!(r#"<!DOCTYPE html>
<html lang="{}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NeuroFlow API Documentation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            text-align: center;
        }}
        .module-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }}
        .module-card {{
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .module-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }}
        .module-card h3 {{
            margin-top: 0;
            color: #4a5568;
        }}
        footer {{
            text-align: center;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #e2e8f0;
            color: #718096;
        }}
    </style>
</head>
<body>
    <header>
        <h1>NeuroFlow API Documentation</h1>
        <p>Comprehensive documentation for the NeuroFlow framework</p>
    </header>
    
    <main>
        <section>
            <h2>Modules</h2>
            <div class="module-list">
                <div class="module-card">
                    <h3>Config</h3>
                    <p>Configuration management module</p>
                    <a href="./config/index.html">View Documentation</a>
                </div>
                <div class="module-card">
                    <h3>Gateway</h3>
                    <p>HTTP gateway and routing</p>
                    <a href="./gateway/index.html">View Documentation</a>
                </div>
                <div class="module-card">
                    <h3>gRPC</h3>
                    <p>gRPC service implementation</p>
                    <a href="./grpc/index.html">View Documentation</a>
                </div>
                <div class="module-card">
                    <h3>Sandbox</h3>
                    <p>WASM sandbox management</p>
                    <a href="./sandbox/index.html">View Documentation</a>
                </div>
                <div class="module-card">
                    <h3>Security</h3>
                    <p>Security and guardrails</p>
                    <a href="./security/index.html">View Documentation</a>
                </div>
                <div class="module-card">
                    <h3>Observability</h3>
                    <p>Monitoring and telemetry</p>
                    <a href="./observability/index.html">View Documentation</a>
                </div>
            </div>
        </section>
    </main>
    
    <footer>
        <p>Generated by NeuroFlow Documentation Generator</p>
        <p>Version: 0.1.0</p>
    </footer>
</body>
</html>"#, self.config.language)
    }

    fn generate_module_docs(&self) -> Result<(), Box<dyn std::error::Error>> {
        let modules = [
            "config",
            "gateway", 
            "grpc",
            "sandbox",
            "security",
            "observability",
            "cli",
            "debug",
            "hot_reload",
            "routing",
            "utils"
        ];

        for module in &modules {
            let module_dir = format!("{}/{}", self.config.output_dir, module);
            std::fs::create_dir_all(&module_dir)?;

            let content = self.generate_module_page(module);
            let path = format!("{}/index.html", module_dir);
            std::fs::write(&path, content)?;
            debug!("Generated module doc: {}", path);
        }

        Ok(())
    }

    fn generate_module_page(&self, module: &str) -> String {
        let title = match module {
            "config" => "Configuration Management",
            "gateway" => "HTTP Gateway",
            "grpc" => "gRPC Services",
            "sandbox" => "WASM Sandbox",
            "security" => "Security & Guardrails",
            "observability" => "Observability",
            "cli" => "Command Line Interface",
            "debug" => "Debug Tools",
            "hot_reload" => "Hot Reload Engine",
            "routing" => "Semantic Routing",
            "utils" => "Utilities",
            _ => "Module Documentation",
        };

        format!(r#"<!DOCTYPE html>
<html lang="{}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{} - NeuroFlow API Docs</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 1rem;
            margin-bottom: 2rem;
        }}
        .api-function {{
            background: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 4px 4px 0;
        }}
        .function-signature {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            background: #edf2f7;
            padding: 0.5rem;
            border-radius: 4px;
            overflow-x: auto;
        }}
        pre {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
        }}
        code {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }}
    </style>
</head>
<body>
    <header>
        <h1>{}</h1>
        <p>Documentation for the {} module</p>
    </header>
    
    <main>
        <section>
            <h2>About</h2>
            <p>The <strong>{}</strong> module provides core functionality for NeuroFlow framework.</p>
            
            <h2>Key Components</h2>
            <div class="api-function">
                <div class="function-signature">pub struct {}Manager</div>
                <p>Main manager struct for handling {} operations.</p>
            </div>
            
            <div class="api-function">
                <div class="function-signature">impl {}Manager {{ pub fn new(...) -> Self }}</div>
                <p>Creates a new instance of the manager.</p>
            </div>
            
            <div class="api-function">
                <div class="function-signature">impl {}Manager {{ pub async fn process(...) -> Result<...> }}</div>
                <p>Processes {} operations asynchronously.</p>
            </div>
            
            <h2>Configuration</h2>
            <p>The {} module can be configured through the main NeuroFlow configuration file.</p>
            
            <pre><code>[{}]
enabled = true
timeout = 30
max_instances = 10
            </code></pre>
        </section>
    </main>
</body>
</html>"#, 
            self.config.language, 
            title, 
            title,
            module,
            capitalize_first(module),
            capitalize_first(module),
            capitalize_first(module),
            capitalize_first(module),
            module
        )
    }

    fn generate_config_docs(&self) -> Result<(), Box<dyn std::error::Error>> {
        let config_dir = format!("{}/configuration", self.config.output_dir);
        std::fs::create_dir_all(&config_dir)?;

        let content = r#"<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Configuration - NeuroFlow API Docs</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 1rem;
            margin-bottom: 2rem;
        }
        .config-section {
            background: #f7fafc;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        .config-key {
            background: #edf2f7;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            display: inline-block;
        }
        pre {
            background: #2d3748;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
        }
        code {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }
    </style>
</head>
<body>
    <header>
        <h1>Configuration Guide</h1>
        <p>Complete guide to configuring NeuroFlow framework</p>
    </header>
    
    <main>
        <section>
            <h2>Overview</h2>
            <p>NeuroFlow can be configured through TOML configuration files or environment variables.</p>
        </section>
        
        <section>
            <h2>Basic Configuration</h2>
            <div class="config-section">
                <h3>Server Configuration</h3>
                <p>Configure the HTTP and gRPC servers:</p>
                <pre><code>[server]
host = "127.0.0.1"
port = 8080
max_connections = 100
request_timeout = 30
idle_connection_timeout = 60
                </code></pre>
                
                <ul>
                    <li><span class="config-key">host</span>: Server bind address</li>
                    <li><span class="config-key">port</span>: HTTP port (default: 8080)</li>
                    <li><span class="config-key">max_connections</span>: Maximum concurrent connections</li>
                    <li><span class="config-key">request_timeout</span>: Request timeout in seconds</li>
                    <li><span class="config-key">idle_connection_timeout</span>: Idle connection timeout</li>
                </ul>
            </div>
            
            <div class="config-section">
                <h3>Sandbox Configuration</h3>
                <p>Configure WASM sandbox settings:</p>
                <pre><code>[sandbox]
max_instances = 10
memory_limit = 536870912  # 512MB
cpu_limit = 1.0
timeout = 30
allowed_hosts = ["localhost", "127.0.0.1"]
allowed_paths = ["/tmp"]
                </code></pre>
                
                <ul>
                    <li><span class="config-key">max_instances</span>: Maximum concurrent sandbox instances</li>
                    <li><span class="config-key">memory_limit</span>: Memory limit per sandbox in bytes</li>
                    <li><span class="config-key">cpu_limit</span>: CPU limit as fraction of core</li>
                    <li><span class="config-key">timeout</span>: Execution timeout in seconds</li>
                    <li><span class="config-key">allowed_hosts</span>: Allowed network hosts</li>
                    <li><span class="config-key">allowed_paths</span>: Allowed filesystem paths</li>
                </ul>
            </div>
            
            <div class="config-section">
                <h3>Security Configuration</h3>
                <p>Configure security settings:</p>
                <pre><code>[security]
  [security.rate_limit]
  requests_per_minute = 1000
  burst_size = 100

  [security.pii_detection]
  enabled = true
  confidence_threshold = 0.8
                </code></pre>
            </div>
        </section>
        
        <section>
            <h2>Environment Variables</h2>
            <p>You can override configuration values using environment variables:</p>
            <ul>
                <li><span class="config-key">NEUROFLOW_ENV</span>: Application environment</li>
                <li><span class="config-key">NEUROFLOW_SERVER_HOST</span>: Server host override</li>
                <li><span class="config-key">NEUROFLOW_SERVER_PORT</span>: Server port override</li>
                <li><span class="config-key">NEUROFLOW_JWT_SECRET</span>: JWT secret key</li>
            </ul>
        </section>
    </main>
</body>
</html>"#;

        let path = format!("{}/configuration/index.html", self.config.output_dir);
        std::fs::write(&path, content)?;
        debug!("Generated config docs: {}", path);

        Ok(())
    }

    fn generate_cli_docs(&self) -> Result<(), Box<dyn std::error::Error>> {
        let cli_dir = format!("{}/cli", self.config.output_dir);
        std::fs::create_dir_all(&cli_dir)?;

        let content = r#"<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLI Reference - NeuroFlow API Docs</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 1rem;
            margin-bottom: 2rem;
        }
        .cli-command {
            background: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 4px 4px 0;
        }
        .command-syntax {
            background: #2d3748;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }
        .option {
            margin: 0.5rem 0;
            padding: 0.5rem;
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <header>
        <h1>Command Line Interface</h1>
        <p>Complete reference for NeuroFlow CLI commands</p>
    </header>
    
    <main>
        <section>
            <h2>Overview</h2>
            <p>The NeuroFlow CLI provides commands for project management, configuration, and deployment.</p>
        </section>
        
        <section>
            <h2>Getting Started</h2>
            <p>Install the NeuroFlow CLI globally:</p>
            <div class="command-syntax">
                cargo install neuroflow-cli
            </div>
        </section>
        
        <section>
            <h2>Available Commands</h2>
            
            <div class="cli-command">
                <h3>neuroflow new</h3>
                <p>Create a new NeuroFlow project</p>
                
                <div class="command-syntax">
                    neuroflow new [OPTIONS] <PROJECT_NAME>
                </div>
                
                <div class="option">
                    <strong>Arguments:</strong><br>
                    PROJECT_NAME - Name of the new project
                </div>
                
                <div class="option">
                    <strong>Options:</strong><br>
                    -p, --path [PATH]          Project path (default: current directory)<br>
                    -t, --template [TEMPLATE]  Project template (default: basic)<br>
                    -e, --with-examples        Include example code
                </div>
                
                <div class="command-syntax">
                    # Create a new project
                    neuroflow new my-agent-project
                    
                    # Create with examples
                    neuroflow new my-project --with-examples
                </div>
            </div>
            
            <div class="cli-command">
                <h3>neuroflow run</h3>
                <p>Run a NeuroFlow project</p>
                
                <div class="command-syntax">
                    neuroflow run [OPTIONS]
                </div>
                
                <div class="option">
                    <strong>Options:</strong><br>
                    -c, --config [FILE]      Configuration file (default: ./config/neuroflow.toml)<br>
                    --env [ENV]              Environment (default: development)<br>
                    --debug                  Enable debug mode<br>
                    --http-port [PORT]       HTTP port override<br>
                    --grpc-port [PORT]       gRPC port override
                </div>
            </div>
            
            <div class="cli-command">
                <h3>neuroflow config</h3>
                <p>Manage configuration</p>
                
                <div class="command-syntax">
                    neuroflow config [SUBCOMMAND]
                </div>
                
                <div class="option">
                    <strong>Subcommands:</strong><br>
                    show                     Display current configuration<br>
                    validate [FILE]          Validate configuration file<br>
                    set <KEY> <VALUE>        Set configuration value<br>
                    template [OUTPUT]        Generate configuration template
                </div>
            </div>
            
            <div class="cli-command">
                <h3>neuroflow status</h3>
                <p>Show system status</p>
                
                <div class="command-syntax">
                    neuroflow status [OPTIONS]
                </div>
                
                <div class="option">
                    <strong>Options:</strong><br>
                    --verbose                Show detailed information<br>
                    --format [FORMAT]        Output format (json, yaml, table)
                </div>
            </div>
            
            <div class="cli-command">
                <h3>neuroflow diagnose</h3>
                <p>Run system diagnostics</p>
                
                <div class="command-syntax">
                    neuroflow diagnose [OPTIONS]
                </div>
                
                <div class="option">
                    <strong>Options:</strong><br>
                    --checks [CHECKS]        Checks to run (default: all)<br>
                    --fix                    Attempt to fix issues<br>
                    --output [FILE]          Output report to file
                </div>
            </div>
        </section>
    </main>
</body>
</html>"#;

        let path = format!("{}/cli/index.html", self.config.output_dir);
        std::fs::write(&path, content)?;
        debug!("Generated CLI docs: {}", path);

        Ok(())
    }
}

fn capitalize_first(s: &str) -> String {
    let mut chars = s.chars();
    match chars.next() {
        None => String::new(),
        Some(first) => first.to_uppercase().collect::<String>() + chars.as_str(),
    }
}

/// 使用指南生成器
pub struct GuideGenerator;

impl GuideGenerator {
    pub fn new() -> Self {
        Self
    }

    /// 生成快速入门指南
    pub fn generate_quick_start_guide(&self, output_dir: &str) -> Result<(), Box<dyn std::error::Error>> {
        std::fs::create_dir_all(output_dir)?;
        
        let content = r#"# NeuroFlow Quick Start Guide

Welcome to NeuroFlow! This guide will help you get started with the framework quickly.

## Installation

First, install the NeuroFlow CLI:

```bash
cargo install neuroflow-cli
```

## Creating Your First Project

Create a new project:

```bash
neuroflow new my-first-agent
cd my-first-agent
```

This creates a basic project structure with:

- `agents/` - Your agent implementations
- `config/` - Configuration files  
- `plugins/` - Custom plugins
- `examples/` - Example implementations

## Writing Your First Agent

Create a simple agent in `agents/hello.py`:

```python
from neuroflow import agent

@agent(name="hello")
def hello_agent(name: str) -> str:
    return f"Hello, {name}!"
```

## Running the Server

Start the NeuroFlow server:

```bash
neuroflow run
```

The server will start on `http://localhost:8080`.

## Testing Your Agent

Test your agent with curl:

```bash
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"agent": "hello", "payload": {"name": "World"}}'
```

You should get a response like:

```json
{
  "success": true,
  "data": {
    "message": "Hello from NeuroFlow!",
    "trace_id": "..."
  },
  "error": null,
  "trace_id": "..."
}
```

## Next Steps

- Explore the [Configuration Guide](./configuration.html) for advanced settings
- Learn about [Semantic Routing](./routing.html) for intelligent agent selection
- Check out the [Security Features](./security.html) for production deployments
- Review the [API Reference](./index.html) for complete documentation

That's it! You now have a working NeuroFlow setup. Continue to the [User Guide](./user-guide.html) for more advanced topics.
"#;

        let path = format!("{}/quick-start.html", output_dir);
        std::fs::write(&path, content)?;
        info!("Quick start guide generated: {}", path);

        Ok(())
    }

    /// 生成最佳实践指南
    pub fn generate_best_practices_guide(&self, output_dir: &str) -> Result<(), Box<dyn std::error::Error>> {
        std::fs::create_dir_all(output_dir)?;
        
        let content = r#"# NeuroFlow Best Practices

This guide covers best practices for developing with NeuroFlow.

## Agent Development

### Naming Conventions
- Use descriptive names for agents (e.g., `user_authenticator` instead of `ua`)
- Follow snake_case for agent names
- Include domain context in names (e.g., `payment_processor`)

### Error Handling
- Always handle exceptions gracefully
- Provide meaningful error messages
- Use structured error responses

```python
from neuroflow import agent

@agent(name="safe_divide")
def safe_divide(a: float, b: float) -> dict:
    try:
        result = a / b
        return {
            "success": True,
            "result": result
        }
    except ZeroDivisionError:
        return {
            "success": False,
            "error": "Cannot divide by zero"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }
```

### Resource Management
- Limit memory and CPU usage
- Set appropriate timeouts
- Clean up resources properly

## Security

### Input Validation
- Always validate inputs
- Sanitize user-provided data
- Use type hints for better validation

### Access Control
- Implement proper authentication
- Use rate limiting
- Validate permissions

## Performance

### Caching
- Cache expensive computations
- Use appropriate TTL values
- Invalidate caches properly

### Asynchronous Operations
- Use async/await for I/O operations
- Avoid blocking operations
- Implement proper concurrency controls

## Configuration

### Environment-Specific Settings
- Use different configs for dev/staging/prod
- Store secrets securely
- Validate config values

### Feature Flags
- Implement feature flags for gradual rollouts
- Use config to toggle features
- Monitor feature usage

## Monitoring and Observability

### Logging
- Log important events
- Use structured logging
- Include correlation IDs

### Metrics
- Track key performance indicators
- Monitor error rates
- Measure response times

## Deployment

### Containerization
- Use Docker for consistent deployments
- Optimize image sizes
- Implement health checks

### Scaling
- Design for horizontal scaling
- Use stateless agents where possible
- Implement proper load balancing

## Testing

### Unit Tests
- Test individual functions
- Mock external dependencies
- Cover edge cases

### Integration Tests
- Test agent interactions
- Validate end-to-end flows
- Test error scenarios

Following these best practices will help you build robust, scalable, and maintainable NeuroFlow applications.
"#;

        let path = format!("{}/best-practices.html", output_dir);
        std::fs::write(&path, content)?;
        info!("Best practices guide generated: {}", path);

        Ok(())
    }
}

/// 教程生成器
pub struct TutorialGenerator;

impl TutorialGenerator {
    pub fn new() -> Self {
        Self
    }

    /// 生成完整教程
    pub fn generate_comprehensive_tutorial(&self, output_dir: &str) -> Result<(), Box<dyn std::error::Error>> {
        std::fs::create_dir_all(output_dir)?;
        
        let content = r#"# NeuroFlow Comprehensive Tutorial

This tutorial will guide you through building a complete application with NeuroFlow.

## Project Setup

Let's create a customer service chatbot application:

```bash
neuroflow new customer-service-bot
cd customer-service-bot
```

## Building a Customer Service Agent

Create `agents/customer_service.py`:

```python
from neuroflow import agent
import json
from typing import Dict, Any

# Knowledge base for common questions
FAQ_KNOWLEDGE = {
    "hours": "We are open Monday-Friday 9AM-6PM EST",
    "returns": "We offer 30-day return policy for unused items",
    "shipping": "Free shipping on orders over $50",
    "contact": "Call us at 1-800-123-4567 or email support@example.com"
}

@agent(name="customer_service")
def customer_service_agent(query: str) -> Dict[str, Any]:
    """
    Handles customer service inquiries
    """
    query_lower = query.lower()
    
    # Check for keywords in the query
    if "hour" in query_lower or "open" in query_lower:
        answer = FAQ_KNOWLEDGE["hours"]
    elif "return" in query_lower or "refund" in query_lower:
        answer = FAQ_KNOWLEDGE["returns"]
    elif "ship" in query_lower or "delivery" in query_lower:
        answer = FAQ_KNOWLEDGE["shipping"]
    elif "contact" in query_lower or "help" in query_lower:
        answer = FAQ_KNOWLEDGE["contact"]
    else:
        answer = "I'm not sure about that. Let me connect you with a human representative."
    
    return {
        "query": query,
        "answer": answer,
        "confidence": 0.8 if answer != FAQ_KNOWLEDGE.get("contact", "") else 0.3
    }
```

## Adding a Sentiment Analysis Agent

Create `agents/sentiment.py`:

```python
from neuroflow import agent
from typing import Dict, Any

SENTIMENT_KEYWORDS = {
    "positive": ["good", "great", "excellent", "amazing", "love", "happy", "satisfied"],
    "negative": ["bad", "terrible", "awful", "hate", "angry", "disappointed", "frustrated"],
    "neutral": ["okay", "fine", "average", "normal"]
}

@agent(name="sentiment_analyzer")
def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyzes sentiment of given text
    """
    text_lower = text.lower()
    words = text_lower.split()
    
    pos_count = sum(1 for word in words if word in SENTIMENT_KEYWORDS["positive"])
    neg_count = sum(1 for word in words if word in SENTIMENT_KEYWORDS["negative"])
    neu_count = sum(1 for word in words if word in SENTIMENT_KEYWORDS["neutral"])
    
    total = pos_count + neg_count + neu_count
    
    if total == 0:
        sentiment = "neutral"
        score = 0.0
    else:
        if pos_count >= neg_count and pos_count >= neu_count:
            sentiment = "positive"
            score = pos_count as f64 / total as f64
        elif neg_count >= pos_count and neg_count >= neu_count:
            sentiment = "negative"
            score = neg_count as f64 / total as f64
        else:
            sentiment = "neutral"
            score = neu_count as f64 / total as f64
    
    return {
        "sentiment": sentiment,
        "score": score,
        "breakdown": {
            "positive": pos_count,
            "negative": neg_count,
            "neutral": neu_count,
            "total": total
        }
    }
```

## Creating a Tool Integration

Create `tools/email_tool.py`:

```python
from neuroflow import tool
from typing import Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@tool(name="send_email", description="Send an email to a customer")
def send_email_tool(to_address: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Sends an email using SMTP
    """
    try:
        # In a real application, you'd use proper email service
        # This is a simplified example
        
        message = MIMEMultipart()
        message["From"] = "noreply@customerservice.com"
        message["To"] = to_address
        message["Subject"] = subject
        
        message.attach(MIMEText(body, "plain"))
        
        # Simulate sending email
        print(f"Sending email to: {to_address}")
        print(f"Subject: {subject}")
        
        return {
            "success": True,
            "message": f"Email sent successfully to {to_address}",
            "recipient": to_address
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to send email: {str(e)}"
        }
```

## Semantic Routing Configuration

In `config/neuroflow.toml`, configure semantic routing:

```toml
[routing]
semantic_enabled = true
vector_dimension = 768
similarity_threshold = 0.6
max_candidates = 5

[[routing.agents]]
name = "customer_service"
description = "Handles general customer service inquiries"
intent_vectors = ["customer support", "help", "problem", "issue", "question"]

[[routing.agents]]
name = "sentiment_analyzer" 
description = "Analyzes sentiment in customer communications"
intent_vectors = ["analyze mood", "sentiment check", "feeling", "emotion", "attitude"]
```

## Testing Your Application

Create `tests/test_agents.py`:

```python
import pytest
from neuroflow.test import AgentTester

def test_customer_service_agent():
    tester = AgentTester("customer_service")
    
    # Test opening hours query
    result = tester.invoke({"query": "What are your business hours?"})
    assert result["success"] is True
    assert "Monday-Friday" in result["data"]["answer"]
    
    # Test return policy query
    result = tester.invoke({"query": "Can I return this item?"})
    assert result["success"] is True
    assert "30-day" in result["data"]["answer"]

def test_sentiment_analyzer():
    tester = AgentTester("sentiment_analyzer")
    
    # Test positive sentiment
    result = tester.invoke({"text": "I love this product, it's amazing!"})
    assert result["success"] is True
    assert result["data"]["sentiment"] == "positive"
    
    # Test negative sentiment
    result = tester.invoke({"text": "This is terrible, I hate it."})
    assert result["success"] is True
    assert result["data"]["sentiment"] == "negative"
```

## Running and Monitoring

Start your application:

```bash
neuroflow run --debug
```

Monitor the logs for requests and responses.

## Production Deployment

For production deployment, create `Dockerfile`:

```dockerfile
FROM rust:1.75 as builder

WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bullseye-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/target/release/kernel /usr/local/bin/neuroflow
EXPOSE 8080
CMD ["neuroflow"]
```

And `docker-compose.yml`:

```yaml
version: '3.8'
services:
  neuroflow:
    build: .
    ports:
      - "8080:8080"
    environment:
      - RUST_LOG=info
      - CONFIG_PATH=/app/config/prod.toml
    volumes:
      - ./config:/app/config
      - ./agents:/app/agents
    restart: unless-stopped
```

This tutorial covered:
- Creating agents for different purposes
- Integrating tools
- Configuring semantic routing
- Testing your application
- Preparing for production

Continue exploring the [Advanced Features](./advanced-features.html) for more capabilities.
"#;

        let path = format!("{}/tutorial.html", output_dir);
        std::fs::write(&path, content)?;
        info!("Tutorial generated: {}", path);

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_doc_generator_creation() {
        let temp_dir = TempDir::new().unwrap();
        let config = DocConfig {
            output_dir: temp_dir.path().to_str().unwrap().to_string(),
            ..Default::default()
        };
        
        let generator = ApiDocGenerator::new(config);
        assert!(generator.generate_api_docs().is_ok());
        
        let index_path = format!("{}/index.html", temp_dir.path().to_str().unwrap());
        assert!(std::path::Path::new(&index_path).exists());
    }

    #[test]
    fn test_guide_generator() {
        let temp_dir = TempDir::new().unwrap();
        let generator = GuideGenerator::new();
        
        assert!(generator.generate_quick_start_guide(temp_dir.path().to_str().unwrap()).is_ok());
        assert!(generator.generate_best_practices_guide(temp_dir.path().to_str().unwrap()).is_ok());
        
        let quick_start_path = format!("{}/quick-start.html", temp_dir.path().to_str().unwrap());
        assert!(std::path::Path::new(&quick_start_path).exists());
    }

    #[test]
    fn test_capitalize_first() {
        assert_eq!(capitalize_first("hello"), "Hello");
        assert_eq!(capitalize_first(""), "");
        assert_eq!(capitalize_first("a"), "A");
    }
}