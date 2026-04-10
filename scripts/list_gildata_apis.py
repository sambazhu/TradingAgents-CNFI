#!/usr/bin/env python3
"""
列出 GildataClient 中所有已封装的 MCP API 接口。
从 gildata_client.py 源码中提取所有 self._call("ToolName", ...) 调用。
"""

import ast
import sys
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
CLIENT_FILE = ROOT / "tradingagents" / "dataflows" / "gildata_client.py"


def extract_apis(filepath: Path):
    """解析 gildata_client.py，提取所有 _call 调用的 tool_name 和参数签名。"""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source)

    apis = []

    for node in ast.walk(tree):
        # 找所有 def 方法
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name == "_call" or node.name.startswith("_"):
            continue

        # 在方法体内找 self._call("ToolName", {...}) 调用
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            func = child.func
            if not (isinstance(func, ast.Attribute) and func.attr == "_call"):
                continue

            # 提取 tool_name (第一个位置参数)
            args = child.args
            if not args:
                continue
            tool_name_node = args[0]
            if not isinstance(tool_name_node, ast.Constant):
                continue
            tool_name = tool_name_node.value

            # 提取方法参数签名
            params = [arg.arg for arg in node.args.args if arg.arg != "self"]

            # 提取 query 参数键名
            query_keys = []
            if len(args) > 1 and isinstance(args[1], ast.Dict):
                for key in args[1].keys:
                    if isinstance(key, ast.Constant):
                        query_keys.append(key.value)

            # 提取 docstring 第一行作为用途说明
            docstring = ""
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)):
                doc_raw = node.body[0].value.value
                if isinstance(doc_raw, str):
                    docstring = doc_raw.strip().split("\n")[0]

            apis.append({
                "method": node.name,
                "tool_name": tool_name,
                "params": params,
                "query_keys": query_keys,
                "docstring": docstring,
            })

    return apis


def main():
    if not CLIENT_FILE.exists():
        print(f"❌ 文件不存在: {CLIENT_FILE}")
        sys.exit(1)

    apis = extract_apis(CLIENT_FILE)

    print(f"{'='*90}")
    print(f"  GildataClient API 接口清单  (共 {len(apis)} 个)")
    print(f"  源文件: {CLIENT_FILE.relative_to(ROOT)}")
    print(f"{'='*90}")
    print()

    # 按类别分组（根据源码中的注释分隔符）
    categories = {
        "市场/技术指标": [],
        "估值数据": [],
        "资金流向": [],
        "风险分析": [],
        "基本面数据": [],
        "新闻/舆情数据": [],
        "情绪分析数据": [],
        "其他": [],
    }

    # 简单按 tool_name 前缀分类
    for api in apis:
        name = api["tool_name"]
        if name.startswith("Stock") and ("Quote" in name or "Value" in name or "Risk" in name):
            if "QuoteTech" in name or "DailyQuote" in name:
                categories["市场/技术指标"].append(api)
            elif "Value" in name:
                categories["估值数据"].append(api)
            elif "Risk" in name:
                categories["风险分析"].append(api)
            else:
                categories["其他"].append(api)
        elif name.startswith("AStock") or name.startswith("RealStock"):
            categories["资金流向"].append(api)
        elif name in ("FinancialAnalysis", "FinancialStatement", "CompanyBasicInfo",
                       "BonusStock", "MainOperIncData", "ConsensusExpectation",
                       "FinancialRatioComparison", "InstitutionalRating"):
            categories["基本面数据"].append(api)
        elif name in ("StockNewslist", "AShareAnnouncement", "InteractivePlatformReport",
                       "CorporateResearchViewpoints", "IndustryNewsFlash"):
            categories["新闻/舆情数据"].append(api)
        elif name in ("RealStockFundFlow", "StockSecuritiesMargin", "MarketLimitUpDownCount"):
            categories["情绪分析数据"].append(api)
        else:
            categories["其他"].append(api)

    idx = 0
    for cat, items in categories.items():
        if not items:
            continue
        print(f"  【{cat}】({len(items)} 个)")
        print(f"  {'-'*86}")
        for api in items:
            idx += 1
            params_str = ", ".join(api["params"])
            query_str = ", ".join(api["query_keys"])
            print(f"  {idx:>2}. {api['method']}()")
            print(f"      MCP Tool: {api['tool_name']}")
            print(f"      方法参数: ({params_str})")
            print(f"      查询字段: {query_str}")
            print(f"      用途: {api['docstring']}")
            print()

    # 输出 JSON 格式供程序使用
    print(f"\n{'='*90}")
    print("  JSON 格式 (供程序调用):")
    print(f"{'='*90}")
    import json
    print(json.dumps(apis, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
