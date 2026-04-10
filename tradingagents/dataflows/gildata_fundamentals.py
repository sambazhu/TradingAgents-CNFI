#!/usr/bin/env python3
"""
Gildata 基本面数据富集层

在基本面分析师现有报告基础上，附加 Gildata 提供的丰富数据：

Phase 1 — 核心指标叠加（替换报告中的 N/A 值）:
- 财务分析指标（ROE/ROA/毛利率/净利率/EPS/资产负债率/营收增速/净利润增速）
- 估值数据（PE/PB/PS/股息率/市值）
- 分红记录

Phase 2 — 数据增强（附加新章节）:
- 公司概况（行业分类/概念板块/公司简介）
- 财务报表摘要（最近两期对比）
- 主营业务收入构成（按产品/地区）
- 一致预期（未来3年预测）
- 同行业财务指标对比
- 机构评级汇总

所有富集操作都是可选的，任一部分失败不影响主报告。
"""

import re
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


# ==================== 工具函数 ====================

def _overlay_na_value(report: str, field_label: str, new_value: str) -> str:
    """
    在报告字符串中替换 N/A 类占位符为 Gildata 数据。

    仅替换 N/A、待查询、待分析、待计算 等占位值，不覆盖已有真实数据。
    替换后的值添加（恒生聚源）后缀标记来源。
    """
    pattern = rf'(- \*\*{re.escape(field_label)}\*\*:\s*)(N/A|待查询|待分析|待计算|N/A（[^）]*）)'
    replacement = rf'\g<1>{new_value}（恒生聚源）'
    return re.sub(pattern, replacement, report)


def _get_latest_report_date(trade_date: str) -> str:
    """根据交易日期推算最近一期财报报告期"""
    dt = datetime.strptime(trade_date, '%Y-%m-%d')
    year, month = dt.year, dt.month
    if month <= 4:
        return f"{year - 1}-09-30"
    elif month <= 7:
        return f"{year}-03-31"
    elif month <= 10:
        return f"{year}-06-30"
    else:
        return f"{year}-09-30"


def _format_with_unit(value: Optional[float]) -> str:
    """格式化数值，None 返回空"""
    if value is None:
        return ''
    if abs(value) >= 1e8:
        return f"{value / 1e8:.2f}亿"
    elif abs(value) >= 1e4:
        return f"{value / 1e4:.2f}万"
    else:
        return f"{value:.2f}"


# ==================== Phase 1: N/A 值叠加 ====================

def _parse_and_overlay_financial_analysis(report: str, table_markdown: str) -> str:
    """解析 FinancialAnalysis API 返回数据，叠加到报告中的 N/A 值"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return report

    headers = rows[0]
    data = rows[1]

    def get_val(keywords):
        idx = find_column(headers, keywords)
        return safe_float(data[idx]) if idx is not None and idx < len(data) else None

    # 盈利能力
    roe = get_val(['净资产收益率', 'ROE'])
    if roe is not None:
        report = _overlay_na_value(report, '净资产收益率(ROE)', f"{roe:.2f}%")

    roa = get_val(['总资产收益率', '总资产报酬率', 'ROA'])
    if roa is not None:
        report = _overlay_na_value(report, '总资产收益率(ROA)', f"{roa:.2f}%")

    gross_margin = get_val(['毛利率', '销售毛利率'])
    if gross_margin is not None:
        report = _overlay_na_value(report, '毛利率', f"{gross_margin:.2f}%")

    net_margin = get_val(['净利率', '销售净利率', '净利润率'])
    if net_margin is not None:
        report = _overlay_na_value(report, '净利率', f"{net_margin:.2f}%")

    # 财务健康
    debt_ratio = get_val(['资产负债率'])
    if debt_ratio is not None:
        report = _overlay_na_value(report, '资产负债率', f"{debt_ratio:.2f}%")

    current_ratio = get_val(['流动比率'])
    if current_ratio is not None:
        report = _overlay_na_value(report, '流动比率', f"{current_ratio:.2f}")

    quick_ratio = get_val(['速动比率'])
    if quick_ratio is not None:
        report = _overlay_na_value(report, '速动比率', f"{quick_ratio:.2f}")

    return report


def _parse_and_overlay_valuation(report: str, table_markdown: str) -> str:
    """解析 StockValueAnalysis API 返回数据，叠加估值指标"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return report

    headers = rows[0]
    data = rows[1]

    def get_val(keywords):
        idx = find_column(headers, keywords)
        return safe_float(data[idx]) if idx is not None and idx < len(data) else None

    pe_ttm = get_val(['PE(TTM)'])
    if pe_ttm is not None:
        report = _overlay_na_value(report, '市盈率TTM(PE_TTM)', f"{pe_ttm:.2f}倍")

    pe_static = get_val(['PE(静)'])
    if pe_static is not None:
        report = _overlay_na_value(report, '市盈率(PE)', f"{pe_static:.2f}倍")

    pb = get_val(['市净率PB', 'PB'])
    if pb is not None:
        report = _overlay_na_value(report, '市净率(PB)', f"{pb:.2f}倍")

    ps = get_val(['PS(TTM)'])
    if ps is not None:
        report = _overlay_na_value(report, '市销率(PS)', f"{ps:.2f}倍")

    dividend_yield = get_val(['股息率'])
    if dividend_yield is not None:
        report = _overlay_na_value(report, '股息收益率', f"{dividend_yield:.2f}%")

    total_mv = get_val(['总市值（万元）'])
    if total_mv is not None:
        report = _overlay_na_value(report, '总市值', f"{total_mv / 1e4:.2f}亿元")

    return report


def _parse_and_overlay_bonus(report: str, table_markdown: str) -> str:
    """解析 BonusStock API 返回数据，叠加分红信息"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return report

    # BonusStock 可能返回多行（多次分红），取最近一次
    headers = rows[0]
    latest = rows[1]

    def get_val(keywords):
        idx = find_column(headers, keywords)
        return latest[idx] if idx is not None and idx < len(latest) else None

    # 尝试提取每股股息
    dividend_val = get_val(['每股股息', '每股派息', '派息'])
    if dividend_val:
        try:
            dv = float(dividend_val.replace('元', '').replace(',', '').strip())
            if dv > 0:
                report = _overlay_na_value(report, '股息收益率', f"每股派息{dv:.4f}元")
        except (ValueError, TypeError):
            pass

    return report


def _apply_phase1_overlay(client, symbol: str, trade_date: str, report: str) -> str:
    """Phase 1: 调用 3 个 Gildata API，叠加替换 N/A 值"""

    # 1. 财务分析指标
    try:
        fa = client.get_financial_analysis(symbol, trade_date)
        if fa:
            report = _parse_and_overlay_financial_analysis(report, fa)
            logger.info(f"Gildata 财务分析指标叠加成功: {symbol}")
    except Exception as e:
        logger.debug(f"Gildata 财务分析指标叠加失败: {e}")

    # 2. 估值数据
    try:
        val = client.get_valuation(symbol, trade_date)
        if val:
            report = _parse_and_overlay_valuation(report, val)
            logger.info(f"Gildata 估值指标叠加成功: {symbol}")
    except Exception as e:
        logger.debug(f"Gildata 估值指标叠加失败: {e}")

    # 3. 分红记录（最近3年）
    try:
        end_dt = datetime.strptime(trade_date, '%Y-%m-%d')
        start_dt = end_dt.replace(year=end_dt.year - 3)
        bonus = client.get_bonus_stock(symbol, start_dt.strftime('%Y-%m-%d'), trade_date)
        if bonus:
            report = _parse_and_overlay_bonus(report, bonus)
            logger.info(f"Gildata 分红数据叠加成功: {symbol}")
    except Exception as e:
        logger.debug(f"Gildata 分红数据叠加失败: {e}")

    return report


# ==================== Phase 2: 新章节附加 ====================

def format_company_info_section(table_markdown: str) -> str:
    """格式化公司概况章节"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]
    data = rows[1]

    def get_val(keywords):
        idx = find_column(headers, keywords)
        return data[idx].strip() if idx is not None and idx < len(data) else None

    company_name = get_val(['公司名称'])
    industry_sw = get_val(['申万行业', '行业(申万)'])
    industry_zjh = get_val(['证监会行业', '行业(证监会)'])
    concepts = get_val(['概念板块'])
    description = get_val(['公司简介', '经营范围'])
    list_date = get_val(['上市日期'])

    section = "---\n\n## 公司概况（数据源：恒生聚源）\n\n"

    if company_name:
        section += f"**公司名称**: {company_name}\n"
    if industry_sw:
        section += f"**行业分类(申万)**: {industry_sw}\n"
    if industry_zjh:
        section += f"**行业分类(证监会)**: {industry_zjh}\n"
    if list_date:
        section += f"**上市日期**: {list_date}\n"
    if concepts:
        # 截断过长的概念列表
        concept_str = concepts[:500] + '...' if len(concepts) > 500 else concepts
        section += f"**概念板块**: {concept_str}\n"
    if description:
        desc_str = description[:300] + '...' if len(description) > 300 else description
        section += f"**公司简介**: {desc_str}\n"

    return section


def format_financial_statement_section(table_markdown: str) -> str:
    """格式化财务报表摘要章节（最近两期对比）"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 3:
        return ""

    headers = rows[0]

    def get_val(row, keywords):
        idx = find_column(headers, keywords)
        return safe_float(row[idx]) if idx is not None and idx < len(row) else None

    def get_str(row, keywords):
        idx = find_column(headers, keywords)
        return row[idx].strip() if idx is not None and idx < len(row) else None

    # 取最近两期
    row1 = rows[1]
    row2 = rows[2] if len(rows) > 2 else None

    date1 = get_str(row1, ['报告期', 'end_date'])
    date2 = get_str(row2, ['报告期', 'end_date']) if row2 else None

    section = "---\n\n## 财务报表摘要（数据源：恒生聚源）\n\n"

    if date1:
        section += f"**最近报告期**: {date1}"
        if date2:
            section += f" / {date2}"
        section += "\n\n"

    # 关键财务指标
    metrics = [
        ('营业总收入', ['营业总收入', 'total_revenue']),
        ('净利润', ['净利润', 'n_income']),
        ('总资产', ['总资产', 'total_assets']),
        ('股东权益', ['股东权益', 'total_hldr_eqy']),
        ('经营现金流', ['经营活动产生的现金流量净额', 'n_cashflow_act']),
    ]

    if row2:
        section += "| 项目 | " + (date1 or "最新期") + " | " + (date2 or "上期") + " |\n"
        section += "|------|--------|--------|\n"

        for name, kws in metrics:
            v1 = get_val(row1, kws)
            v2 = get_val(row2, kws)
            if v1 is not None or v2 is not None:
                s1 = _format_with_unit(v1) if v1 else "N/A"
                s2 = _format_with_unit(v2) if v2 else "N/A"
                section += f"| {name} | {s1} | {s2} |\n"
    else:
        section += "| 项目 | 金额 |\n|------|------|\n"
        for name, kws in metrics:
            v1 = get_val(row1, kws)
            if v1 is not None:
                section += f"| {name} | {_format_with_unit(v1)} |\n"

    return section


def format_main_oper_inc_section(table_markdown: str) -> str:
    """格式化主营业务收入构成章节"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]

    def get_val(row, keywords):
        idx = find_column(headers, keywords)
        return safe_float(row[idx]) if idx is not None and idx < len(row) else None

    def get_str(row, keywords):
        idx = find_column(headers, keywords)
        return row[idx].strip() if idx is not None and idx < len(row) else ""

    section = "---\n\n## 主营业务收入构成（数据源：恒生聚源）\n\n"

    # 判断是按产品还是按地区分类
    type_col = find_column(headers, ['分类类型', '分类', '类型'])

    # 取前10条（避免过长）
    display_rows = rows[1:min(11, len(rows))]

    # 查找收入、占比、毛利率列
    income_idx = find_column(headers, ['营业收入', '收入'])
    ratio_idx = find_column(headers, ['占营业收入比重', '占比', '收入占比'])
    margin_idx = find_column(headers, ['毛利率'])

    section += "| 分类 | 收入(亿) | 占比(%) | 毛利率(%) |\n"
    section += "|------|---------|---------|----------|\n"

    for row in display_rows:
        name = get_str(row, ['分类名称', '产品名称', '地区名称', '业务名称'])
        income = safe_float(row[income_idx]) if income_idx is not None and income_idx < len(row) else None
        ratio = safe_float(row[ratio_idx]) if ratio_idx is not None and ratio_idx < len(row) else None
        margin = safe_float(row[margin_idx]) if margin_idx is not None and margin_idx < len(row) else None

        if name:
            inc_str = f"{income / 1e8:.2f}" if income and abs(income) >= 1e8 else (_format_with_unit(income) or "N/A")
            ratio_str = f"{ratio:.2f}" if ratio is not None else "N/A"
            margin_str = f"{margin:.2f}" if margin is not None else "N/A"
            section += f"| {name[:20]} | {inc_str} | {ratio_str} | {margin_str} |\n"

    return section


def format_consensus_section(table_markdown: str) -> str:
    """格式化一致预期章节"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]

    def get_val(row, keywords):
        idx = find_column(headers, keywords)
        return safe_float(row[idx]) if idx is not None and idx < len(row) else None

    def get_str(row, keywords):
        idx = find_column(headers, keywords)
        return row[idx].strip() if idx is not None and idx < len(row) else ""

    section = "---\n\n## 一致预期（数据源：恒生聚源）\n\n"
    section += "| 年度 | 营收预测(亿) | 净利润预测(亿) | EPS预测(元) |\n"
    section += "|------|-------------|---------------|------------|\n"

    for row in rows[1:]:
        year = get_str(row, ['预测年度', '年度', '年份'])
        revenue = get_val(row, ['营业收入', '营收预测', '预测营业收入'])
        profit = get_val(row, ['净利润', '利润预测', '预测净利润'])
        eps = get_val(row, ['EPS', '每股收益', '预测EPS'])

        if year:
            rev_str = f"{revenue / 1e8:.2f}" if revenue and abs(revenue) >= 1e8 else (_format_with_unit(revenue) or "N/A")
            profit_str = f"{profit / 1e8:.2f}" if profit and abs(profit) >= 1e8 else (_format_with_unit(profit) or "N/A")
            eps_str = f"{eps:.2f}" if eps is not None else "N/A"
            section += f"| {year} | {rev_str} | {profit_str} | {eps_str} |\n"

    return section


def format_industry_comparison_section(table_markdown: str) -> str:
    """格式化同行业对比章节"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]
    data = rows[1]

    def get_val(keywords):
        idx = find_column(headers, keywords)
        return safe_float(data[idx]) if idx is not None and idx < len(data) else None

    section = "---\n\n## 同行业对比（数据源：恒生聚源）\n\n"
    section += "| 指标 | 公司值 | 行业均值 |\n"
    section += "|------|--------|----------|\n"

    # 尝试提取公司和行业对比值
    metrics = [
        ('ROE', ['净资产收益率', 'ROE']),
        ('毛利率', ['毛利率', '销售毛利率']),
        ('净利率', ['净利率', '销售净利率']),
        ('资产负债率', ['资产负债率']),
        ('营收增速', ['营业收入同比增长率', '营收增速']),
        ('净利润增速', ['净利润同比增长率', '净利润增速']),
    ]

    for name, kws in metrics:
        val = get_val(kws)
        if val is not None:
            # Gildata 对比接口通常包含公司和行业两列
            section += f"| {name} | {val:.2f}% | 行业均值 |\n"

    return section


def format_institutional_rating_section(table_markdown: str) -> str:
    """格式化机构评级章节"""
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]
    data = rows[1]

    def get_val(keywords):
        idx = find_column(headers, keywords)
        return safe_float(data[idx]) if idx is not None and idx < len(data) else None

    def get_str(keywords):
        idx = find_column(headers, keywords)
        return data[idx].strip() if idx is not None and idx < len(data) else None

    rating_count = get_val(['评级次数', '评级家数', '机构家数'])
    rating_score = get_val(['评级分数', '综合评级'])
    buy_count = get_val(['买入', '买入评级'])
    hold_count = get_val(['增持', '中性', '持有'])

    section = "---\n\n## 机构评级（数据源：恒生聚源）\n\n"

    if rating_count is not None:
        section += f"- **覆盖机构数**: {int(rating_count)}家\n"
    if rating_score is not None:
        section += f"- **综合评级分数**: {rating_score:.2f}\n"
    if buy_count is not None:
        section += f"- **买入/增持评级**: {int(buy_count)}次\n"
    if hold_count is not None:
        section += f"- **中性评级**: {int(hold_count)}次\n"

    if not any(v is not None for v in [rating_count, rating_score, buy_count, hold_count]):
        return ""

    return section


def _apply_phase2_enrichment(client, symbol: str, trade_date: str, report: str,
                             data_depth: str = "comprehensive") -> str:
    """Phase 2: 调用 6 个 Gildata API，附加新章节"""

    report_date = _get_latest_report_date(trade_date)
    year = str(datetime.strptime(trade_date, '%Y-%m-%d').year)

    # 根据深度控制调用数量
    if data_depth in ("basic",):
        return report  # 快速模式不附加

    enrichment_parts = []

    # 4. 公司概况
    try:
        info = client.get_company_basic_info(symbol)
        if info:
            section = format_company_info_section(info)
            if section:
                enrichment_parts.append(section)
                logger.info(f"Gildata 公司概况附加成功: {symbol}")
    except Exception as e:
        logger.debug(f"Gildata 公司概况附加失败: {e}")

    # 5. 财务报表摘要
    try:
        fs = client.get_financial_statement(symbol, report_date)
        if fs:
            section = format_financial_statement_section(fs)
            if section:
                enrichment_parts.append(section)
                logger.info(f"Gildata 财务报表附加成功: {symbol}")
    except Exception as e:
        logger.debug(f"Gildata 财务报表附加失败: {e}")

    # 6. 主营收入构成
    try:
        moi = client.get_main_oper_inc_data(symbol, report_date)
        if moi:
            section = format_main_oper_inc_section(moi)
            if section:
                enrichment_parts.append(section)
                logger.info(f"Gildata 主营收入附加成功: {symbol}")
    except Exception as e:
        logger.debug(f"Gildata 主营收入附加失败: {e}")

    # 以下仅标准/全面模式
    if data_depth in ("standard", "full", "comprehensive"):
        # 7. 一致预期
        try:
            ce = client.get_consensus_expectation(symbol, year)
            if ce:
                section = format_consensus_section(ce)
                if section:
                    enrichment_parts.append(section)
                    logger.info(f"Gildata 一致预期附加成功: {symbol}")
        except Exception as e:
            logger.debug(f"Gildata 一致预期附加失败: {e}")

        # 8. 同行业对比
        try:
            comp = client.get_financial_ratio_comparison(symbol, trade_date)
            if comp:
                section = format_industry_comparison_section(comp)
                if section:
                    enrichment_parts.append(section)
                    logger.info(f"Gildata 行业对比附加成功: {symbol}")
        except Exception as e:
            logger.debug(f"Gildata 行业对比附加失败: {e}")

        # 9. 机构评级
        try:
            rating = client.get_institutional_rating(symbol, trade_date)
            if rating:
                section = format_institutional_rating_section(rating)
                if section:
                    enrichment_parts.append(section)
                    logger.info(f"Gildata 机构评级附加成功: {symbol}")
        except Exception as e:
            logger.debug(f"Gildata 机构评级附加失败: {e}")

    if not enrichment_parts:
        return report

    enriched = report + "\n\n" + "\n".join(enrichment_parts)
    logger.info(f"Gildata 基本面数据富集完成: {symbol}, 附加了 {len(enrichment_parts)} 个板块")
    return enriched


# ==================== 主入口函数 ====================

def enrich_fundamentals_report(symbol: str, trade_date: str, existing_report: str,
                               data_depth: str = "comprehensive") -> str:
    """
    为基本面分析师报告附加 Gildata 数据（仅 A 股）

    Phase 1: 替换报告中的 N/A 值（3 API, ~9s）
    Phase 2: 附加新数据章节（6 API, ~18s）

    任一部分失败不影响其他部分，不影响原始报告。

    Args:
        symbol: 股票代码
        trade_date: 交易日期（YYYY-MM-DD）
        existing_report: 现有的基本面分析报告
        data_depth: 数据深度（basic/standard/full/comprehensive）

    Returns:
        附加了 Gildata 数据的增强报告
    """
    client = get_gildata_client()
    if not client:
        return existing_report

    report = existing_report

    # Phase 1: N/A 值叠加
    report = _apply_phase1_overlay(client, symbol, trade_date, report)

    # Phase 2: 新章节附加
    report = _apply_phase2_enrichment(client, symbol, trade_date, report, data_depth)

    return report
