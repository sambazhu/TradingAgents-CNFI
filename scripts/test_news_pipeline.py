#!/usr/bin/env python3
"""
完整新闻分析师链路测试
验证 unified_news_tool → Gildata 富集 → 完整输出
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ['GILDATA_API_TOKEN'] = 'YOUR_GILDATA_API_TOKEN'

from datetime import datetime

STOCK_CODE = "000651"
STOCK_NAME = "格力电器"

print("=" * 70)
print(f"  完整新闻分析师链路测试")
print(f"  股票: {STOCK_NAME}({STOCK_CODE})")
print("=" * 70)

# Step 1: 初始化工具
print(f"\n📊 Step 1: 初始化 UnifiedNewsAnalyzer...\n")

from tradingagents.tools.unified_news_tool import UnifiedNewsAnalyzer
from tradingagents.agents.utils.agent_utils import Toolkit

toolkit = Toolkit()
analyzer = UnifiedNewsAnalyzer(toolkit)

# Step 2: 获取 A 股新闻（含 Gildata 富集）
print(f"\n📊 Step 2: 获取 {STOCK_CODE} 的A股新闻（含 Gildata 富集）...\n")

result = analyzer.get_stock_news_unified(STOCK_CODE, max_news=10, model_info="kimi-k2.5")

# Step 3: 分析结果
print(f"\n{'=' * 70}")
print(f"  链路返回结果: {len(result)} 字符")
print(f"{'=' * 70}")

# 检查 Gildata 数据是否集成
checks = {
    "恒生聚源": "恒生聚源" in result,
    "个股舆情": "个股舆情" in result or "舆情" in result,
    "互动平台": "互动平台" in result or "问答" in result,
    "研究观点": "研究观点" in result or "研报" in result,
}

print(f"\n📋 Gildata 集成检查:")
for name, found in checks.items():
    print(f"  {'✅' if found else '⚠️'} {name}")

# 打印结果
print(f"\n{'=' * 70}")
print(f"  完整输出")
print(f"{'=' * 70}")

# 只打印 Gildata 补充部分
if "恒生聚源" in result:
    parts = result.split("恒生聚源补充数据")
    if len(parts) > 1:
        print("\n## 恒生聚源补充数据" + parts[1][:2000])
        if len(parts[1]) > 2000:
            print(f"\n... (截断，完整 {len(parts[1])} 字符)")
    else:
        print(result[:2000])
else:
    print(result[:2000])

# 保存结果
os.makedirs("results", exist_ok=True)
filename = f"results/news_{STOCK_CODE}_{datetime.now().strftime('%Y%m%d')}_result.txt"
with open(filename, 'w', encoding='utf-8') as f:
    f.write(result)
print(f"\n📄 结果已保存: {filename}")

print(f"\n{'=' * 70}")
print(f"  ✅ 完整链路测试完成！")
print(f"{'=' * 70}")
