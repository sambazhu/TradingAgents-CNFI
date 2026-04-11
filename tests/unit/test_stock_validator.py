"""StockDataPreparer 单元测试 — 代码格式验证与市场自动检测（不含外部数据获取）。"""

import pytest
from tradingagents.utils.stock_validator import (
    StockDataPreparer,
    StockDataPreparationResult,
    StockValidationResult,  # 向后兼容别名
)


@pytest.fixture
def preparer():
    return StockDataPreparer()


# ── StockDataPreparationResult.to_dict ──────────────────────────────

class TestStockDataPreparationResult:

    def test_to_dict_keys(self):
        r = StockDataPreparationResult(
            is_valid=True, stock_code="000001", market_type="A股",
            stock_name="平安银行"
        )
        d = r.to_dict()
        expected_keys = {
            "is_valid", "stock_code", "market_type", "stock_name",
            "error_message", "suggestion", "has_historical_data",
            "has_basic_info", "data_period_days", "cache_status",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_defaults(self):
        r = StockDataPreparationResult(is_valid=False, stock_code="XXX")
        d = r.to_dict()
        assert d["is_valid"] is False
        assert d["stock_name"] == ""
        assert d["error_message"] == ""

    def test_backward_compat_alias(self):
        assert StockValidationResult is StockDataPreparationResult


# ── _validate_format ────────────────────────────────────────────────

class TestValidateFormat:

    def test_empty_code(self, preparer):
        r = preparer._validate_format("", "auto")
        assert r.is_valid is False
        assert "不能为空" in r.error_message

    def test_too_long(self, preparer):
        r = preparer._validate_format("12345678901", "auto")
        assert r.is_valid is False
        assert "10" in r.error_message

    def test_china_valid(self, preparer):
        r = preparer._validate_format("000001", "A股")
        assert r.is_valid is True

    def test_china_invalid_letters(self, preparer):
        r = preparer._validate_format("ABC123", "A股")
        assert r.is_valid is False
        assert "6位数字" in r.error_message

    def test_china_invalid_short(self, preparer):
        r = preparer._validate_format("00001", "A股")
        assert r.is_valid is False

    def test_hk_valid_dot_hk(self, preparer):
        r = preparer._validate_format("0700.HK", "港股")
        assert r.is_valid is True

    def test_hk_valid_pure_digits(self, preparer):
        r = preparer._validate_format("0700", "港股")
        assert r.is_valid is True

    def test_hk_invalid(self, preparer):
        r = preparer._validate_format("ABC", "港股")
        assert r.is_valid is False

    def test_us_valid(self, preparer):
        r = preparer._validate_format("AAPL", "美股")
        assert r.is_valid is True

    def test_us_invalid_numbers(self, preparer):
        r = preparer._validate_format("12345", "美股")
        assert r.is_valid is False
        assert "字母" in r.error_message

    def test_us_case_insensitive(self, preparer):
        r = preparer._validate_format("aapl", "美股")
        assert r.is_valid is True

    def test_auto_market_skips_specific_validation(self, preparer):
        """auto 模式不做特定市场格式校验，只做空/长度检查。"""
        r = preparer._validate_format("000001", "auto")
        assert r.is_valid is True


# ── _detect_market_type ─────────────────────────────────────────────

class TestDetectMarketType:

    def test_china_6digit(self, preparer):
        assert preparer._detect_market_type("000001") == "A股"

    def test_hk_dot_hk(self, preparer):
        assert preparer._detect_market_type("0700.HK") == "港股"

    def test_hk_pure_4digit(self, preparer):
        assert preparer._detect_market_type("0700") == "港股"

    def test_hk_5digit(self, preparer):
        assert preparer._detect_market_type("09988") == "港股"

    def test_us_letters(self, preparer):
        assert preparer._detect_market_type("AAPL") == "美股"

    def test_unknown(self, preparer):
        assert preparer._detect_market_type("ABC123") == "未知"

    def test_empty(self, preparer):
        assert preparer._detect_market_type("") == "未知"


# ── _prepare_data_by_market — 不支持的市场类型 ──────────────────────

class TestPrepareDataByMarket:

    def test_unsupported_market(self, preparer):
        r = preparer._prepare_data_by_market("000001", "日本", 30, "2025-01-01")
        assert r.is_valid is False
        assert "不支持" in r.error_message
