#!/usr/bin/env python3
"""
端到端测试：新闻分析师完整报告生成
使用 qwen3-235b-a22b 模型，对宁德时代(300750)生成完整新闻分析报告
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ['GILDATA_API_TOKEN'] = 'YOUR_GILDATA_API_TOKEN'

from datetime import datetime

STOCK_CODE = "300750"
STOCK_NAME = "宁德时代"

print("=" * 70)
print(f"  新闻分析师完整报告生成测试")
print(f"  股票: {STOCK_NAME}({STOCK_CODE})")
print(f"  模型: qwen3-235b-a22b")
print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Step 1: 创建 LLM
print(f"\n📊 Step 1: 创建 LLM (qwen3-235b-a22b)...\n")

from tradingagents.llm_adapters.dashscope_openai_adapter import create_dashscope_openai_llm

llm = create_dashscope_openai_llm(
    model="qwen3-235b-a22b",
    temperature=0.1,
    max_tokens=4000,
)

# Step 2: 创建 Toolkit 和 news_analyst
print(f"\n📊 Step 2: 创建新闻分析师...\n")

from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.agents.analysts.news_analyst import create_news_analyst

toolkit = Toolkit()
news_analyst_node = create_news_analyst(llm, toolkit)

# Step 3: 构造 state 并调用
print(f"\n📊 Step 3: 生成完整报告...\n")

state = {
    "trade_date": datetime.now().strftime("%Y-%m-%d"),
    "company_of_interest": STOCK_CODE,
    "messages": [],
    "session_id": "test-e2e-news",
}

start_time = datetime.now()
result = news_analyst_node(state)
elapsed = (datetime.now() - start_time).total_seconds()

# Step 4: 输出报告
report = result.get("news_report", "")

print(f"\n{'=' * 70}")
print(f"  📰 新闻分析报告 — {STOCK_NAME}({STOCK_CODE})")
print(f"  生成耗时: {elapsed:.1f}秒")
print(f"  报告长度: {len(report)} 字符")
print(f"{'=' * 70}")

print(f"\n{report}")

# 保存
os.makedirs("results", exist_ok=True)
filename = f"results/news_report_{STOCK_CODE}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
with open(filename, 'w', encoding='utf-8') as f:
    f.write(f"# {STOCK_NAME}({STOCK_CODE}) 新闻分析报告\n\n")
    f.write(f"- 模型: qwen3-235b-a22b\n")
    f.write(f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"- 耗时: {elapsed:.1f}秒\n\n")
    f.write("---\n\n")
    f.write(report)
print(f"\n📄 报告已保存: {filename}")

print(f"\n{'=' * 70}")
print(f"  ✅ 测试完成！")
print(f"{'=' * 70}")
