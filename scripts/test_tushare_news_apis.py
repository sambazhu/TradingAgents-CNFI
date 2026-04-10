#!/usr/bin/env python3
"""
测试 Tushare 8 个新闻类 API 的数据可访问性
验证当前 token 是否有权限访问这些接口
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tushare as ts
from datetime import datetime, timedelta

# 从 .env 读取 token
TOKEN = "3e7c48ec9139989fd838de40439c7ddc9b6e021f6604ec35777a4248"

print("=" * 70)
print(f"  Tushare 新闻类 API 可访问性测试")
print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  Token: {TOKEN[:8]}...{TOKEN[-4:]}")
print("=" * 70)

pro = ts.pro_api(TOKEN)

# 测试用的日期
today = datetime.now()
yesterday = today - timedelta(days=1)
today_str = today.strftime('%Y%m%d')
yesterday_str = yesterday.strftime('%Y%m%d')
# 用更早的日期确保有数据
test_date = '20250120'
test_date_start = '20250101'

results = {}

def test_api(name, func, **kwargs):
    """测试单个 API"""
    print(f"\n{'─' * 50}")
    print(f"📋 {name}")
    print(f"   参数: {kwargs}")
    try:
        df = func(**kwargs)
        if df is not None and len(df) > 0:
            print(f"   ✅ 成功! 返回 {len(df)} 条记录")
            print(f"   列名: {list(df.columns)}")
            print(f"   前2行预览:")
            print(df.head(2).to_string(max_colwidth=60))
            results[name] = {"status": "✅", "count": len(df), "columns": list(df.columns)}
        else:
            print(f"   ⚠️ 返回空数据 (可能是无数据，也可能是无权限)")
            results[name] = {"status": "⚠️", "count": 0, "columns": []}
    except Exception as e:
        err_msg = str(e)
        print(f"   ❌ 失败: {err_msg}")
        # 判断是否是权限问题
        if "权限" in err_msg or "permission" in err_msg.lower() or "积分" in err_msg or "无权" in err_msg:
            results[name] = {"status": "🔒", "error": "无权限"}
        else:
            results[name] = {"status": "❌", "error": err_msg[:100]}

# ===== 测试 8 个 API =====

# 1. news — 新闻快讯
test_api("1. news (新闻快讯)",
         pro.news,
         src='cls',
         start_date='2025-01-20 09:00:00',
         end_date='2025-01-20 22:00:00')

# 2. major_news — 新闻通讯
test_api("2. major_news (新闻通讯)",
         pro.major_news,
         src='财联社',
         start_date='2025-01-20 00:00:00',
         end_date='2025-01-21 00:00:00')

# 3. cctv_news — 新闻联播
test_api("3. cctv_news (新闻联播)",
         pro.cctv_news,
         date='20250120')

# 4. anns_d — 上市公司公告
test_api("4. anns_d (上市公司公告)",
         pro.anns_d,
         ts_code='000651.SZ',
         start_date='20250101',
         end_date='20250120')

# 5. research_report — 券商研究报告
test_api("5. research_report (券商研究报告)",
         pro.research_report,
         ts_code='000651.SZ',
         start_date='20250101',
         end_date='20250120')

# 6. irm_qa_sh — 上证E互动
test_api("6. irm_qa_sh (上证E互动)",
         pro.irm_qa_sh,
         ts_code='600519.SH',
         trade_date='20250120')

# 7. irm_qa_sz — 深证互动易
test_api("7. irm_qa_sz (深证互动易)",
         pro.irm_qa_sz,
         ts_code='000651.SZ',
         trade_date='20250120')

# 8. npr — 国家政策法规
test_api("8. npr (国家政策法规)",
         pro.npr,
         end_date='2025-01-20 17:00:00')

# ===== 汇总 =====
print(f"\n{'=' * 70}")
print(f"  测试结果汇总")
print(f"{'=' * 70}")

for name, info in results.items():
    if info["status"] in ("✅", "⚠️"):
        count = info.get("count", 0)
        print(f"  {info['status']} {name}: {count} 条记录")
    elif info["status"] == "🔒":
        print(f"  {info['status']} {name}: {info.get('error', '无权限')}")
    else:
        print(f"  {info['status']} {name}: {info.get('error', '未知错误')}")

accessible = sum(1 for v in results.values() if v["status"] == "✅")
total = len(results)
print(f"\n  📊 可用 API: {accessible}/{total}")

if accessible == total:
    print("  🎉 所有 API 均可正常访问!")
elif accessible > 0:
    print(f"  ⚠️ {total - accessible} 个 API 不可用，可能需要单独申请权限")
else:
    print("  ❌ 所有 API 均不可用，请检查 token 和权限设置")

print(f"\n{'=' * 70}")
