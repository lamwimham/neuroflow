---
name: trading-signals
description: 基于技术指标生成交易信号，包括 RSI 信号、MACD 信号、布林带信号、随机指标信号和综合信号
version: 1.0.0
author: Trader Agent Team
category: data-analysis
created: 2026-02-19
tags:
  - cryptocurrency
  - trading
  - signals
  - technical-analysis
  - decision-making
trigger_words:
  - 交易信号
  - 买入信号
  - 卖出信号
  - 持仓建议
  - 信号分析
dependencies:
  - skill: technical-indicators
  - mcp: null
tools_required:
  - python3
  - technical-indicators skill
context: fork
allowed_tools:
  - read
  - write
  - bash
  - python_execution
assigned_agents:
  - trader
---

# TRADING SIGNALS SKILL

## Overview

本技能基于技术分析指标生成综合交易信号，通过多指标组合分析提供买入、卖出或持仓建议，并附带置信度和理由说明。

## Goals

### Primary Goal
基于多个技术指标的组合分析，生成可靠的交易信号和明确的操作建议。

### Secondary Goals
- 提供信号置信度评估
- 解释信号生成理由
- 支持多指标权重配置
- 避免单一指标的误导性信号

## Prerequisites

### Knowledge Requirements
- 理解技术分析指标的含义
- 了解信号组合策略
- 熟悉风险管理原则

### Tool Requirements
- technical-indicators skill
- Python 运行环境
- 实时价格数据

### Skill Dependencies
- technical-indicators: 提供基础指标计算

## Workflow

### Phase 1: 指标获取
1. **获取技术指标数据**
   - 调用 technical-indicators skill
   - 获取 RSI、MACD、布林带等指标
   - 验证数据完整性

2. **指标质量检查**
   - 确认数据时效性
   - 检查异常值
   - 评估数据可靠性

### Phase 2: 单指标信号生成
3. **RSI 信号**
   - RSI > 70: 超买 → 卖出信号
   - RSI < 30: 超卖 → 买入信号
   - 其他：中性

4. **MACD 信号**
   - MACD 上穿信号线：金叉 → 买入信号
   - MACD 下穿信号线：死叉 → 卖出信号
   - 其他：中性

5. **布林带信号**
   - 价格触及下轨：买入信号
   - 价格触及上轨：卖出信号
   - 其他：中性

6. **随机指标信号**
   - %K 和%D > 80: 超买 → 卖出信号
   - %K 和%D < 20: 超卖 → 买入信号
   - 其他：中性

### Phase 3: 信号组合
7. **权重计算**
   - 为每个指标分配权重
   - 计算买入/卖出得分
   - 评估信号一致性

8. **综合判断**
   - 比较买入和卖出得分
   - 确定最终信号方向
   - 计算置信度

### Phase 4: 输出建议
9. **生成交易建议**
   - 明确信号方向（买入/卖出/持仓）
   - 提供置信度百分比
   - 详细说明理由

10. **风险评估**
    - 标注风险等级
    - 提供止损建议
    - 建议仓位大小

## Implementation

### RSI Signal Generation
```python
def rsi_signal(rsi_value: float) -> Dict:
    """基于 RSI 生成交易信号"""
    if rsi_value >= 70:
        return {
            "signal": "sell",
            "strength": min((rsi_value - 70) / 30, 1.0),
            "reason": f"RSI 超买 ({rsi_value:.2f})"
        }
    elif rsi_value <= 30:
        return {
            "signal": "buy",
            "strength": min((30 - rsi_value) / 30, 1.0),
            "reason": f"RSI 超卖 ({rsi_value:.2f})"
        }
    else:
        return {
            "signal": "hold",
            "strength": 0,
            "reason": f"RSI 中性 ({rsi_value:.2f})"
        }
```

### MACD Signal Generation
```python
def macd_signal(macd_data: Dict) -> Dict:
    """基于 MACD 生成交易信号"""
    histogram = macd_data.get("histogram", 0)
    if histogram > 0:
        return {
            "signal": "buy",
            "strength": min(abs(histogram) / 10, 1.0),
            "reason": "MACD 金叉，上升动量"
        }
    elif histogram < 0:
        return {
            "signal": "sell",
            "strength": min(abs(histogram) / 10, 1.0),
            "reason": "MACD 死叉，下降动量"
        }
    return {"signal": "hold", "strength": 0, "reason": "MACD 中性"}
```

### Signal Combination
```python
def combine_signals(signals: List[Dict]) -> Dict:
    """组合多个指标信号"""
    buy_score = 0
    sell_score = 0
    reasons = []
    
    for signal in signals:
        strength = signal.get("strength", 0)
        sig = signal.get("signal", "hold")
        reason = signal.get("reason", "")
        
        if sig == "buy":
            buy_score += strength
            reasons.append(reason)
        elif sig == "sell":
            sell_score += strength
            reasons.append(reason)
    
    if buy_score > sell_score:
        return {
            "signal": "buy",
            "strength": min(buy_score / len(signals), 1.0),
            "reason": "; ".join(reasons)
        }
    elif sell_score > buy_score:
        return {
            "signal": "sell",
            "strength": min(sell_score / len(signals), 1.0),
            "reason": "; ".join(reasons)
        }
    else:
        return {"signal": "hold", "strength": 0, "reason": "信号平衡"}
```

## Output Format

```json
{
  "timestamp": "2026-02-19T10:00:00Z",
  "symbol": "BTC/USDT",
  "current_price": 42500.00,
  "signal": {
    "direction": "buy",
    "confidence": 75.5,
    "strength": "strong",
    "reason": "RSI 超卖 (28.50); MACD 金叉; 价格触及布林带下轨"
  },
  "individual_signals": {
    "rsi": {"signal": "buy", "strength": 0.55, "value": 28.50},
    "macd": {"signal": "buy", "strength": 0.60, "histogram": 25.25},
    "bollinger": {"signal": "buy", "strength": 0.80, "position": "below_lower"},
    "stochastic": {"signal": "hold", "strength": 0, "k": 45, "d": 42}
  },
  "recommendation": {
    "action": "买入",
    "suggestion": "强烈建议买入，多个指标显示买入信号",
    "stop_loss": 41000.00,
    "take_profit": [44000.00, 45500.00],
    "position_size": "建议仓位的 20-30%"
  },
  "risk_assessment": {
    "risk_level": "medium",
    "volatility": "normal",
    "market_condition": "trending"
  }
}
```

## Examples

### 示例 1: 强烈买入信号
```
用户：分析 BTC 当前是否适合买入

输出:
{
  "signal": "buy",
  "confidence": 85.0,
  "reason": "RSI 超卖 (25.30); MACD 金叉; 价格触及布林带下轨; 随机指标超卖",
  "recommendation": "强烈建议买入，多个指标共振显示买入机会"
}
```

### 示例 2: 观望信号
```
用户：现在应该买入还是卖出 ETH？

输出:
{
  "signal": "hold",
  "confidence": 0,
  "reason": "信号平衡 - RSI 中性，MACD 中性，价格在布林带中轨",
  "recommendation": "保持观望，等待更明确的信号"
}
```

### 示例 3: 卖出信号
```
用户：是否应该获利了结？

输出:
{
  "signal": "sell",
  "confidence": 72.5,
  "reason": "RSI 超买 (75.20); MACD 死叉; 价格触及布林带上轨",
  "recommendation": "建议卖出，考虑获利了结"
}
```

## Quality Metrics

- **信号准确率**: 目标 > 60%（回测）
- **响应时间**: < 200ms
- **置信度校准**: 高置信度信号应有更高准确率
- **风险控制**: 所有信号必须附带风险评估

## Troubleshooting

### 问题 1: 信号冲突
**症状**: 不同指标给出相反信号
**解决**: 
- 降低置信度评估
- 建议观望
- 增加权重给更可靠的指标

### 问题 2: 假信号
**症状**: 信号快速反转
**解决**:
- 增加确认条件
- 使用更长周期验证
- 结合成交量分析

### 问题 3: 滞后性
**症状**: 信号延迟
**解决**:
- 使用更敏感的参数
- 结合价格行为分析
- 考虑领先指标

## Related Skills

- technical-indicators: 提供基础指标计算
- risk-management: 风险管理和仓位控制
- backtesting: 策略回测和验证

## Version History

- **1.0.0** (2026-02-19): Initial release
  - RSI, MACD, Bollinger Bands, Stochastic signals
  - Signal combination algorithm
  - Confidence scoring
  - Risk assessment
