#!/usr/bin/env python3
"""
Tushare 新闻数据富集层

在新闻分析师现有报告基础上，附加 Tushare 提供的新闻/舆情数据：

1. 新闻快讯（市场实时快讯）
2. 新闻通讯（长篇新闻报道）
3. 新闻联播文字稿（宏观/政策信息）
4. 互动平台问答（上证E互动 + 深证互动易）

所有富集操作都是可选的，任一部分失败不影响主报告。
"""

import os
import re
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# ==================== 工具函数 ====================

def _get_tushare_api():
    """获取同步 tushare API 连接"""
    token = os.getenv("TUSHARE_TOKEN", "")
    if not token or len(token) < 30:
        return None
    try:
        import tushare as ts
        return ts.pro_api(token)
    except Exception as e:
        logger.debug(f"Tushare API 初始化失败: {e}")
        return None


def _normalize_ts_code(stock_code: str) -> tuple:
    """
    将股票代码转为 Tushare 格式并返回 (ts_code, exchange, clean_code)

    >>> _normalize_ts_code("000651")   -> ("000651.SZ", "SZ", "000651")
    >>> _normalize_ts_code("600519")   -> ("600519.SH", "SH", "600519")
    >>> _normalize_ts_code("000651.SZ") -> ("000651.SZ", "SZ", "000651")
    """
    stock_code = stock_code.strip().upper()
    # 已经是 Tushare 格式
    if '.' in stock_code:
        parts = stock_code.split('.')
        return stock_code, parts[1], parts[0]
    # 自动判断交易所
    if stock_code.startswith(('60', '68')):
        return f"{stock_code}.SH", "SH", stock_code
    else:
        return f"{stock_code}.SZ", "SZ", stock_code


def _truncate(text: str, max_len: int = 300) -> str:
    if not text or len(text) <= max_len:
        return text or ""
    return text[:max_len] + "..."


def _is_relevant(content: str, keywords: list) -> bool:
    """检查内容是否包含任一关键词"""
    if not content:
        return False
    return any(kw in content for kw in keywords)


# ==================== 各 API 格式化函数 ====================

def format_news_flash_section(df, stock_code: str) -> str:
    """格式化新闻快讯章节（从市场快讯中筛选与个股相关的）"""
    if df is None or df.empty:
        return ""

    # 构建关键词列表用于筛选
    clean_code = stock_code.replace('.SZ', '').replace('.SH', '').replace('.SS', '')
    keywords = [clean_code]

    # 尝试匹配公司名称（从 content 中提取可能的简称）
    section = "### 新闻快讯（数据源：Tushare）\n\n"

    # 筛选与个股相关的快讯
    relevant = []
    for _, row in df.iterrows():
        content = str(row.get('content', ''))
        title = str(row.get('title', ''))
        text = content + title
        if _is_relevant(text, keywords):
            relevant.append(row)

    if not relevant:
        # 如果没有直接相关的，取前5条市场快讯作为背景
        section += "> 未找到与该股直接相关的快讯，以下为当日市场重要快讯\n\n"
        relevant = [row for _, row in df.head(8).iterrows()]

    for row in relevant[:8]:
        content = _truncate(str(row.get('content', '')), 300)
        dt = str(row.get('datetime', ''))
        src = str(row.get('channels', ''))

        section += f"- **{content}**"
        if dt:
            section += f" [{dt[:16]}]"
        if src and src != 'None':
            section += f" ({src})"
        section += "\n"

    return section


def format_major_news_section(df) -> str:
    """格式化新闻通讯章节"""
    if df is None or df.empty:
        return ""

    section = "### 新闻通讯（数据源：Tushare）\n\n"

    # 取前8条
    for _, row in df.head(8).iterrows():
        title = str(row.get('title', '')).strip()
        pub_time = str(row.get('pub_time', ''))
        src = str(row.get('src', ''))
        url = str(row.get('url', ''))

        if title and title != 'None':
            section += f"- **{title}**"
            if src and src != 'None':
                section += f" — {src}"
            if pub_time and pub_time != 'None':
                section += f" ({pub_time[:16]})"
            section += "\n"

    return section


def format_cctv_news_section(df) -> str:
    """格式化新闻联播章节"""
    if df is None or df.empty:
        return ""

    section = "### 新闻联播要点（数据源：Tushare）\n\n"
    section += "> 央视新闻联播文字稿摘要，反映宏观政策导向\n\n"

    for _, row in df.iterrows():
        title = str(row.get('title', '')).strip()
        content = str(row.get('content', '')).strip()

        if title and title != 'None':
            section += f"**{title}**\n"
        if content and content != 'None':
            section += f"> {_truncate(content, 300)}\n\n"

    return section


def format_interactive_qa_section(df_qa) -> str:
    """格式化互动平台问答章节（上证E互动 + 深证互动易合并）"""
    if df_qa is None or df_qa.empty:
        return ""

    section = "### 投资者互动问答（数据源：Tushare）\n\n"
    section += "> 投资者在交易所互动平台的提问与公司回复\n\n"

    for _, row in df_qa.head(8).iterrows():
        question = str(row.get('q', '')).strip()
        answer = str(row.get('a', '')).strip()
        pub_time = str(row.get('pub_time', ''))
        trade_date = str(row.get('trade_date', ''))
        name = str(row.get('name', ''))

        if question and question != 'None':
            q_short = _truncate(question, 200)
            section += f"**Q**: {q_short}\n\n"
            if answer and answer != 'None':
                a_short = _truncate(answer, 300)
                section += f"**A**: {a_short}\n\n"
            section += "---\n\n"

    return section


# ==================== 主入口函数 ====================

def enrich_with_tushare_news(stock_code: str, trade_date: str,
                              existing_report: str) -> str:
    """
    新闻分析师 Tushare 数据富集（仅 A 股）

    在现有新闻数据基础上，附加 Tushare 的快讯/通讯/联播/互动数据。
    任一部分失败不影响其他部分和原始数据。

    Args:
        stock_code: 股票代码（如 "000651" 或 "000651.SZ"）
        trade_date: 交易日期（YYYY-MM-DD）
        existing_report: 现有的新闻数据

    Returns:
        附加了 Tushare 数据的增强新闻数据
    """
    api = _get_tushare_api()
    if not api:
        return existing_report

    ts_code, exchange, clean_code = _normalize_ts_code(stock_code)
    trade_date_compact = trade_date.replace('-', '')

    enrichment_parts = []

    # 1. 新闻快讯 (~1s)
    try:
        start_dt = f"{trade_date} 09:00:00"
        # 结束时间取次日早上8点以覆盖盘后新闻
        next_day = (datetime.strptime(trade_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        end_dt = f"{next_day} 08:00:00"

        df = api.news(start_date=start_dt, end_date=end_dt)
        if df is not None and not df.empty:
            section = format_news_flash_section(df, clean_code)
            if section:
                enrichment_parts.append(section)
                logger.info(f"Tushare 新闻快讯附加成功: {stock_code}, {len(df)} 条")
    except Exception as e:
        logger.debug(f"Tushare 新闻快讯获取失败: {e}")

    # 2. 新闻通讯 (~1s)
    try:
        start_dt = f"{trade_date} 00:00:00"
        next_day = (datetime.strptime(trade_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        end_dt = f"{next_day} 00:00:00"

        df = api.major_news(start_date=start_dt, end_date=end_dt)
        if df is not None and not df.empty:
            section = format_major_news_section(df)
            if section:
                enrichment_parts.append(section)
                logger.info(f"Tushare 新闻通讯附加成功: {stock_code}, {len(df)} 条")
    except Exception as e:
        logger.debug(f"Tushare 新闻通讯获取失败: {e}")

    # 3. 新闻联播 (~1s)
    try:
        df = api.cctv_news(date=trade_date_compact)
        if df is not None and not df.empty:
            section = format_cctv_news_section(df)
            if section:
                enrichment_parts.append(section)
                logger.info(f"Tushare 新闻联播附加成功: {stock_code}, {len(df)} 条")
    except Exception as e:
        logger.debug(f"Tushare 新闻联播获取失败: {e}")

    # 4. 互动平台问答 (~2s) — 上证E互动 + 深证互动易
    try:
        import pandas as pd
        dfs = []

        # 上证E互动
        try:
            df_sh = api.irm_qa_sh(ts_code=ts_code, start_date=trade_date_compact,
                                   end_date=trade_date_compact)
            if df_sh is not None and not df_sh.empty:
                dfs.append(df_sh)
        except Exception:
            pass

        # 深证互动易
        try:
            df_sz = api.irm_qa_sz(ts_code=ts_code, start_date=trade_date_compact,
                                   end_date=trade_date_compact)
            if df_sz is not None and not df_sz.empty:
                dfs.append(df_sz)
        except Exception:
            pass

        # 如果当日无数据，扩大到最近30天
        if not dfs:
            end_dt30 = trade_date_compact
            start_dt30 = (datetime.strptime(trade_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y%m%d')

            try:
                df_sh = api.irm_qa_sh(ts_code=ts_code, start_date=start_dt30, end_date=end_dt30)
                if df_sh is not None and not df_sh.empty:
                    dfs.append(df_sh)
            except Exception:
                pass

            try:
                df_sz = api.irm_qa_sz(ts_code=ts_code, start_date=start_dt30, end_date=end_dt30)
                if df_sz is not None and not df_sz.empty:
                    dfs.append(df_sz)
            except Exception:
                pass

        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            # 按时间排序（如果有 pub_time 列）
            if 'pub_time' in combined.columns:
                combined = combined.sort_values('pub_time', ascending=False)
            section = format_interactive_qa_section(combined)
            if section:
                enrichment_parts.append(section)
                logger.info(f"Tushare 互动问答附加成功: {stock_code}, {len(combined)} 条")

    except Exception as e:
        logger.debug(f"Tushare 互动问答获取失败: {e}")

    if not enrichment_parts:
        return existing_report

    enriched = existing_report + "\n\n---\n\n## Tushare 补充数据\n\n" + "\n".join(enrichment_parts)
    logger.info(f"Tushare 新闻数据富集完成: {stock_code}, 附加了 {len(enrichment_parts)} 个板块")
    return enriched
