#!/usr/bin/env python3
"""
Gildata 数据富集层

在市场分析师现有报告基础上，附加 Gildata 提供的丰富数据：
- 估值数据（PE/PB/PS/PCF/PEG/股息率/市值）
- 资金流向（大单/特大单/中单/小单净买入）
- 风险指标（Beta/Alpha/波动率/夏普比率）
- 风险因子暴露

所有富集操作都是可选的，任一部分失败不影响主报告。
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from tradingagents.dataflows.gildata_client import get_gildata_client

logger = logging.getLogger(__name__)


# ==================== Markdown 表格解析工具 ====================

def parse_markdown_table(table_markdown: str) -> list[list[str]]:
    """
    解析 Markdown 表格为二维列表

    Args:
        table_markdown: Markdown 表格字符串

    Returns:
        二维列表，第一行为表头，后续为数据行
    """
    lines = [line.strip() for line in table_markdown.strip().split('\n') if line.strip()]
    rows = []
    for line in lines:
        if line.startswith('|') and line.endswith('|'):
            cells = [cell.strip() for cell in line[1:-1].split('|')]
            # 跳过分隔行
            if cells and all(set(c) <= {'-', ':', ' '} for c in cells):
                continue
            rows.append(cells)
    return rows


def find_column(headers: list[str], keywords: list[str]) -> Optional[int]:
    """在表头中查找包含关键字的列索引"""
    for i, h in enumerate(headers):
        for kw in keywords:
            if kw in h:
                return i
    return None


def safe_float(value: str) -> Optional[float]:
    """安全转换字符串为浮点数"""
    if not value or value == '-' or value == '':
        return None
    try:
        return float(value.replace(',', ''))
    except (ValueError, TypeError):
        return None


def format_with_unit(value: Optional[float], unit: str = '') -> str:
    """格式化数值，None 返回 'N/A'"""
    if value is None:
        return 'N/A'
    if abs(value) >= 1e8:
        return f"{value / 1e8:.2f}亿{unit}"
    elif abs(value) >= 1e4:
        return f"{value / 1e4:.2f}万{unit}"
    else:
        return f"{value:.2f}{unit}"


# ==================== 格式化各数据板块 ====================

def format_valuation_section(table_markdown: str) -> str:
    """
    格式化估值数据板块

    从 StockValueAnalysis 返回的 Markdown 表格中提取关键估值指标
    """
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]
    data = rows[1]  # 取最新一行

    def get_val(keywords: list[str]) -> Optional[float]:
        idx = find_column(headers, keywords)
        if idx is not None and idx < len(data):
            return safe_float(data[idx])
        return None

    pe_ttm = get_val(['PE(TTM)'])
    pe_static = get_val(['PE(静)'])
    pb = get_val(['市净率PB'])
    pb_lf = get_val(['PB(Lf)'])
    ps_ttm = get_val(['PS(TTM)'])
    pcf_ttm = get_val(['PCF(TTM)'])
    peg = get_val(['PEG'])
    dividend_yield = get_val(['股息率'])
    rolling_dividend = get_val(['滚动股息率'])
    total_mv = get_val(['总市值（万元）'])
    circ_mv = get_val(['流通市值（万元）'])

    section = "---\n\n## 估值指标（数据源：恒生聚源）\n\n"

    section += "**市盈率/市净率**:\n"
    section += f"- PE(TTM): {pe_ttm:.2f}" if pe_ttm else "- PE(TTM): N/A"
    section += f"  |  PE(静): {pe_static:.2f}\n" if pe_static else "  |  PE(静): N/A\n"
    section += f"- PB: {pb:.2f}" if pb else "- PB: N/A"
    section += f"  |  PB(LF): {pb_lf:.2f}\n" if pb_lf else "  |  PB(LF): N/A\n"

    section += "\n**其他估值指标**:\n"
    if ps_ttm is not None:
        section += f"- PS(TTM): {ps_ttm:.2f}\n"
    if pcf_ttm is not None:
        section += f"- PCF(TTM): {pcf_ttm:.2f}\n"
    if peg is not None:
        section += f"- PEG: {peg:.2f}\n"

    section += "\n**股息与市值**:\n"
    if dividend_yield is not None:
        section += f"- 股息率: {dividend_yield:.2f}%\n"
    if rolling_dividend is not None:
        section += f"- 滚动股息率: {rolling_dividend:.2f}%\n"
    if total_mv is not None:
        # Gildata 返回的市值单位为万元，转换为亿元显示
        section += f"- 总市值: {total_mv / 1e4:.2f}亿元\n"
    if circ_mv is not None:
        section += f"- 流通市值: {circ_mv / 1e4:.2f}亿元\n"

    return section


def format_capital_flow_section(table_markdown: str) -> str:
    """
    格式化资金流向数据板块

    从 AStockCashFlow 返回的 Markdown 表格中提取资金流向数据
    """
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]

    def get_val(row: list[str], keywords: list[str]) -> Optional[float]:
        idx = find_column(headers, keywords)
        if idx is not None and idx < len(row):
            return safe_float(row[idx])
        return None

    # 最新一天
    latest = rows[1]

    # 找关键列
    dde = get_val(latest, ['大单净额DDE'])
    super_large = get_val(latest, ['特大单净买入'])
    large = get_val(latest, ['大单净买入'])
    medium = get_val(latest, ['中单净买入'])
    small = get_val(latest, ['小单净买入'])
    net_pct = get_val(latest, ['资金比'])
    red_days = get_val(latest, ['连红天数'])

    # 取日期字符串
    date_idx = find_column(headers, ['交易日期'])
    date_str = latest[date_idx] if date_idx is not None and date_idx < len(latest) else "N/A"

    section = "---\n\n## 资金流向分析（数据源：恒生聚源）\n\n"
    section += f"**最近交易日 ({date_str}) 资金流向**:\n\n"

    if dde is not None:
        direction = "净流入" if dde > 0 else "净流出"
        section += f"- 大单DDE净额: {dde:+.2f}万元 ({direction})\n"
    if super_large is not None:
        section += f"- 特大单净买入: {super_large:+.2f}万元\n"
    if large is not None:
        section += f"- 大单净买入: {large:+.2f}万元\n"
    if medium is not None:
        section += f"- 中单净买入: {medium:+.2f}万元\n"
    if small is not None:
        section += f"- 小单净买入: {small:+.2f}万元\n"
    if net_pct is not None:
        section += f"- 资金比: {net_pct:.2f}%\n"
    if red_days is not None:
        section += f"- 连红天数: {int(red_days)}天\n"

    # 如果有多天数据，添加近几日趋势
    if len(rows) > 3:
        section += f"\n**近{min(len(rows) - 1, 5)}日资金流向趋势**:\n\n"
        section += "| 日期 | 大单DDE(万) | 资金比(%) | 涨跌幅(%) |\n"
        section += "|------|------------|----------|----------|\n"
        for row in rows[1:min(6, len(rows))]:
            date_idx = find_column(headers, ['交易日期'])
            d = row[date_idx] if date_idx is not None and date_idx < len(row) else "N/A"
            dde_v = get_val(row, ['大单净额DDE'])
            pct_v = get_val(row, ['资金比'])
            chg_v = get_val(row, ['涨跌幅'])
            section += f"| {d} | {dde_v:+.2f} | {pct_v:.2f} | {chg_v:+.2f} |\n" if all(v is not None for v in [dde_v, pct_v, chg_v]) else ""

    return section


def format_risk_section(table_markdown: str) -> str:
    """
    格式化风险分析数据板块

    从 StockRiskAnalysis 返回的 Markdown 表格中提取风险指标
    """
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]
    latest = rows[1]

    def get_val(keywords: list[str]) -> Optional[float]:
        idx = find_column(headers, keywords)
        if idx is not None and idx < len(latest):
            return safe_float(latest[idx])
        return None

    beta_hs300 = get_val(['Beta值(相对沪深300'])
    beta_industry = get_val(['Beta值(相对申万行业'])
    alpha_hs300 = get_val(['阿尔法(相对沪深300'])
    vol_daily = get_val(['波动率(日步长)'])
    vol_weekly = get_val(['波动率(周步长)'])
    sharpe = get_val(['夏普比率'])
    mkt_ret_arith = get_val(['市场收益率(算术平均)'])
    mkt_ret_geo = get_val(['市场收益率(几何平均)'])

    section = "---\n\n## 风险分析指标（数据源：恒生聚源）\n\n"

    section += "**Beta/Alpha 分析**:\n"
    if beta_hs300 is not None:
        section += f"- Beta(相对沪深300, 一年): {beta_hs300:.2f}\n"
    if beta_industry is not None:
        section += f"- Beta(相对行业, 一年): {beta_industry:.2f}\n"
    if alpha_hs300 is not None:
        section += f"- Alpha(相对沪深300, 一年): {alpha_hs300:.4f}\n"

    section += "\n**波动性与收益**:\n"
    if vol_daily is not None:
        section += f"- 日波动率: {vol_daily:.4f}\n"
    if vol_weekly is not None:
        section += f"- 周波动率: {vol_weekly:.4f}\n"
    if sharpe is not None:
        section += f"- 夏普比率(年化): {sharpe:.2f}\n"
    if mkt_ret_arith is not None:
        section += f"- 市场收益率(算术平均): {mkt_ret_arith:.4f}\n"
    if mkt_ret_geo is not None:
        section += f"- 市场收益率(几何平均): {mkt_ret_geo:.4f}\n"

    return section


def format_risk_factor_section(table_markdown: str) -> str:
    """
    格式化风险因子板块

    从 StockRiskFactorReport 返回的 Markdown 表格中提取9大风险因子
    """
    rows = parse_markdown_table(table_markdown)
    if len(rows) < 2:
        return ""

    headers = rows[0]
    latest = rows[1]

    factor_names = [
        ('市值因子', ['市值因子']),
        ('波动因子', ['波动因子']),
        ('流动性因子', ['流动性因子']),
        ('动量因子', ['动量因子']),
        ('质量因子', ['质量因子']),
        ('价值因子', ['价值因子']),
        ('成长因子', ['成长因子']),
        ('情感因子', ['情感因子']),
        ('分红因子', ['分红因子']),
    ]

    section = "---\n\n## 风险因子暴露（数据源：恒生聚源）\n\n"

    factors_found = []
    for name, keywords in factor_names:
        idx = find_column(headers, keywords)
        if idx is not None and idx < len(latest):
            val = safe_float(latest[idx])
            if val is not None:
                direction = "正向暴露" if val > 0 else "负向暴露"
                factors_found.append(f"- **{name}**: {val:+.2f} ({direction})")

    if factors_found:
        section += "\n".join(factors_found)
        section += "\n\n> 因子值大于0表示正向暴露（倾向该因子特征），小于0表示负向暴露"
    else:
        section += "暂无风险因子数据\n"

    return section


# ==================== 主富集函数 ====================

def enrich_market_report(symbol: str, trade_date: str, existing_report: str) -> str:
    """
    为市场分析师报告附加 Gildata 富集数据

    附加内容：
    1. 估值数据（PE/PB/PS/股息率/市值）
    2. 资金流向（大单/特大单净买入）
    3. 风险指标（Beta/Alpha/波动率/夏普比率）
    4. 风险因子暴露

    任一部分失败不影响其他部分，也不影响原始报告。

    Args:
        symbol: 股票代码
        trade_date: 交易日期（YYYY-MM-DD）
        existing_report: 现有的市场分析师报告

    Returns:
        附加了 Gildata 数据的增强报告
    """
    client = get_gildata_client()
    if not client:
        return existing_report

    enrichment_parts = []

    # 1. 估值数据
    try:
        valuation = client.get_valuation(symbol, trade_date)
        if valuation:
            section = format_valuation_section(valuation)
            if section:
                enrichment_parts.append(section)
                logger.info(f"Gildata 估值数据附加成功: {symbol}")
    except Exception as e:
        logger.debug(f"Gildata 估值数据获取失败: {e}")

    # 2. 资金流向（最近30天）
    try:
        end_dt = datetime.strptime(trade_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=30)
        cashflow = client.get_capital_flow(
            symbol,
            start_dt.strftime('%Y-%m-%d'),
            end_dt.strftime('%Y-%m-%d')
        )
        if cashflow:
            section = format_capital_flow_section(cashflow)
            if section:
                enrichment_parts.append(section)
                logger.info(f"Gildata 资金流向数据附加成功: {symbol}")
    except Exception as e:
        logger.debug(f"Gildata 资金流向数据获取失败: {e}")

    # 3. 风险分析
    try:
        risk = client.get_risk_analysis(symbol, trade_date)
        if risk:
            section = format_risk_section(risk)
            if section:
                enrichment_parts.append(section)
                logger.info(f"Gildata 风险分析数据附加成功: {symbol}")
    except Exception as e:
        logger.debug(f"Gildata 风险分析数据获取失败: {e}")

    # 4. 风险因子
    try:
        factors = client.get_risk_factors(symbol, trade_date)
        if factors:
            section = format_risk_factor_section(factors)
            if section:
                enrichment_parts.append(section)
                logger.info(f"Gildata 风险因子数据附加成功: {symbol}")
    except Exception as e:
        logger.debug(f"Gildata 风险因子数据获取失败: {e}")

    if not enrichment_parts:
        logger.info(f"Gildata 无可用富集数据: {symbol}")
        return existing_report

    enriched = existing_report + "\n\n" + "\n".join(enrichment_parts)
    logger.info(f"Gildata 富集数据附加完成: {symbol}, 附加了 {len(enrichment_parts)} 个板块")
    return enriched


def apply_gildata_tech_indicators(data, symbol: str, trade_date: str) -> bool:
    """
    用 Gildata 预计算的技术指标覆盖 DataFrame 中的自算值

    更新 DataFrame 最后一行的 MA、MACD、KDJ、BOLL、RSI 值。
    如果 Gildata 不可用或失败，返回 False，保留自算值。

    Args:
        data: 包含技术指标的 DataFrame
        symbol: 股票代码
        trade_date: 交易日期

    Returns:
        是否成功应用了 Gildata 数据
    """
    client = get_gildata_client()
    if not client:
        return False

    try:
        table = client.get_tech_indicators(symbol, trade_date)
        if not table:
            return False

        rows = parse_markdown_table(table)
        if len(rows) < 2:
            return False

        headers = rows[0]
        latest = rows[1]

        def get_val(keywords: list[str]) -> Optional[float]:
            idx = find_column(headers, keywords)
            if idx is not None and idx < len(latest):
                return safe_float(latest[idx])
            return None

        # 更新最新行的技术指标
        last_idx = data.index[-1]

        # MA 系列
        col_map = {
            'ma5': ['MA5', '收盘价简单移动平均MA5'],
            'ma10': ['MA10', '收盘价简单移动平均MA10'],
            'ma20': ['MA20', '收盘价简单移动平均MA20'],
            'ma60': ['MA60', '收盘价简单移动平均MA60'],
        }
        for col, keywords in col_map.items():
            val = get_val(keywords)
            if val is not None and col in data.columns:
                data.at[last_idx, col] = val

        # MACD
        macd_dif = get_val(['DIFF'])
        macd_dea = get_val(['DEA'])
        macd_hist = get_val(['MACD'])
        if macd_dif is not None and 'macd_dif' in data.columns:
            data.at[last_idx, 'macd_dif'] = macd_dif
        if macd_dea is not None and 'macd_dea' in data.columns:
            data.at[last_idx, 'macd_dea'] = macd_dea
        if macd_hist is not None and 'macd' in data.columns:
            data.at[last_idx, 'macd'] = macd_hist

        # BOLL
        boll_upper = get_val(['UPPER', '上轨'])
        boll_mid = get_val(['MID', '中轨'])
        boll_lower = get_val(['LOWER', '下轨'])
        if boll_upper is not None and 'boll_upper' in data.columns:
            data.at[last_idx, 'boll_upper'] = boll_upper
        if boll_mid is not None and 'boll_mid' in data.columns:
            data.at[last_idx, 'boll_mid'] = boll_mid
        if boll_lower is not None and 'boll_lower' in data.columns:
            data.at[last_idx, 'boll_lower'] = boll_lower

        # RSI
        rsi_val = get_val(['RSI', '相对强弱指标'])
        if rsi_val is not None:
            if 'rsi' in data.columns:
                data.at[last_idx, 'rsi'] = rsi_val

        # KDJ（新增指标，DataFrame 中可能没有这些列）
        kdj_k = get_val(['K值', 'KDJ随机指标K'])
        kdj_d = get_val(['D值', 'KDJ随机指标D'])
        kdj_j = get_val(['J值', 'KDJ随机指标J'])
        if kdj_k is not None:
            data.at[last_idx, 'kdj_k'] = kdj_k
        if kdj_d is not None:
            data.at[last_idx, 'kdj_d'] = kdj_d
        if kdj_j is not None:
            data.at[last_idx, 'kdj_j'] = kdj_j

        logger.info(f"Gildata 技术指标覆盖成功: {symbol}")
        return True

    except Exception as e:
        logger.debug(f"Gildata 技术指标覆盖失败: {e}")
        return False
