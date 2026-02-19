---
name: technical-indicators
description: 提供加密货币交易技术分析指标计算，包括 SMA、EMA、RSI、MACD、布林带、ATR、随机振荡器等
version: 1.0.0
author: Trader Agent Team
category: data-analysis
created: 2026-02-19
tags:
  - cryptocurrency
  - trading
  - technical-analysis
  - indicators
  - data-analysis
trigger_words:
  - 计算指标
  - 技术分析
  - RSI
  - MACD
  - 布林带
  - 移动平均
dependencies:
  - skill: null
  - mcp: null
tools_required:
  - python3
  - numpy (optional for advanced calculations)
context: fork
allowed_tools:
  - read
  - write
  - bash
  - python_execution
assigned_agents:
  - trader
---

# TECHNICAL INDICATORS SKILL

## Overview

本技能提供全面的加密货币交易技术分析指标计算功能，帮助交易员分析市场趋势、动量和波动性。支持主流技术指标的实时计算和解读。

## Goals

### Primary Goal
为加密货币交易提供准确、及时的技术指标计算和解释，辅助交易决策。

### Secondary Goals
- 支持多种经典技术指标（SMA、EMA、RSI、MACD、布林带等）
- 提供指标解读和交易信号建议
- 支持自定义参数配置
- 确保计算准确性和性能

## Prerequisites

### Knowledge Requirements
- 理解技术分析基本概念
- 了解各指标的计算方法和应用场景
- 熟悉加密货币市场特性

### Tool Requirements
- Python 运行环境
- numpy 库（用于高效数值计算）
- 历史价格数据访问

### Skill Dependencies
- 无

## Workflow

### Phase 1: 数据准备
1. **获取价格数据**
   - 收集 OHLCV 数据（开盘价、最高价、最低价、收盘价、成交量）
   - 验证数据完整性和准确性
   - 确定时间周期（1h、4h、1d 等）

2. **数据预处理**
   - 处理缺失值
   - 排序时间序列
   - 确保数据格式一致

### Phase 2: 指标计算
3. **趋势指标**
   - SMA（简单移动平均线）
   - EMA（指数移动平均线）
   - 计算不同周期的移动平均

4. **动量指标**
   - RSI（相对强弱指数）
   - MACD（移动平均收敛发散）
   - 随机振荡器

5. **波动性指标**
   - 布林带（Bollinger Bands）
   - ATR（平均真实波幅）

### Phase 3: 结果解读
6. **指标分析**
   - 判断超买超卖状态
   - 识别趋势方向
   - 评估波动性水平

7. **生成报告**
   - 汇总所有指标值
   - 提供交易信号建议
   - 标注关键支撑阻力位

## Implementation

### SMA (Simple Moving Average)
```python
def calculate_sma(prices: List[float], period: int = 20) -> float:
    """计算简单移动平均线"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period
```

**解读**: 
- 价格 > SMA: 上升趋势
- 价格 < SMA: 下降趋势
- 常用周期：20（月线）、50（季线）、200（年线）

### EMA (Exponential Moving Average)
```python
def calculate_ema(prices: List[float], period: int = 20) -> float:
    """计算指数移动平均线"""
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema
```

**解读**: EMA 对近期价格更敏感，适合短期交易

### RSI (Relative Strength Index)
```python
def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """计算相对强弱指数"""
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
```

**解读**:
- RSI > 70: 超买（考虑卖出）
- RSI < 30: 超卖（考虑买入）
- RSI 50: 中性

### MACD (Moving Average Convergence Divergence)
```python
def calculate_macd(prices: List[float]) -> Dict:
    """计算 MACD 指标"""
    fast_ema = ema(prices, 12)
    slow_ema = ema(prices, 26)
    macd_line = fast_ema - slow_ema
    signal_line = ema([macd_line], 9)
    histogram = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}
```

**解读**:
- MACD 上穿信号线：金叉（买入信号）
- MACD 下穿信号线：死叉（卖出信号）
- Histogram > 0: 上升动量

### Bollinger Bands
```python
def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict:
    """计算布林带"""
    sma = calculate_sma(prices, period)
    variance = sum((p - sma) ** 2 for p in prices[-period:]) / period
    std = sqrt(variance)
    return {
        "upper": sma + (std_dev * std),
        "middle": sma,
        "lower": sma - (std_dev * std)
    }
```

**解读**:
- 价格触及下轨：可能反弹（买入机会）
- 价格触及上轨：可能回落（卖出机会）
- 带宽收窄：即将突破

## Output Format

```json
{
  "timestamp": "2026-02-19T10:00:00Z",
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "indicators": {
    "sma_20": 42500.00,
    "ema_20": 42650.00,
    "rsi_14": 65.5,
    "macd": {
      "macd_line": 125.50,
      "signal_line": 100.25,
      "histogram": 25.25
    },
    "bollinger_bands": {
      "upper": 43500.00,
      "middle": 42500.00,
      "lower": 41500.00
    },
    "atr_14": 850.00
  },
  "signals": {
    "trend": "bullish",
    "momentum": "neutral",
    "volatility": "normal"
  }
}
```

## Examples

### 示例 1: 计算 RSI
```
用户：计算 BTC 的 RSI 指标，价格序列：[42000, 42100, 41900, 42300, 42500, ...]

输出:
{
  "indicator": "RSI",
  "value": 65.5,
  "signal": "neutral",
  "interpretation": "RSI 处于中性区域，无明显超买超卖信号"
}
```

### 示例 2: 计算 MACD
```
用户：分析 ETH 的 MACD 指标

输出:
{
  "indicator": "MACD",
  "macd_line": 15.25,
  "signal_line": 12.50,
  "histogram": 2.75,
  "signal": "buy",
  "interpretation": "MACD 位于信号线上方，显示上升动量"
}
```

### 示例 3: 综合指标分析
```
用户：对 BTC 进行全面技术分析

输出:
{
  "trend_indicators": {"sma": "bullish", "ema": "bullish"},
  "momentum_indicators": {"rsi": "neutral", "macd": "bullish"},
  "volatility_indicators": {"bb": "normal", "atr": "low"},
  "overall_signal": "buy",
  "confidence": 0.75
}
```

## Quality Metrics

- **计算准确性**: 100% 符合标准公式
- **响应时间**: < 100ms
- **数据完整性**: 至少需要 26 个数据点（MACD 要求）
- **错误处理**: 完善的异常处理和错误提示

## Troubleshooting

### 问题 1: 数据不足
**症状**: 返回 null 或错误
**解决**: 确保提供至少 26 个价格数据点

### 问题 2: 异常值影响
**症状**: 指标值异常
**解决**: 检查数据质量，排除异常价格

### 问题 3: 参数选择不当
**症状**: 信号不准确
**解决**: 根据交易品种和时间周期调整参数

## Related Skills

- trading-signals: 基于指标生成交易信号
- risk-management: 风险管理和仓位控制
- market-data: 市场数据获取

## Version History

- **1.0.0** (2026-02-19): Initial release
  - SMA, EMA, RSI, MACD, Bollinger Bands, ATR, Stochastic
  - Basic signal generation
  - Standard output format
