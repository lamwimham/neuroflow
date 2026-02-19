# trader Agent

**版本**: v0.4.1
**创建日期**: 2026-02-19
**描述**: 一个专注于加密货币市场的交易员，提供技术分析和交易信号

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 设置 LLM API Key (根据使用的厂商选择)

# 国产大模型（推荐）
export DEEPSEEK_API_KEY="your-api-key"    # 深度求索 (DeepSeek)

# 其他选项
export OPENAI_API_KEY="your-api-key"      # OpenAI
export ZHIPU_API_KEY="your-api-key"       # 智谱 AI (GLM)
```

### 3. 运行 Agent

```bash
# 直接运行
python trader.py

# 或使用 CLI
neuroflow agent run trader "你好"
```

---

## 📁 项目结构

```
.
├── trader.py               # Agent 主文件
├── config.yaml             # 配置文件
├── requirements.txt        # Python 依赖
├── AGENT.md                # 本文件
├── skills/                 # Skills 目录
│   ├── technical-indicators/
│   │   ├── SKILL.md        # 技术指标技能定义
│   │   ├── FRAMEWORK.md    # 实现框架
│   │   ├── EXAMPLES.md     # 使用示例
│   │   ├── scripts/        # 脚本目录
│   │   └── resources/      # 资源目录
│   └── trading-signals/
│       ├── SKILL.md        # 交易信号技能定义
│       ├── FRAMEWORK.md
│       ├── EXAMPLES.md
│       ├── scripts/
│       └── resources/
└── workspace/              # 工作目录
    └── .gitkeep
```

---

## 🎯 Skills

trader Agent 使用以下 Skills：

### 1. technical-indicators

**功能**: 提供加密货币交易技术分析指标计算

**指标列表**:
- SMA (简单移动平均线)
- EMA (指数移动平均线)
- RSI (相对强弱指数)
- MACD (移动平均收敛发散)
- Bollinger Bands (布林带)
- ATR (平均真实波幅)
- Stochastic (随机振荡器)

**使用示例**:
```python
# 计算 RSI
result = await skills_manager.execute(
    skill_name="technical-indicators",
    function="calculate_rsi",
    params={"prices": [42000, 42100, 41900, ...], "period": 14}
)
```

**详细文档**: [skills/technical-indicators/SKILL.md](skills/technical-indicators/SKILL.md)

### 2. trading-signals

**功能**: 基于技术指标生成综合交易信号

**信号类型**:
- RSI 信号（超买/超卖）
- MACD 信号（金叉/死叉）
- 布林带信号
- 随机指标信号
- 综合信号（多指标组合）

**输出格式**:
```json
{
  "signal": "buy",
  "confidence": 75.5,
  "reason": "RSI 超卖 (28.50); MACD 金叉; 价格触及布林带下轨",
  "recommendation": "强烈建议买入，多个指标显示买入信号"
}
```

**详细文档**: [skills/trading-signals/SKILL.md](skills/trading-signals/SKILL.md)

---

## 🛠️ 工具列表

Agent 提供以下工具：

| 工具名称 | 说明 | 所属 Skill |
|---------|------|-----------|
| `greet` | 问候用户 | - |
| `calculate_rsi` | 计算 RSI 指标 | technical-indicators |
| `calculate_macd` | 计算 MACD 指标 | technical-indicators |
| `generate_trading_signal` | 生成综合交易信号 | trading-signals |

---

## 📊 使用示例

### 示例 1: 询问技术指标

```
用户：帮我分析 BTC 的 RSI 指标，价格序列是 [42000, 42100, 41900, 42300, 42500]

Agent: 正在计算 RSI 指标...
       RSI (14): 65.5
       信号：中性
       解读：RSI 处于中性区域，无明显超买超卖信号
```

### 示例 2: 生成交易信号

```
用户：现在应该买入还是卖出 ETH？

Agent: 正在分析多个技术指标...
       
       综合信号：买入
       置信度：75.5%
       理由：RSI 超卖 (28.50); MACD 金叉; 价格触及布林带下轨
       
       建议：强烈建议买入，多个指标共振显示买入机会
       止损：41000
       目标价位：44000, 45500
```

### 示例 3: 全面技术分析

```
用户：对 BTC 进行全面技术分析

Agent: 📊 技术指标分析结果:
       
       趋势指标:
       - SMA(20): 42500 (价格在上行)
       - EMA(20): 42650 (上升趋势)
       
       动量指标:
       - RSI(14): 65.5 (中性偏多)
       - MACD: 金叉 (买入信号)
       
       波动性指标:
       - 布林带：价格在中轨附近
       - ATR(14): 850 (正常波动)
       
       综合建议：持仓观望，等待更明确信号
```

---

## ⚙️ 配置

编辑 `config.yaml` 配置 Agent：

```yaml
agent:
  name: trader
  description: 加密货币交易分析专家
  llm:
    provider: deepseek
    model: deepseek-chat

skills:
  enabled:
    - technical-indicators
    - trading-signals

mcp:
  servers:
    - name: filesystem
      enabled: true
```

---

## 🧪 测试

```bash
# 运行测试
python trader.py

# 验证 Skills
neuroflow skill validate technical-indicators
neuroflow skill validate trading-signals

# 列出所有 Skills
neuroflow skill list
```

---

## 📚 相关文档

- [Skills 概念文档](../../docs-site/docs/concepts/skills.md)
- [CLI 使用指南](../../docs-site/docs/guides/cli.md)
- [技术指标 SKILL.md](skills/technical-indicators/SKILL.md)
- [交易信号 SKILL.md](skills/trading-signals/SKILL.md)

---

**最后更新**: 2026-02-19  
**维护者**: Trader Agent Team
