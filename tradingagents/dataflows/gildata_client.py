#!/usr/bin/env python3
"""
Gildata（恒生聚源）API 客户端

通过 MCP JSON-RPC over HTTP 协议调用 Gildata API，获取 A 股市场数据。
提供预计算的技术指标、估值数据、资金流向和风险指标。

协议说明：
- 端点: https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token={TOKEN}
- 请求格式: MCP JSON-RPC，query 参数为双转义的 JSON 字符串
- 响应格式: JSON，results[0].table_markdown 包含 Markdown 表格数据
"""

import json
import os
import time
import logging
import threading
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_BASE_URL = "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api"
DEFAULT_TIMEOUT = 30
DEFAULT_CALL_INTERVAL = 3.0  # 默认调用间隔（秒），防止频率限制

# 全局锁和上次调用时间，用于跨方法控制调用频率
_last_call_time = 0.0
_call_lock = threading.Lock()


class GildataClient:
    """Gildata 恒生聚源 API 客户端"""

    def __init__(self, token: str, base_url: str = DEFAULT_BASE_URL, timeout: int = DEFAULT_TIMEOUT,
                 call_interval: float = DEFAULT_CALL_INTERVAL):
        self.token = token
        self.base_url = base_url
        self.timeout = timeout
        self.call_interval = call_interval
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _call(self, tool_name: str, query_params: dict) -> Optional[str]:
        """
        调用 Gildata MCP 工具

        Args:
            tool_name: 工具名称（如 StockQuoteTechIndex）
            query_params: 查询参数字典（如 {"ticker": "000001", "trade_date": "2025-04-01"}）

        Returns:
            table_markdown 字符串，失败返回 None
        """
        # 构造嵌套 JSON 字符串 query
        query_str = json.dumps(query_params, ensure_ascii=False)

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": {"query": query_str}
            },
            "id": self._next_id()
        }

        url = f"{self.base_url}?token={self.token}"

        # 调用间隔控制：确保两次调用之间有足够间隔，防止频率限制
        with _call_lock:
            global _last_call_time
            elapsed = time.time() - _last_call_time
            if elapsed < self.call_interval:
                wait = self.call_interval - elapsed
                logger.debug(f"Gildata 调用间隔等待 {wait:.1f}s")
                time.sleep(wait)
            _last_call_time = time.time()

        try:
            response = httpx.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json,text/event-stream"
                },
                timeout=self.timeout
            )

            if response.status_code != 200:
                logger.warning(f"Gildata API 返回非200状态码: {response.status_code}")
                return None

            data = response.json()

            # 检查 JSON-RPC 错误
            if "error" in data:
                err = data["error"]
                logger.warning(f"Gildata API 错误: code={err.get('code')}, message={err.get('message')}")
                return None

            # 提取 table_markdown
            result = data.get("result", {})
            content = result.get("content", [])
            if not content:
                logger.warning(f"Gildata API 返回空 content")
                return None

            text = content[0].get("text", "")
            parsed = json.loads(text)

            if parsed.get("code") != 0:
                logger.warning(f"Gildata API 业务错误: code={parsed.get('code')}")
                return None

            results = parsed.get("results", [])
            if not results:
                return None

            table_markdown = results[0].get("table_markdown", "")
            if not table_markdown or not table_markdown.strip():
                logger.debug(f"Gildata API {tool_name} 返回空表格")
                return None

            logger.info(f"Gildata API {tool_name} 成功返回 {len(table_markdown)} 字符")
            return table_markdown

        except httpx.TimeoutException:
            logger.warning(f"Gildata API 超时: {tool_name}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Gildata API 响应解析失败: {e}")
            return None
        except Exception as e:
            logger.warning(f"Gildata API 调用异常: {e}")
            return None

    # ==================== 市场/技术指标 ====================

    def get_tech_indicators(self, ticker: str, trade_date: str) -> Optional[str]:
        """
        获取预计算的技术指标（MA、MACD、KDJ、BOLL、RSI、VMA）

        Args:
            ticker: 股票代码（如 000001）
            trade_date: 交易日期（YYYY-MM-DD）

        Returns:
            Markdown 表格字符串
        """
        return self._call("StockQuoteTechIndex", {
            "ticker": ticker,
            "trade_date": trade_date
        })

    def get_daily_quote(self, ticker: str, trade_date: str) -> Optional[str]:
        """
        获取日行情数据

        Args:
            ticker: 股票代码
            trade_date: 交易日期（YYYY-MM-DD）

        Returns:
            Markdown 表格字符串
        """
        return self._call("StockDailyQuote", {
            "ticker": ticker,
            "trade_date": trade_date
        })

    # ==================== 估值数据 ====================

    def get_valuation(self, ticker: str, trade_date: str) -> Optional[str]:
        """
        获取估值数据（PE、PB、PS、PCF、PEG、股息率、市值、EV）

        Args:
            ticker: 股票代码
            trade_date: 交易日期（YYYY-MM-DD）

        Returns:
            Markdown 表格字符串
        """
        return self._call("StockValueAnalysis", {
            "ticker": ticker,
            "trade_date": trade_date
        })

    # ==================== 资金流向 ====================

    def get_capital_flow(self, ticker: str, start_date: str, end_date: str) -> Optional[str]:
        """
        获取资金流向数据（大单/特大单/中单/小单净买入、DDE、资金比）

        Args:
            ticker: 股票代码
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）

        Returns:
            Markdown 表格字符串
        """
        return self._call("AStockCashFlow", {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date
        })

    # ==================== 风险分析 ====================

    def get_risk_analysis(self, ticker: str, trade_date: str) -> Optional[str]:
        """
        获取风险分析数据（Beta、Alpha、波动率、夏普比率）

        Args:
            ticker: 股票代码
            trade_date: 交易日期（YYYY-MM-DD）

        Returns:
            Markdown 表格字符串
        """
        return self._call("StockRiskAnalysis", {
            "ticker": ticker,
            "trade_date": trade_date
        })

    def get_risk_factors(self, ticker: str, trade_date: str) -> Optional[str]:
        """
        获取风险因子暴露（9大因子：市值/波动/流动性/动量/质量/价值/成长/情感/分红）

        Args:
            ticker: 股票代码
            trade_date: 交易日期（YYYY-MM-DD）

        Returns:
            Markdown 表格字符串
        """
        return self._call("StockRiskFactorReport", {
            "ticker": ticker,
            "trade_date": trade_date
        })

    # ==================== 基本面数据 ====================

    def get_financial_analysis(self, ticker: str, trade_date: str) -> Optional[str]:
        """
        获取财务分析指标（ROE/ROA/毛利率/净利率/EPS/BPS/资产负债率/流动比率/速动比率/周转率/营收增速/净利润增速）

        Args:
            ticker: 股票代码
            trade_date: 交易日期（YYYY-MM-DD）

        Returns:
            Markdown 表格字符串
        """
        return self._call("FinancialAnalysis", {
            "ticker": ticker,
            "trade_date": trade_date
        })

    def get_financial_statement(self, ticker: str, report_date: str) -> Optional[str]:
        """
        获取财务报表数据（资产负债表/利润表/现金流量表）

        Args:
            ticker: 股票代码
            report_date: 报告期（YYYY-MM-DD，如 2025-12-31）

        Returns:
            Markdown 表格字符串
        """
        return self._call("FinancialStatement", {
            "ticker": ticker,
            "report_date": report_date
        })

    def get_company_basic_info(self, ticker: str) -> Optional[str]:
        """
        获取公司基本信息（行业分类/概念板块/公司简介）

        Args:
            ticker: 股票代码

        Returns:
            Markdown 表格字符串
        """
        return self._call("CompanyBasicInfo", {
            "ticker": ticker
        })

    def get_bonus_stock(self, ticker: str, start_date: str, end_date: str) -> Optional[str]:
        """
        获取分红记录（每股股息/除权除息日/分红方案）

        Args:
            ticker: 股票代码
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）

        Returns:
            Markdown 表格字符串
        """
        return self._call("BonusStock", {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date
        })

    def get_main_oper_inc_data(self, ticker: str, report_date: str) -> Optional[str]:
        """
        获取主营收入构成（按产品/行业/地区的收入、成本、利润、毛利率）

        Args:
            ticker: 股票代码
            report_date: 报告期（YYYY-MM-DD）

        Returns:
            Markdown 表格字符串
        """
        return self._call("MainOperIncData", {
            "ticker": ticker,
            "report_date": report_date
        })

    def get_consensus_expectation(self, ticker: str, forecast_year: str) -> Optional[str]:
        """
        获取一致预期（未来3年营收/净利润/EPS预测）

        Args:
            ticker: 股票代码
            forecast_year: 预测年份（如 2026）

        Returns:
            Markdown 表格字符串
        """
        return self._call("ConsensusExpectation", {
            "ticker": ticker,
            "forecast_year": forecast_year
        })

    def get_financial_ratio_comparison(self, ticker: str, trade_date: str) -> Optional[str]:
        """
        获取同行业财务比率对比（ROE/毛利率/净利率与行业均值对比）

        Args:
            ticker: 股票代码
            trade_date: 交易日期（YYYY-MM-DD）

        Returns:
            Markdown 表格字符串
        """
        return self._call("FinancialRatioComparison", {
            "ticker": ticker,
            "trade_date": trade_date
        })

    def get_institutional_rating(self, ticker: str, trade_date: str) -> Optional[str]:
        """
        获取机构评级（评级次数/分数/机构家数）

        Args:
            ticker: 股票代码
            trade_date: 交易日期（YYYY-MM-DD）

        Returns:
            Markdown 表格字符串
        """
        return self._call("InstitutionalRating", {
            "ticker": ticker,
            "trade_date": trade_date
        })

    # ==================== 新闻/舆情数据 ====================

    def get_stock_news(self, ticker: str, trade_date: str) -> Optional[str]:
        """
        获取股票相关舆情（带情绪标签）

        Args:
            ticker: 股票代码
            trade_date: 交易日期（YYYY-MM-DD）

        Returns:
            Markdown 表格字符串
        """
        return self._call("StockNewslist", {
            "ticker": ticker,
            "trade_date": trade_date
        })

    def get_announcement(self, ticker: str, start_date: str, end_date: str) -> Optional[str]:
        """
        获取A股上市公司公告（财报/重大事项/增减持等）

        Args:
            ticker: 股票代码
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）

        Returns:
            Markdown 表格字符串
        """
        return self._call("AShareAnnouncement", {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date
        })

    def get_interactive_platform(self, ticker: str, trade_date: str) -> Optional[str]:
        """
        获取互动平台投资者问答（交易所互动平台）

        Args:
            ticker: 股票代码
            trade_date: 交易日期（YYYY-MM-DD）

        Returns:
            Markdown 表格字符串
        """
        return self._call("InteractivePlatformReport", {
            "ticker": ticker,
            "trade_date": trade_date
        })

    def get_corporate_research(self, ticker: str) -> Optional[str]:
        """
        获取券商对公司的研究观点（盈利/市场份额/产品等维度）

        Args:
            ticker: 股票代码

        Returns:
            Markdown 表格字符串
        """
        return self._call("CorporateResearchViewpoints", {
            "ticker": ticker
        })

    def get_industry_news_flash(self, industry_type: str) -> Optional[str]:
        """
        获取行业公众号推送的产业快讯

        Args:
            industry_type: 行业类型

        Returns:
            Markdown 表格字符串
        """
        return self._call("IndustryNewsFlash", {
            "industry_type": industry_type
        })

    # ==================== 情绪分析数据 ====================

    def get_real_stock_fund_flow(self, ticker: str) -> Optional[str]:
        """
        获取个股实时资金流向（主力/散户）

        Args:
            ticker: 股票代码

        Returns:
            Markdown 表格字符串
        """
        return self._call("RealStockFundFlow", {"ticker": ticker})

    def get_securities_margin(self, ticker: str, trade_date: str) -> Optional[str]:
        """
        获取融资融券数据

        Args:
            ticker: 股票代码
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            Markdown 表格字符串
        """
        return self._call("StockSecuritiesMargin", {
            "ticker": ticker,
            "trade_date": trade_date
        })

    def get_market_limit_count(self, trade_date: str) -> Optional[str]:
        """
        获取市场涨跌停统计

        Args:
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            Markdown 表格字符串
        """
        return self._call("MarketLimitUpDownCount", {
            "trade_date": trade_date
        })


# ==================== 全局单例 ====================

_gildata_client: Optional[GildataClient] = None


def _get_gildata_token_from_db() -> str:
    """从激活的系统配置中读取 Gildata token，作为环境变量缺失时的兜底。"""
    try:
        from app.core.database import get_mongo_db_sync

        db = get_mongo_db_sync()
        config = db.system_configs.find_one({"is_active": True}, sort=[("version", -1)]) or {}
        for ds in config.get("data_source_configs", []):
            ds_type = str(ds.get("type", "")).lower()
            ds_name = str(ds.get("name", "")).lower()
            if ds_type == "gildata" or ds_name == "gildata":
                return str(ds.get("api_key", "")).strip()
    except Exception as e:
        logger.debug(f"从数据库读取 Gildata token 失败: {e}")

    return ""


def get_gildata_client() -> Optional[GildataClient]:
    """
    获取 Gildata 客户端单例

    Returns:
        GildataClient 实例，如果未配置 token 则返回 None
    """
    global _gildata_client

    if _gildata_client is not None:
        return _gildata_client

    token = os.getenv("GILDATA_API_TOKEN", "").strip() or _get_gildata_token_from_db()
    if not token:
        logger.debug("Gildata token 未配置（环境变量和数据库均未找到），Gildata 数据不可用")
        return None

    base_url = os.getenv("GILDATA_API_BASE_URL", DEFAULT_BASE_URL)
    timeout = int(os.getenv("GILDATA_TIMEOUT", str(DEFAULT_TIMEOUT)))
    call_interval = float(os.getenv("GILDATA_CALL_INTERVAL", str(DEFAULT_CALL_INTERVAL)))

    try:
        _gildata_client = GildataClient(token=token, base_url=base_url, timeout=timeout,
                                         call_interval=call_interval)
        logger.info(f"Gildata 客户端初始化成功")
        return _gildata_client
    except Exception as e:
        logger.warning(f"Gildata 客户端初始化失败: {e}")
        return None


def is_gildata_enabled() -> bool:
    """检查 Gildata 是否已启用（token 已配置）"""
    return bool(os.getenv("GILDATA_API_TOKEN", "").strip() or _get_gildata_token_from_db())
