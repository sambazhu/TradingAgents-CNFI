#!/usr/bin/env python3
"""
社交媒体分析师 Gildata + AKShare 情绪数据富集层

在社交媒体分析师现有报告基础上，附加多维度情绪数据：

A. AKShare 股吧情绪数据：
   1. 东方财富股吧综合评分（排名/关注指数）
   2. 30天综合评分走势
   3. 30天用户关注指数走势
   4. 买卖参与意愿及变化

B. Gildata 市场情绪数据：
   5. 实时主力/散户资金流向
   6. 融资融券余额
   7. 涨跌停统计

所有富集操作都是可选的，任一部分失败不影响主报告。
"""

import logging
from datetime import datetime
from typing import Optional

from tradingagents.dataflows.gildata_client import get_gildata_client
from tradingagents.dataflows.gildata_enrichment import (
    parse_markdown_table,
    find_column,
    safe_float,
)

logger = logging.getLogger(__name__)


# ==================== AKShare 格式化函数 ====================

def _get_akshare_comment(symbol: str) -> dict:
    """获取东方财富股吧综合评价"""
    try:
        import akshare as ak
        df = ak.stock_comment_em()
        row = df[df['代码'] == symbol]
        if row.empty:
            return {}
        r = row.iloc[0]
        return {
            'name': str(r.get('名称', '')),
            'price': safe_float(str(r.get('最新价', ''))),
            'change_pct': safe_float(str(r.get('涨跌幅', ''))),
            'turnover': safe_float(str(r.get('换手率', ''))),
            'pe': safe_float(str(r.get('市盈率', ''))),
            'main_cost': safe_float(str(r.get('主力成本', ''))),
            'inst_participation': safe_float(str(r.get('机构参与度', ''))),
            'score': safe_float(str(r.get('综合得分', ''))),
            'rank_change': safe_float(str(r.get('上升', ''))),
            'rank': int(r.get('目前排名', 0)) if r.get('目前排名') else None,
            'focus_index': safe_float(str(r.get('关注指数', ''))),
        }
    except Exception as e:
        logger.debug(f"AKShare 股吧综合评价获取失败: {e}")
        return {}


def _get_akshare_score_trend(symbol: str) -> list:
    """获取30天综合评分走势"""
    try:
        import akshare as ak
        df = ak.stock_comment_detail_zhpj_lspf_em(symbol=symbol)
        if df is None or df.empty:
            return []
        trend = []
        for _, row in df.tail(10).iterrows():
            trend.append({
                'date': str(row.get('交易日', '')),
                'score': float(row.get('评分', 0)),
            })
        return trend
    except Exception as e:
        logger.debug(f"AKShare 评分走势获取失败: {e}")
        return []


def _get_akshare_focus_trend(symbol: str) -> list:
    """获取30天用户关注指数走势"""
    try:
        import akshare as ak
        df = ak.stock_comment_detail_scrd_focus_em(symbol=symbol)
        if df is None or df.empty:
            return []
        trend = []
        for _, row in df.tail(10).iterrows():
            trend.append({
                'date': str(row.get('交易日', '')),
                'focus': float(row.get('用户关注指数', 0)),
            })
        return trend
    except Exception as e:
        logger.debug(f"AKShare 关注走势获取失败: {e}")
        return []


def _get_akshare_desire(symbol: str) -> list:
    """获取买卖参与意愿"""
    try:
        import akshare as ak
        df = ak.stock_comment_detail_scrd_desire_em(symbol=symbol)
        if df is None or df.empty:
            return []
        result = []
        for _, row in df.iterrows():
            result.append({
                'date': str(row.get('交易日期', '')),
                'desire': float(row.get('参与意愿', 0)),
                'avg5': float(row.get('5日平均参与意愿', 0)),
                'change': float(row.get('参与意愿变化', 0)),
            })
        return result
    except Exception as e:
        logger.debug(f"AKShare 参与意愿获取失败: {e}")
        return []


def format_akshare_overview(comment: dict) -> str:
    """格式化股吧综合评价章节"""
    if not comment:
        return ""

    section = "### 东方财富股吧综合评价\n\n"

    name = comment.get('name', '')
    score = comment.get('score')
    rank = comment.get('rank')
    focus = comment.get('focus_index')
    inst = comment.get('inst_participation')
    main_cost = comment.get('main_cost')
    price = comment.get('price')
    rank_change = comment.get('rank_change')

    if score is not None:
        # 评分等级
        if score >= 80:
            level = "强势"
        elif score >= 60:
            level = "中性偏强"
        elif score >= 40:
            level = "中性"
        else:
            level = "弱势"
        section += f"**综合评分**: {score:.1f}/100 ({level})\n\n"

    if rank is not None:
        direction = f"↑{int(rank_change)}" if rank_change and rank_change > 0 else f"↓{int(abs(rank_change))}" if rank_change and rank_change < 0 else "→"
        section += f"**市场排名**: 第{rank}名 ({direction})\n\n"

    if focus is not None:
        section += f"**关注指数**: {focus:.1f}/100\n\n"

    if inst is not None:
        section += f"**机构参与度**: {inst:.1%}\n\n"

    if main_cost and price:
        diff = price - main_cost
        diff_pct = diff / main_cost * 100 if main_cost else 0
        position = "高于" if diff > 0 else "低于"
        section += f"**主力成本**: {main_cost:.2f}元 (当前价{position}主力成本{abs(diff_pct):.1f}%)\n\n"

    return section


def format_akshare_score_trend(trend: list) -> str:
    """格式化评分走势章节"""
    if not trend:
        return ""

    section = "### 综合评分走势（近10日）\n\n"
    section += "| 日期 | 评分 | 趋势 |\n|------|------|------|\n"

    prev_score = None
    for item in trend:
        date = item['date']
        score = item['score']
        if prev_score is not None:
            diff = score - prev_score
            arrow = f"↑{diff:.1f}" if diff > 0 else f"↓{abs(diff):.1f}" if diff < 0 else "→"
        else:
            arrow = "-"
        section += f"| {date} | {score:.1f} | {arrow} |\n"
        prev_score = score

    return section


def format_akshare_focus_trend(trend: list) -> str:
    """格式化关注指数走势章节"""
    if not trend:
        return ""

    section = "### 用户关注指数走势（近10日）\n\n"
    section += "| 日期 | 关注指数 | 变化 |\n|------|---------|------|\n"

    prev_focus = None
    for item in trend:
        date = item['date']
        focus = item['focus']
        if prev_focus is not None:
            diff = focus - prev_focus
            arrow = f"↑{diff:.1f}" if diff > 0 else f"↓{abs(diff):.1f}" if diff < 0 else "→"
        else:
            arrow = "-"
        section += f"| {date} | {focus:.1f} | {arrow} |\n"
        prev_focus = focus

    return section


def format_akshare_desire(desire: list) -> str:
    """格式化参与意愿章节"""
    if not desire:
        return ""

    section = "### 投资者参与意愿\n\n"

    latest = desire[-1]
    desire_val = latest['desire']
    avg5 = latest['avg5']
    change = latest['change']

    if desire_val > 60:
        mood = "积极"
    elif desire_val > 40:
        mood = "中性"
    else:
        mood = "谨慎"

    section += f"**最新参与意愿**: {desire_val:.1f} ({mood})，5日均值 {avg5:.1f}，日变化 {change:+.1f}\n\n"

    section += "| 日期 | 参与意愿 | 5日均值 | 变化 |\n|------|---------|--------|------|\n"
    for item in desire:
        section += f"| {item['date']} | {item['desire']:.1f} | {item['avg5']:.1f} | {item['change']:+.1f} |\n"

    return section


# ==================== Gildata 格式化函数 ====================

def format_fund_flow_section(table_markdown: str) -> str:
    """格式化实时资金流向章节"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]
    data = rows[1]

    def get_val(keywords):
        idx = find_column(headers, keywords)
        if idx is not None and idx < len(data):
            return safe_float(data[idx])
        return None

    main_net = get_val(['主力净额'])
    super_large = get_val(['超大单资金净额'])
    large = get_val(['大单资金净额'])
    medium = get_val(['中单资金净额'])
    small = get_val(['小单资金净额'])
    main_in = get_val(['主力资金总流入'])
    main_out = get_val(['主力资金总流出'])

    section = "### 实时资金流向（数据源：恒生聚源）\n\n"

    if main_net is not None:
        direction = "净流入" if main_net > 0 else "净流出"
        section += f"**主力资金**: {main_net:+.2f}万元 ({direction})\n\n"

    if super_large is not None:
        section += f"- 超大单净额: {super_large:+.2f}万元\n"
    if large is not None:
        section += f"- 大单净额: {large:+.2f}万元\n"
    if medium is not None:
        section += f"- 中单净额: {medium:+.2f}万元\n"
    if small is not None:
        section += f"- 小单(散户)净额: {small:+.2f}万元\n"

    section += "\n> 主力资金为正表示主力买入，散户资金为正表示散户买入，两者方向相反\n\n"
    return section


def format_margin_section(table_markdown: str) -> str:
    """格式化融资融券章节"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]
    data = rows[1]

    def get_val(keywords):
        idx = find_column(headers, keywords)
        if idx is not None and idx < len(data):
            return safe_float(data[idx])
        return None

    rz_buy = get_val(['融资买入额'])
    rz_repay = get_val(['融资偿还额'])
    rz_balance = get_val(['融资余额'])
    rz_net_buy = get_val(['融资净买入额'])
    rq_sell = get_val(['融券卖出量'])
    rq_repay = get_val(['融券偿还量'])
    rq_balance = get_val(['融券余额'])

    section = "### 融资融券数据（数据源：恒生聚源）\n\n"

    if rz_balance is not None:
        section += f"**融资余额**: {rz_balance:.2f}元\n\n"

    if rz_net_buy is not None:
        direction = "净买入" if rz_net_buy > 0 else "净偿还"
        section += f"- 融资{direction}: {abs(rz_net_buy):.2f}元\n"
    if rz_buy is not None:
        section += f"- 融资买入: {rz_buy:.2f}元\n"
    if rz_repay is not None:
        section += f"- 融资偿还: {rz_repay:.2f}元\n"

    if rq_balance is not None:
        section += f"- 融券余额: {rq_balance:.2f}元\n"

    section += "\n> 融资净买入为正表示加杠杆做多，融券余额增加表示看空力量增强\n\n"
    return section


def format_market_breadth_section(table_markdown: str) -> str:
    """格式化涨跌停统计章节"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]
    data = rows[1]

    def get_val(keywords):
        idx = find_column(headers, keywords)
        if idx is not None and idx < len(data):
            v = data[idx].strip()
            try:
                return int(v)
            except (ValueError, TypeError):
                return None
        return None

    up = get_val(['上涨家数'])
    down = get_val(['下跌家数'])
    limit_up = get_val(['涨停家数'])
    limit_down = get_val(['跌停家数'])
    flat = get_val(['平盘家数'])
    total = get_val(['成分股家数'])
    trade_date = get_val(['交易日期'])

    section = "### 市场涨跌停概况（数据源：恒生聚源）\n\n"

    if up is not None and down is not None:
        ratio = up / (up + down) * 100 if (up + down) > 0 else 50
        breadth = "普涨" if ratio > 70 else "普跌" if ratio < 30 else "分化"
        section += f"**涨跌比**: {up}:{down} ({breadth})\n\n"

    if limit_up is not None:
        section += f"- 涨停: {limit_up}家\n"
    if limit_down is not None:
        section += f"- 跌停: {limit_down}家\n"
    if flat is not None:
        section += f"- 平盘: {flat}家\n"
    if total is not None:
        section += f"- 总计: {total}家\n"

    section += "\n"
    return section


# ==================== 主入口函数 ====================

def enrich_sentiment_report(symbol: str, trade_date: str,
                             existing_report: str) -> str:
    """
    社交媒体分析师数据富集（仅 A 股）

    附加 AKShare 股吧情绪数据 + Gildata 市场情绪数据。
    任一部分失败不影响其他部分和原始数据。

    Args:
        symbol: 股票代码（纯数字，如 "300750"）
        trade_date: 交易日期（YYYY-MM-DD）
        existing_report: 现有的情绪分析数据

    Returns:
        附加了情绪数据的增强报告
    """
    enrichment_parts = []

    # ===== A. AKShare 股吧情绪数据 =====

    # 1. 综合评价（~5s）
    try:
        comment = _get_akshare_comment(symbol)
        if comment:
            section = format_akshare_overview(comment)
            if section:
                enrichment_parts.append(section)
                logger.info(f"AKShare 股吧综合评价附加成功: {symbol}")
    except Exception as e:
        logger.debug(f"AKShare 股吧综合评价附加失败: {e}")

    # 2. 评分走势（~1s）
    try:
        trend = _get_akshare_score_trend(symbol)
        if trend:
            section = format_akshare_score_trend(trend)
            if section:
                enrichment_parts.append(section)
                logger.info(f"AKShare 评分走势附加成功: {symbol}")
    except Exception as e:
        logger.debug(f"AKShare 评分走势附加失败: {e}")

    # 3. 关注指数走势（~1s）
    try:
        focus = _get_akshare_focus_trend(symbol)
        if focus:
            section = format_akshare_focus_trend(focus)
            if section:
                enrichment_parts.append(section)
                logger.info(f"AKShare 关注走势附加成功: {symbol}")
    except Exception as e:
        logger.debug(f"AKShare 关注走势附加失败: {e}")

    # 4. 参与意愿（~1s）
    try:
        desire = _get_akshare_desire(symbol)
        if desire:
            section = format_akshare_desire(desire)
            if section:
                enrichment_parts.append(section)
                logger.info(f"AKShare 参与意愿附加成功: {symbol}")
    except Exception as e:
        logger.debug(f"AKShare 参与意愿附加失败: {e}")

    # ===== B. Gildata 市场情绪数据 =====

    client = get_gildata_client()
    if client:
        # 5. 资金流向（~3s）
        try:
            flow = client.get_real_stock_fund_flow(symbol)
            if flow:
                section = format_fund_flow_section(flow)
                if section:
                    enrichment_parts.append(section)
                    logger.info(f"Gildata 资金流向附加成功: {symbol}")
        except Exception as e:
            logger.debug(f"Gildata 资金流向附加失败: {e}")

        # 6. 融资融券（~3s）
        try:
            margin = client.get_securities_margin(symbol, trade_date)
            if margin:
                section = format_margin_section(margin)
                if section:
                    enrichment_parts.append(section)
                    logger.info(f"Gildata 融资融券附加成功: {symbol}")
        except Exception as e:
            logger.debug(f"Gildata 融资融券附加失败: {e}")

        # 7. 涨跌停统计（~3s）
        try:
            breadth = client.get_market_limit_count(trade_date)
            if breadth:
                section = format_market_breadth_section(breadth)
                if section:
                    enrichment_parts.append(section)
                    logger.info(f"Gildata 涨跌停统计附加成功: {symbol}")
        except Exception as e:
            logger.debug(f"Gildata 涨跌停统计附加失败: {e}")

    if not enrichment_parts:
        return existing_report

    enriched = existing_report + "\n\n---\n\n## 市场情绪数据\n\n" + "\n".join(enrichment_parts)
    logger.info(f"情绪数据富集完成: {symbol}, 附加了 {len(enrichment_parts)} 个板块")
    return enriched
