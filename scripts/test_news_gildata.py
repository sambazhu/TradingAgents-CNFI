#!/usr/bin/env python3
"""
新闻分析师 Gildata 集成验证脚本
测试完整的新闻数据链路 + Gildata 富集
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 设置 Gildata API Token
os.environ['GILDATA_API_TOKEN'] = 'YOUR_GILDATA_API_TOKEN'

from datetime import datetime

STOCK_CODE = "000651"
STOCK_NAME = "格力电器"
TRADE_DATE = "2026-04-08"

print("=" * 70)
print(f"  新闻分析师 Gildata 集成验证")
print(f"  股票: {STOCK_NAME}({STOCK_CODE})  日期: {TRADE_DATE}")
print("=" * 70)

# ===== Step 1: 测试各 Gildata API =====
print(f"\n📊 Step 1: 测试 Gildata 新闻相关 API...\n")

from tradingagents.dataflows.gildata_client import get_gildata_client
from tradingagents.dataflows.gildata_news import (
    format_stock_news_section,
    format_interactive_qa_section,
    format_announcement_section,
    format_research_viewpoints_section,
)

client = get_gildata_client()

api_results = {}

# 1. StockNewslist
print("  [1/4] StockNewslist (个股舆情)...")
try:
    news_md = client.get_stock_news(STOCK_CODE, TRADE_DATE)
    if news_md:
        section = format_stock_news_section(news_md)
        api_results["个股舆情"] = len(section)
        print(f"  ✅ 个股舆情: {len(news_md)} 字符 → 格式化 {len(section)} 字符")
    else:
        api_results["个股舆情"] = 0
        print(f"  ❌ 个股舆情: 返回空")
except Exception as e:
    api_results["个股舆情"] = 0
    print(f"  ❌ 个股舆情: {e}")

# 2. InteractivePlatformReport
print("  [2/4] InteractivePlatformReport (互动问答)...")
try:
    qa_md = client.get_interactive_platform(STOCK_CODE, TRADE_DATE)
    if qa_md:
        section = format_interactive_qa_section(qa_md)
        api_results["互动问答"] = len(section)
        print(f"  ✅ 互动问答: {len(qa_md)} 字符 → 格式化 {len(section)} 字符")
    else:
        api_results["互动问答"] = 0
        print(f"  ❌ 互动问答: 返回空")
except Exception as e:
    api_results["互动问答"] = 0
    print(f"  ❌ 互动问答: {e}")

# 3. AShareAnnouncement
print("  [3/4] AShareAnnouncement (公司公告)...")
try:
    from datetime import timedelta
    end_dt = datetime.strptime(TRADE_DATE, '%Y-%m-%d')
    start_dt = end_dt - timedelta(days=30)
    ann_md = client.get_announcement(STOCK_CODE, start_dt.strftime('%Y-%m-%d'), TRADE_DATE)
    if ann_md:
        section = format_announcement_section(ann_md)
        api_results["公司公告"] = len(section)
        print(f"  ✅ 公司公告: {len(ann_md)} 字符 → 格式化 {len(section)} 字符")
    else:
        api_results["公司公告"] = 0
        print(f"  ⚠️ 公司公告: 返回空 (该股可能无近期公告)")
except Exception as e:
    api_results["公司公告"] = 0
    print(f"  ❌ 公司公告: {e}")

# 4. CorporateResearchViewpoints
print("  [4/4] CorporateResearchViewpoints (研究观点)...")
try:
    research_md = client.get_corporate_research(STOCK_CODE)
    if research_md:
        section = format_research_viewpoints_section(research_md)
        api_results["研究观点"] = len(section)
        print(f"  ✅ 研究观点: {len(research_md)} 字符 → 格式化 {len(section)} 字符")
    else:
        api_results["研究观点"] = 0
        print(f"  ❌ 研究观点: 返回空")
except Exception as e:
    api_results["研究观点"] = 0
    print(f"  ❌ 研究观点: {e}")

success_count = sum(1 for v in api_results.values() if v > 0)
print(f"\n  📊 API 测试结果: {success_count}/{len(api_results)} 成功")

# ===== Step 2: 测试完整富集函数 =====
print(f"\n📊 Step 2: 测试 enrich_news_report 富集函数...\n")

from tradingagents.dataflows.gildata_news import enrich_news_report

# 模拟现有新闻数据
fake_news = """=== 📰 新闻数据来源: 东方财富实时新闻 ===
获取时间: 2026-04-08 09:30:00
数据长度: 500 字符

=== 📋 新闻内容 ===
# 格力电器 最新新闻

1. 格力电器发布2025年报，营收1900亿元
2. 格力空调市占率稳居行业第一
"""

enriched = enrich_news_report(STOCK_CODE, TRADE_DATE, fake_news)

print(f"  原始新闻长度: {len(fake_news)} 字符")
print(f"  富集后长度: {len(enriched)} 字符")
print(f"  增量: {len(enriched) - len(fake_news)} 字符")

# 检查各板块是否附加
checks = {
    "恒生聚源补充数据": "恒生聚源补充数据" in enriched,
    "个股舆情": "个股舆情" in enriched,
    "互动平台问答": "互动平台问答" in enriched,
    "券商研究观点": "券商研究观点" in enriched,
}

print(f"\n  📋 内容检查:")
for name, found in checks.items():
    print(f"    {'✅' if found else '⚠️'} {name}")

# ===== Step 3: 打印富集后的完整结果 =====
print(f"\n{'=' * 70}")
print(f"  富集后完整结果 ({len(enriched)} 字符)")
print(f"{'=' * 70}")

# 只打印 Gildata 补充部分
if "恒生聚源补充数据" in enriched:
    gildata_part = enriched.split("恒生聚源补充数据")[1]
    print("## 恒生聚源补充数据" + gildata_part[:3000])
    if len(gildata_part) > 3000:
        print(f"\n... (截断，完整内容 {len(gildata_part)} 字符)")
else:
    print("  ⚠️ 无 Gildata 补充数据")

print(f"\n{'=' * 70}")
print(f"  ✅ 验证完成！成功 {success_count}/{len(api_results)} 个 API")
print(f"{'=' * 70}")
