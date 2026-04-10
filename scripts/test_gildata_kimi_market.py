#!/usr/bin/env python3
"""
测试脚本：用 Kimi K2.5 (通过 DashScope) + Gildata 数据源跑市场分析师
随机选择一只 A 股，生成技术分析报告
"""
import os
import random

# 设置环境变量
os.environ['GILDATA_API_TOKEN'] = 'YOUR_GILDATA_API_TOKEN'

# A 股候选池
STOCK_POOL = [
    ('601318', '中国平安'), ('000858', '五粮液'), ('600036', '招商银行'),
    ('000333', '美的集团'), ('600519', '贵州茅台'), ('002415', '海康威视'),
    ('601012', '隆基绿能'), ('000651', '格力电器'), ('600900', '长江电力'),
    ('002230', '科大讯飞'), ('601899', '紫金矿业'), ('000001', '平安银行'),
]

# 随机选股（排除上次用过的 601318 和 000001）
remaining = [(c, n) for c, n in STOCK_POOL if c not in ('601318', '000001')]
ticker, name = random.choice(remaining)
trade_date = '2025-04-08'

print(f"{'='*60}")
print(f"  股票: {name} ({ticker})")
print(f"  分析日期: {trade_date}")
print(f"  模型: kimi-k2.5 (via DashScope)")
print(f"  数据源: Gildata 恒生聚源")
print(f"{'='*60}\n")

# Step 1: 获取 Gildata 全部数据
print("📊 Step 1: 获取 Gildata 数据...\n")

from tradingagents.dataflows.gildata_client import get_gildata_client
from tradingagents.dataflows.gildata_enrichment import (
    format_valuation_section,
    format_capital_flow_section,
    format_risk_section,
    format_risk_factor_section,
    parse_markdown_table,
)

client = get_gildata_client()

# 1.1 日行情
print("  [1/5] 日行情...")
daily = client.get_daily_quote(ticker, trade_date)
daily_info = ""
if daily:
    rows = parse_markdown_table(daily)
    if len(rows) >= 2:
        headers, data = rows[0], rows[1]
        def gv(kws):
            from tradingagents.dataflows.gildata_enrichment import find_column, safe_float
            idx = find_column(headers, kws)
            return data[idx] if idx is not None and idx < len(data) else 'N/A'
        daily_info = f"""**日行情数据** ({trade_date}):
- 开盘: {gv(['今开盘'])}元  收盘: {gv(['收盘价'])}元  最高: {gv(['最高价'])}元  最低: {gv(['最低价'])}元
- 涨跌: {gv(['涨跌'])}元 ({gv(['涨跌幅'])}%)  振幅: {gv(['振幅'])}%
- 成交额: {gv(['成交额'])}万元  成交量: {gv(['成交量'])}万股  换手率: {gv(['换手率'])}%  量比: {gv(['量比'])}
"""
        print(f"    ✅ 收盘{gv(['收盘价'])}元, 涨跌{gv(['涨跌'])}元")
else:
    print("    ❌ 无数据")

# 1.2 技术指标
print("  [2/5] 技术指标...")
tech = client.get_tech_indicators(ticker, trade_date)
tech_info = ""
if tech:
    rows = parse_markdown_table(tech)
    if len(rows) >= 2:
        headers, data = rows[0], rows[1]
        def gv(kws):
            from tradingagents.dataflows.gildata_enrichment import find_column
            idx = find_column(headers, kws)
            return data[idx] if idx is not None and idx < len(data) else 'N/A'
        tech_info = f"""**技术指标** (最新值):
- MA5: {gv(['MA5'])}  MA10: {gv(['MA10'])}  MA20: {gv(['MA20'])}  MA60: {gv(['MA60'])}
- MACD: DIF={gv(['DIFF'])}, DEA={gv(['DEA'])}, MACD柱={gv(['MACD'])}
- KDJ: K={gv(['K值'])}, D={gv(['D值'])}, J={gv(['J值'])}
- BOLL: 上轨={gv(['UPPER'])}, 中轨={gv(['MID'])}, 下轨={gv(['LOWER'])}
- RSI: {gv(['RSI'])}
"""
        print(f"    ✅ MA5={gv(['MA5'])}, MACD DIF={gv(['DIFF'])}, RSI={gv(['RSI'])}")
else:
    print("    ❌ 无数据")

# 1.3 估值
print("  [3/5] 估值数据...")
val = client.get_valuation(ticker, trade_date)
val_info = ""
if val:
    val_info = format_valuation_section(val)
    print(f"    ✅ 已获取")
else:
    print("    ❌ 无数据")

# 1.4 资金流向
print("  [4/5] 资金流向...")
cf = client.get_capital_flow(ticker, '2025-03-08', trade_date)
cf_info = ""
if cf:
    cf_info = format_capital_flow_section(cf)
    print(f"    ✅ 已获取")
else:
    print("    ❌ 无数据")

# 1.5 风险分析 + 因子
print("  [5/5] 风险分析...")
risk = client.get_risk_analysis(ticker, trade_date)
risk_info = ""
if risk:
    risk_info = format_risk_section(risk)
    print(f"    ✅ 已获取风险指标")

factors = client.get_risk_factors(ticker, trade_date)
factors_info = ""
if factors:
    factors_info = format_risk_factor_section(factors)
    print(f"    ✅ 已获取风险因子")

# 组合所有数据
full_data = f"""# {name}({ticker}) 市场数据 ({trade_date})
数据源: 恒生聚源 Gildata

{daily_info}

{tech_info}

{val_info}

{cf_info}

{risk_info}

{factors_info}
"""

print(f"\n📊 数据获取完成，共 {len(full_data)} 字符\n")

# Step 2: 用 Kimi K2.5 生成技术分析报告
print("🤖 Step 2: 调用 Kimi K2.5 生成技术分析报告...\n")

from tradingagents.graph.trading_graph import create_llm_by_provider

# DashScope API Key
dashscope_key = 'YOUR_DASHSCOPE_API_KEY'
print(f"  API Key: {dashscope_key[:10]}...{dashscope_key[-5:]}")

llm = create_llm_by_provider(
    provider='dashscope',
    model='kimi-k2.5',
    backend_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    temperature=0.3,
    max_tokens=4096,
    timeout=120,
    api_key=dashscope_key
)

prompt = f"""你是一位专业的A股技术分析师。请基于以下市场数据，为 {name}({ticker}) 生成一份完整的技术分析报告。

**分析对象**: {name}({ticker})
**分析日期**: {trade_date}
**所属市场**: A股（上海/深圳交易所）

**以下是实时获取的市场数据**:

{full_data}

---

请按照以下格式生成报告（使用中文）:

# {name}({ticker}) 技术分析报告
**分析日期**: {trade_date}

## 一、行情概览
[基于日行情数据，描述当日表现]

## 二、技术指标分析
### 1. 均线系统分析
[分析MA5/10/20/60的排列形态，价格与均线位置关系，判断趋势]
### 2. MACD分析
[分析DIF/DEA/MACD柱，判断金叉/死叉、多空力量]
### 3. KDJ分析
[分析K/D/J三线位置，判断超买/超卖]
### 4. RSI分析
[分析RSI值，判断强弱和超买/超卖]
### 5. 布林带分析
[分析价格在布林带中的位置，判断波动性]

## 三、资金面分析
[基于资金流向数据，分析主力资金动向]

## 四、估值分析
[基于PE/PB/PS/股息率等数据，评估估值水平]

## 五、风险分析
[基于Beta/波动率/夏普比率/风险因子，评估风险特征]

## 六、综合评估与操作建议
### 1. 综合评估
[综合以上所有分析]
### 2. 操作建议
- **投资评级**: [买入/持有/卖出]
- **目标价位**: [具体价格区间]
- **止损位**: [具体价格]
- **关键支撑位**: [具体价格]
- **关键压力位**: [具体价格]

---
*报告由 Kimi K2.5 模型基于恒生聚源实时数据生成，仅供参考，不构成投资建议*
"""

response = llm.invoke(prompt)
report = response.content

print("=" * 60)
print(report)
print("=" * 60)

# 保存报告
output_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, f'gildata_{ticker}_{trade_date}_report.md')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(report)
print(f"\n📄 报告已保存: {output_file}")
