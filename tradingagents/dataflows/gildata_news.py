#!/usr/bin/env python3
"""
Gildata 新闻数据富集层

在新闻分析师现有报告基础上，附加 Gildata 提供的新闻/舆情/公告数据：

1. 个股舆情（带情绪标签的结构化新闻）
2. 互动平台投资者问答
3. 公司公告（A股上市公司公告）
4. 券商研究观点

所有富集操作都是可选的，任一部分失败不影响主报告。
"""

import re
import logging
import html
from datetime import datetime, timedelta
from typing import Optional

from tradingagents.dataflows.gildata_client import get_gildata_client
from tradingagents.dataflows.gildata_enrichment import (
    parse_markdown_table,
    find_column,
    safe_float,
)

logger = logging.getLogger(__name__)


# ==================== 工具函数 ====================

def _clean_html(text: str) -> str:
    """去除 HTML 标签，还原实体，清理空白"""
    if not text:
        return ""
    # 去除 style 块
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    # 去除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 还原 HTML 实体
    text = html.unescape(text)
    # 合并空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _truncate(text: str, max_len: int = 300) -> str:
    """截断过长的文本"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


# ==================== 各 API 格式化函数 ====================

def format_stock_news_section(table_markdown: str) -> str:
    """格式化个股舆情章节"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]

    def get_str(row, keywords):
        idx = find_column(headers, keywords)
        return row[idx].strip() if idx is not None and idx < len(row) else ""

    # 取最近 5 条新闻
    display_rows = rows[1:min(6, len(rows))]

    section = "### 个股舆情（数据源：恒生聚源）\n\n"

    for row in display_rows:
        title = get_str(row, ['新闻标题', '标题'])
        content_raw = get_str(row, ['新闻原文内容', '内容'])
        pub_time = get_str(row, ['发布时间', '时间'])

        # 清理 HTML
        content = _clean_html(content_raw)
        content = _truncate(content, 400)

        if title:
            section += f"**{title}**"
            if pub_time and pub_time != "-":
                section += f" [{pub_time}]"
            section += "\n"
        if content:
            section += f"> {content}\n\n"

    return section


def format_interactive_qa_section(table_markdown: str) -> str:
    """格式化互动平台问答章节"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]

    def get_str(row, keywords):
        idx = find_column(headers, keywords)
        return row[idx].strip() if idx is not None and idx < len(row) else ""

    # 取最近 8 条问答
    display_rows = rows[1:min(9, len(rows))]

    section = "### 互动平台问答（数据源：恒生聚源）\n\n"
    section += "> 投资者在交易所互动平台的提问与公司回复\n\n"

    for row in display_rows:
        question = get_str(row, ['问题情况', '问题'])
        answer = get_str(row, ['回复情况', '回复'])
        q_time = get_str(row, ['提问时间'])
        a_time = get_str(row, ['回复时间'])

        if question:
            q_short = _truncate(question.replace('<br>', ' '), 200)
            section += f"**Q** ({q_time}): {q_short}\n\n"
            if answer:
                a_short = _truncate(answer.replace('<br>', ' '), 300)
                section += f"**A** ({a_time}): {a_short}\n\n"
            section += "---\n\n"

    return section


def format_announcement_section(table_markdown: str) -> str:
    """格式化公司公告章节"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]

    def get_str(row, keywords):
        idx = find_column(headers, keywords)
        return row[idx].strip() if idx is not None and idx < len(row) else ""

    # 取最近 10 条公告
    display_rows = rows[1:min(11, len(rows))]

    section = "### 公司公告（数据源：恒生聚源）\n\n"

    for row in display_rows:
        title = get_str(row, ['公告标题', '标题', '公告名称'])
        ann_type = get_str(row, ['公告类型', '类型'])
        pub_date = get_str(row, ['公告日期', '发布日期', '日期'])

        if title:
            line = f"- **{title}**"
            if ann_type:
                line += f" [{ann_type}]"
            if pub_date:
                line += f" ({pub_date})"
            section += line + "\n"

    return section


def format_research_viewpoints_section(table_markdown: str, trade_date: str = "") -> str:
    """格式化券商研究观点章节"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]

    def get_str(row, keywords):
        idx = find_column(headers, keywords)
        return row[idx].strip() if idx is not None and idx < len(row) else ""

    cutoff_date = None
    if trade_date:
        try:
            cutoff_date = datetime.strptime(trade_date, "%Y-%m-%d").date()
        except ValueError:
            cutoff_date = None

    filtered_rows = []
    for row in rows[1:]:
        if cutoff_date is None:
            filtered_rows.append(row)
            continue

        pub_time = get_str(row, ['研报发布时间', '发布时间'])
        if not pub_time:
            filtered_rows.append(row)
            continue

        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", pub_time)
        if not date_match:
            filtered_rows.append(row)
            continue

        try:
            pub_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()
        except ValueError:
            filtered_rows.append(row)
            continue

        if pub_date <= cutoff_date:
            filtered_rows.append(row)

    # 按日期降序取最近的观点，最多 8 条
    display_rows = filtered_rows[:8]
    if not display_rows:
        return ""

    section = "### 券商研究观点（数据源：恒生聚源）\n\n"

    for row in display_rows:
        pub_time = get_str(row, ['研报发布时间', '发布时间'])
        institution = get_str(row, ['研报机构', '机构'])
        author = get_str(row, ['研报作者', '作者'])
        title = get_str(row, ['研报标题', '标题'])
        viewpoint = get_str(row, ['公司研究研报观点', '研报观点', '观点'])
        dimension = get_str(row, ['公司研究维度', '研究维度', '维度'])

        if viewpoint:
            vp_short = _truncate(viewpoint, 400)
            section += f"**{title or '研报观点'}**"
            if institution:
                section += f" — {institution}"
            if author:
                section += f" ({author})"
            if pub_time:
                section += f" [{pub_time[:10]}]"
            section += "\n"
            if dimension:
                section += f"*维度: {dimension}*\n"
            section += f"> {vp_short}\n\n"

    return section


def format_industry_flash_section(table_markdown: str) -> str:
    """格式化行业快讯章节"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]

    def get_str(row, keywords):
        idx = find_column(headers, keywords)
        return row[idx].strip() if idx is not None and idx < len(row) else ""

    # 取最近 5 条快讯
    display_rows = rows[1:min(6, len(rows))]

    section = "### 行业快讯（数据源：恒生聚源）\n\n"

    for row in display_rows:
        title = get_str(row, ['标题', '新闻标题'])
        content = get_str(row, ['内容', '摘要', '快讯内容'])
        pub_time = get_str(row, ['发布时间', '时间'])

        if title or content:
            text = title or content
            text = _truncate(_clean_html(text), 300)
            section += f"- **{text}**"
            if pub_time and pub_time != "-":
                section += f" ({pub_time})"
            section += "\n"

    return section


def _parse_industry_type(company_info_markdown: str) -> Optional[str]:
    """从公司基本信息中解析行业类型"""
    rows = parse_markdown_table(company_info_markdown)
    if len(rows) < 2:
        return None

    headers = rows[0]

    def get_str(keywords):
        idx = find_column(headers, keywords)
        return rows[1][idx].strip() if idx is not None and idx < len(rows[1]) else ""

    # 尝试从申万行业分类中提取
    industry = get_str(['申万行业', '行业(申万)'])
    if industry:
        # 提取三级分类的最后一层，如 "家用电器-白色家电-空调" -> "空调"
        parts = industry.split('-')
        return parts[-1].strip() if parts else industry

    return None


# ==================== 主入口函数 ====================

def enrich_news_report(symbol: str, trade_date: str, existing_report: str,
                       data_depth: str = "standard") -> str:
    """
    新闻分析师 Gildata 数据富集（仅 A 股）

    在现有新闻数据基础上，附加 Gildata 的舆情/问答/研报数据。
    任一部分失败不影响其他部分和原始数据。

    Args:
        symbol: 股票代码
        trade_date: 交易日期（YYYY-MM-DD）
        existing_report: 现有的新闻数据
        data_depth: 数据深度（basic/standard/full/comprehensive）

    Returns:
        附加了 Gildata 数据的增强新闻数据
    """
    client = get_gildata_client()
    if not client:
        return existing_report

    enrichment_parts = []

    # 1. 个股舆情（~3s）
    try:
        news = client.get_stock_news(symbol, trade_date)
        if news:
            section = format_stock_news_section(news)
            if section:
                enrichment_parts.append(section)
                logger.info(f"Gildata 个股舆情附加成功: {symbol}")
    except Exception as e:
        logger.debug(f"Gildata 个股舆情附加失败: {e}")

    # 2. 互动平台问答（~3s）
    try:
        qa = client.get_interactive_platform(symbol, trade_date)
        if qa:
            section = format_interactive_qa_section(qa)
            if section:
                enrichment_parts.append(section)
                logger.info(f"Gildata 互动问答附加成功: {symbol}")
    except Exception as e:
        logger.debug(f"Gildata 互动问答附加失败: {e}")

    # 3. 公司公告（~3s）
    try:
        end_dt = datetime.strptime(trade_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=30)
        ann = client.get_announcement(symbol, start_dt.strftime('%Y-%m-%d'), trade_date)
        if ann:
            section = format_announcement_section(ann)
            if section:
                enrichment_parts.append(section)
                logger.info(f"Gildata 公司公告附加成功: {symbol}")
    except Exception as e:
        logger.debug(f"Gildata 公司公告附加失败: {e}")

    # 以下仅标准/全面模式
    if data_depth in ("standard", "full", "comprehensive"):
        # 4. 券商研究观点（~3s）
        try:
            research = client.get_corporate_research(symbol)
            if research:
                section = format_research_viewpoints_section(research, trade_date)
                if section:
                    enrichment_parts.append(section)
                    logger.info(f"Gildata 研究观点附加成功: {symbol}")
        except Exception as e:
            logger.debug(f"Gildata 研究观点附加失败: {e}")

    if not enrichment_parts:
        return existing_report

    enriched = existing_report + "\n\n---\n\n## 恒生聚源补充数据\n\n" + "\n".join(enrichment_parts)
    logger.info(f"Gildata 新闻数据富集完成: {symbol}, 附加了 {len(enrichment_parts)} 个板块")
    return enriched
