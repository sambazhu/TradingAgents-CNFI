#!/usr/bin/env python3
"""
完整市场分析师链路测试 — 2026-04-09
股票: 格力电器(000651)  日期: 2026-04-08
已验证 Gildata 6/6 API 全部有数据
"""
import os

os.environ['GILDATA_API_TOKEN'] = 'YOUR_GILDATA_API_TOKEN'

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S')

TICKER = '000651'
NAME = '格力电器'
TRADE_DATE = '2026-04-08'
START_DATE = '2025-04-08'  # 回溯1年

print(f"{'='*70}")
print(f"  完整市场分析师链路测试")
print(f"  股票: {NAME}({TICKER})")
print(f"  日期: {TRADE_DATE}")
print(f"  Gildata: 6/6 API 已验证有数据")
print(f"{'='*70}\n")

# ============================================================
# Step 1: 完整数据链路
# ============================================================
print(f"📊 Step 1: 调用完整数据链路...\n")

from tradingagents.dataflows.data_source_manager import get_china_stock_data_unified

result = get_china_stock_data_unified(TICKER, START_DATE, TRADE_DATE)

print(f"\n{'='*70}")
print(f"📊 数据链路返回结果 (共 {len(result)} 字符):")
print(f"{'='*70}")
print(result)
print(f"{'='*70}")

# ============================================================
# Step 2: 检查集成情况
# ============================================================
print(f"\n📊 Step 2: 检查数据集成情况...\n")

checks = {
    '基础行情': ['收盘价', '涨跌', '成交量', '换手率'],
    '技术指标': ['MA5', 'MA10', 'MA20', 'MA60', 'MACD', 'RSI', '布林带'],
    'Gildata估值': ['PE(TTM)', '股息率', '总市值'],
    'Gildata资金': ['资金流向分析', '大单', '净买入'],
    'Gildata风险': ['风险分析指标', 'Beta', '夏普比率'],
    'Gildata因子': ['风险因子暴露', '市值因子', '波动因子'],
}

for section, keywords in checks.items():
    found = [kw for kw in keywords if kw in result]
    missing = [kw for kw in keywords if kw not in result]
    if found and not missing:
        print(f"  ✅ {section}: 全部找到")
    elif found:
        print(f"  ⚠️ {section}: 找到 {found}, 缺少 {missing}")
    else:
        print(f"  ❌ {section}: 缺失")

# ============================================================
# Step 3: Kimi K2.5 生成报告
# ============================================================
print(f"\n🤖 Step 3: 调用 Kimi K2.5 生成技术分析报告...\n")

from tradingagents.graph.trading_graph import create_llm_by_provider

llm = create_llm_by_provider(
    provider='dashscope',
    model='kimi-k2.5',
    backend_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    temperature=0.3,
    max_tokens=4096,
    timeout=120,
    api_key='YOUR_DASHSCOPE_API_KEY'
)

prompt = f"""你是一位专业的A股技术分析师。请基于以下市场数据，为 {NAME}({TICKER}) 生成一份完整的技术分析报告。

**分析对象**: {NAME}({TICKER})
**分析日期**: {TRADE_DATE}
**所属市场**: A股（深圳交易所）

**以下是系统通过完整数据链路获取的市场数据**:

{result}

---

请按照以下格式生成报告（使用中文）:

# {NAME}({TICKER}) 技术分析报告
**分析日期**: {TRADE_DATE}

## 一、行情概览
## 二、技术指标分析（均线/MACD/RSI/BOLL）
## 三、资金面分析
## 四、估值分析
## 五、风险分析
## 六、综合评估与操作建议
- 投资评级、目标价位、止损位、支撑位、压力位

---
*报告由 Kimi K2.5 模型基于恒生聚源实时数据生成，仅供参考*
"""

response = llm.invoke(prompt)
report = response.content

print(f"{'='*70}")
print(report)
print(f"{'='*70}")

# 保存
output_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, f'full_pipeline_{TICKER}_{TRADE_DATE}_report.md')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(report)
print(f"\n📄 报告已保存: {output_file}")
