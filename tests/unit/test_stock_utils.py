"""StockUtils 单元测试 — 股票代码识别、市场判断、货币信息。"""

import pytest
from tradingagents.utils.stock_utils import (
    StockMarket,
    StockUtils,
    is_china_stock,
    is_hk_stock,
    is_us_stock,
    get_stock_market_info,
)


# ── identify_stock_market ──────────────────────────────────────────

class TestIdentifyStockMarket:

    def test_china_a_6digit(self):
        assert StockUtils.identify_stock_market("000001") == StockMarket.CHINA_A
        assert StockUtils.identify_stock_market("600519") == StockMarket.CHINA_A
        assert StockUtils.identify_stock_market("300750") == StockMarket.CHINA_A

    def test_hk_with_dot_hk(self):
        assert StockUtils.identify_stock_market("0700.HK") == StockMarket.HONG_KONG
        assert StockUtils.identify_stock_market("09988.HK") == StockMarket.HONG_KONG

    def test_hk_pure_digits_4_5(self):
        # 4 位纯数字当前会被识别为港股
        assert StockUtils.identify_stock_market("0700") == StockMarket.HONG_KONG
        assert StockUtils.identify_stock_market("9988") == StockMarket.HONG_KONG
        # 5 位纯数字也是港股
        assert StockUtils.identify_stock_market("09988") == StockMarket.HONG_KONG

    def test_us_letters(self):
        assert StockUtils.identify_stock_market("AAPL") == StockMarket.US
        assert StockUtils.identify_stock_market("TSLA") == StockMarket.US
        assert StockUtils.identify_stock_market("A") == StockMarket.US
        assert StockUtils.identify_stock_market("GOOGL") == StockMarket.US

    def test_unknown_empty(self):
        assert StockUtils.identify_stock_market("") == StockMarket.UNKNOWN
        assert StockUtils.identify_stock_market(None) == StockMarket.UNKNOWN

    def test_unknown_garbage(self):
        assert StockUtils.identify_stock_market("ABC123") == StockMarket.UNKNOWN
        assert StockUtils.identify_stock_market("!@#") == StockMarket.UNKNOWN

    def test_case_insensitive(self):
        assert StockUtils.identify_stock_market("aapl") == StockMarket.US
        assert StockUtils.identify_stock_market("0700.hk") == StockMarket.HONG_KONG


# ── is_*_stock shortcuts ────────────────────────────────────────────

class TestIsStockShortcuts:

    @pytest.mark.parametrize("code", ["000001", "600519", "300750"])
    def test_is_china_stock_true(self, code):
        assert is_china_stock(code) is True

    @pytest.mark.parametrize("code", ["AAPL", "0700.HK", "0700"])
    def test_is_china_stock_false(self, code):
        assert is_china_stock(code) is False

    @pytest.mark.parametrize("code", ["0700", "0700.HK", "9988"])
    def test_is_hk_stock_true(self, code):
        assert is_hk_stock(code) is True

    @pytest.mark.parametrize("code", ["AAPL", "000001"])
    def test_is_hk_stock_false(self, code):
        assert is_hk_stock(code) is False

    @pytest.mark.parametrize("code", ["AAPL", "TSLA"])
    def test_is_us_stock_true(self, code):
        assert is_us_stock(code) is True

    @pytest.mark.parametrize("code", ["000001", "0700.HK"])
    def test_is_us_stock_false(self, code):
        assert is_us_stock(code) is False


# ── get_currency_info ───────────────────────────────────────────────

class TestGetCurrencyInfo:

    def test_china(self):
        name, symbol = StockUtils.get_currency_info("000001")
        assert name == "人民币"
        assert symbol == "¥"

    def test_hk(self):
        name, symbol = StockUtils.get_currency_info("0700.HK")
        assert name == "港币"
        assert symbol == "HK$"

    def test_us(self):
        name, symbol = StockUtils.get_currency_info("AAPL")
        assert name == "美元"
        assert symbol == "$"

    def test_unknown(self):
        name, symbol = StockUtils.get_currency_info("")
        assert name == "未知"
        assert symbol == "?"


# ── get_data_source ─────────────────────────────────────────────────

class TestGetDataSource:

    def test_china(self):
        assert StockUtils.get_data_source("000001") == "china_unified"

    def test_hk(self):
        assert StockUtils.get_data_source("0700.HK") == "yahoo_finance"

    def test_us(self):
        assert StockUtils.get_data_source("AAPL") == "yahoo_finance"

    def test_unknown(self):
        assert StockUtils.get_data_source("") == "unknown"


# ── normalize_hk_ticker ─────────────────────────────────────────────

class TestNormalizeHkTicker:

    def test_add_hk_suffix(self):
        assert StockUtils.normalize_hk_ticker("0700") == "0700.HK"
        assert StockUtils.normalize_hk_ticker("9988") == "9988.HK"

    def test_already_has_suffix(self):
        assert StockUtils.normalize_hk_ticker("0700.HK") == "0700.HK"

    def test_empty(self):
        assert StockUtils.normalize_hk_ticker("") == ""
        assert StockUtils.normalize_hk_ticker(None) is None

    def test_case_insensitive(self):
        assert StockUtils.normalize_hk_ticker("0700.hk") == "0700.HK"


# ── get_market_info ─────────────────────────────────────────────────

class TestGetMarketInfo:

    def test_china_full_info(self):
        info = get_stock_market_info("000001")
        assert info["market"] == "china_a"
        assert info["market_name"] == "中国A股"
        assert info["is_china"] is True
        assert info["is_hk"] is False
        assert info["is_us"] is False
        assert info["currency_symbol"] == "¥"

    def test_hk_full_info(self):
        info = get_stock_market_info("0700.HK")
        assert info["market"] == "hong_kong"
        assert info["market_name"] == "港股"
        assert info["is_hk"] is True

    def test_us_full_info(self):
        info = get_stock_market_info("AAPL")
        assert info["market"] == "us"
        assert info["market_name"] == "美股"
        assert info["is_us"] is True

    def test_unknown_full_info(self):
        info = get_stock_market_info("")
        assert info["market_name"] == "未知市场"
