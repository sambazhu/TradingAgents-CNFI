#!/usr/bin/env python3
"""
测试脚本：跑完整的市场分析师数据链路，验证 Gildata 集成效果
使用五粮液(000858)，日期 2025-04-02（已验证所有6个 Gildata API 均有数据）

链路：data_source_manager.get_china_stock_data_unified()
  → DataSourceManager.get_stock_data()
    → _get_xxx_data() (获取原始 OHLCV)
    → _format_stock_data_response()
      → 自算技术指标（MA/RSI/MACD/BOLL）
      → ★ Gildata 预计算技术指标覆盖
      → 格式化报告
      → ★ Gildata 富集数据附加（估值/资金/风险）
"""
import os
import sys
import logging

# 设置环境变量
os.environ['GILDATA_API_TOKEN'] = 'YOUR_GILDATA_API_TOKEN'

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)

# 参数
TICKER = '000858'
NAME = '五粮液'
TRADE_DATE = '2025-04-02'  # 已验证：所有6个Gildata接口均有数据

print(f"{'='*70}")
print(f"  完整市场分析师链路测试")
print(f"  股票: {NAME}({TICKER})")
print(f"  日期: {TRADE_DATE}")
print(f"  Gildata: 全部6个API已验证有数据")
print(f"{'='*70}\n")

# ============================================================
# Step 1: 直接调用 data_source_manager 的链路
# ============================================================
print("📊 Step 1: 调用完整数据链路 (data_source_manager)...\n")

from tradingagents.dataflows.data_source_manager import get_china_stock_data_unified

# 回溯365天，确保有足够数据计算MA60等长周期指标
start_date = '2024-04-01'

print(f"  调用: get_china_stock_data_unified('{TICKER}', '{start_date}', '{TRADE_DATE}')")
print(f"  (内部会经过: 数据源获取 → 自算技术指标 → Gildata覆盖 → Gildata富集)\n")

result = get_china_stock_data_unified(TICKER, start_date, TRADE_DATE)

print(f"\n{'='*70}")
print(f"📊 链路返回结果 (共 {len(result)} 字符):")
print(f"{'='*70}")
print(result)
print(f"{'='*70}")

# ============================================================
# Step 2: 检查 Gildata 数据是否出现在报告中
# ============================================================
print(f"\n📊 Step 2: 检查 Gildata 数据集成情况...\n")

checks = {
    '基础行情数据': ['收盘价', '开盘价', '成交量'],
    '自算技术指标': ['MA5', 'MA10', 'MA20', 'MA60', 'MACD', 'RSI', '布林带'],
    'Gildata估值数据': ['PE(TTM)', '市净率PB', 'PS(TTM)', '股息率', '总市值'],
    'Gildata资金流向': ['资金流向分析', '大单', '净买入', '资金比'],
    'Gildata风险分析': ['风险分析指标', 'Beta', '波动率', '夏普比率'],
    'Gildata风险因子': ['风险因子暴露', '市值因子', '波动因子'],
}

for section, keywords in checks.items():
    found = [kw for kw in keywords if kw in result]
    missing = [kw for kw in keywords if kw not in result]
    if found and not missing:
        print(f"  ✅ {section}: 全部找到 {found}")
    elif found:
        print(f"  ⚠️ {section}: 部分找到 {found}, 缺少 {missing}")
    else:
        print(f"  ❌ {section}: 全部缺失")

# ============================================================
# Step 3: 用 Kimi K2.5 生成技术分析报告
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
[基于日行情数据，描述当日表现]

## 二、技术指标分析
### 1. 均线系统分析
[分析MA5/10/20/60的排列形态，价格与均线位置关系]
### 2. MACD分析
[分析DIF/DEA/MACD柱]
### 3. RSI分析
[分析RSI值]
### 4. 布林带分析
[分析价格在布林带中的位置]

## 三、资金面分析
[基于资金流向数据]

## 四、估值分析
[基于PE/PB/PS/股息率等]

## 五、风险分析
[基于Beta/波动率/夏普比率/风险因子]

## 六、综合评估与操作建议
### 1. 综合评估
### 2. 操作建议
- 投资评级、目标价位、止损位、支撑位、压力位

---
*报告由 Kimi K2.5 模型基于恒生聚源实时数据生成，仅供参考*
"""

response = llm.invoke(prompt)
report = response.content

print(f"{'='*70}")
print(report)
print(f"{'='*70}")

# 保存报告
output_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, f'full_pipeline_{TICKER}_{TRADE_DATE}_report.md')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(report)
print(f"\n📄 报告已保存: {output_file}")
