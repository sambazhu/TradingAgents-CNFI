"""SignalProcessor 单元测试 — 信号解析、价格提取、动作映射。"""

import json
import pytest
from unittest.mock import MagicMock, patch

from tradingagents.graph.signal_processing import SignalProcessor


@pytest.fixture
def processor():
    """创建一个 mock LLM 的 SignalProcessor 实例。"""
    mock_llm = MagicMock()
    return SignalProcessor(quick_thinking_llm=mock_llm)


# ── process_signal 空输入 / 无效输入 ────────────────────────────────

class TestProcessSignalInvalidInput:

    def test_none_input(self, processor):
        result = processor.process_signal(None, "000001")
        assert result["action"] == "持有"
        assert result["target_price"] is None

    def test_empty_string(self, processor):
        result = processor.process_signal("", "000001")
        assert result["action"] == "持有"

    def test_whitespace_only(self, processor):
        result = processor.process_signal("   ", "000001")
        assert result["action"] == "持有"


# ── _extract_simple_decision — action 提取 ──────────────────────────

class TestExtractSimpleDecision:

    def test_action_buy(self, processor):
        result = processor._extract_simple_decision("建议买入该股票，目标价45元")
        assert result["action"] == "买入"

    def test_action_sell(self, processor):
        result = processor._extract_simple_decision("建议卖出该股票，止损")
        assert result["action"] == "卖出"

    def test_action_hold(self, processor):
        result = processor._extract_simple_decision("建议持有观望")
        assert result["action"] == "持有"

    def test_action_overweight(self, processor):
        result = processor._extract_simple_decision("建议增持该股票")
        assert result["action"] == "增持"

    def test_action_underweight(self, processor):
        result = processor._extract_simple_decision("建议减持该股票")
        assert result["action"] == "减持"

    def test_action_default_hold(self, processor):
        result = processor._extract_simple_decision("无法判断市场趋势")
        assert result["action"] == "持有"

    def test_english_buy(self, processor):
        result = processor._extract_simple_decision("We recommend BUY this stock")
        assert result["action"] == "买入"

    def test_english_sell(self, processor):
        result = processor._extract_simple_decision("We recommend SELL immediately")
        assert result["action"] == "卖出"


# ── _extract_simple_decision — 价格提取 ─────────────────────────────

class TestExtractSimpleDecisionPrice:

    def test_target_price(self, processor):
        result = processor._extract_simple_decision("目标价位：45.50")
        assert result["target_price"] == 45.50

    def test_price_with_yuan(self, processor):
        result = processor._extract_simple_decision("建议买入，价格35.8元")
        assert result["target_price"] == 35.8

    def test_price_with_symbol(self, processor):
        result = processor._extract_simple_decision("建议买入，¥42.5")
        assert result["target_price"] == 42.5

    def test_no_price(self, processor):
        result = processor._extract_simple_decision("建议持有观望")
        # 无明确价格时可能是 None 或推算值
        assert result["target_price"] is None or isinstance(result["target_price"], float)


# ── _smart_price_estimation ─────────────────────────────────────────

class TestSmartPriceEstimation:

    def test_with_current_price_and_percentage_buy(self, processor):
        text = "当前价格：10.00，上涨 15%"
        result = processor._smart_price_estimation(text, "买入", is_china=True)
        assert result == round(10.00 * 1.15, 2)

    def test_with_current_price_and_percentage_sell(self, processor):
        text = "当前价格：10.00，上涨 15%"
        result = processor._smart_price_estimation(text, "卖出", is_china=True)
        assert result == round(10.00 * 0.85, 2)

    def test_with_current_price_no_percentage_buy(self, processor):
        text = "当前价格：10.00，趋势良好"
        result = processor._smart_price_estimation(text, "买入", is_china=True)
        assert result == round(10.00 * 1.15, 2)

    def test_with_current_price_no_percentage_sell(self, processor):
        text = "当前价格：10.00，风险较大"
        result = processor._smart_price_estimation(text, "卖出", is_china=True)
        assert result == round(10.00 * 0.95, 2)

    def test_with_current_price_hold(self, processor):
        text = "当前价格：10.00"
        result = processor._smart_price_estimation(text, "持有", is_china=True)
        assert result == 10.00

    def test_no_price_info(self, processor):
        text = "市场波动较大"
        result = processor._smart_price_estimation(text, "持有", is_china=True)
        assert result is None

    def test_us_stock_multiplier(self, processor):
        text = "当前价格：100.00"
        result = processor._smart_price_estimation(text, "买入", is_china=False)
        assert result == round(100.00 * 1.12, 2)


# ── process_signal — JSON 解析路径 ──────────────────────────────────

class TestProcessSignalJsonPath:

    def test_valid_json_response(self, processor):
        """LLM 返回合法 JSON 时正确提取。"""
        decision_json = json.dumps({
            "action": "买入",
            "target_price": 45.50,
            "confidence": 0.8,
            "risk_score": 0.3,
            "reasoning": "基本面良好"
        })
        processor.quick_thinking_llm.invoke.return_value = MagicMock(content=decision_json)

        result = processor.process_signal("分析报告...", "000001")
        assert result["action"] == "买入"
        assert result["target_price"] == 45.50
        assert result["confidence"] == 0.8
        assert result["risk_score"] == 0.3

    def test_action_mapping_english_to_chinese(self, processor):
        """LLM 返回英文 action 时自动映射。"""
        decision_json = json.dumps({
            "action": "buy",
            "target_price": 50,
            "confidence": 0.7,
            "risk_score": 0.4,
            "reasoning": "看好"
        })
        processor.quick_thinking_llm.invoke.return_value = MagicMock(content=decision_json)

        result = processor.process_signal("分析报告...", "000001")
        assert result["action"] == "买入"

    @pytest.mark.parametrize("eng,cn", [
        ("buy", "买入"), ("sell", "卖出"), ("hold", "持有"),
        ("overweight", "增持"), ("underweight", "减持"),
        ("购买", "买入"), ("出售", "卖出"), ("加仓", "增持"), ("减仓", "减持"),
    ])
    def test_all_action_mappings(self, processor, eng, cn):
        decision_json = json.dumps({
            "action": eng, "target_price": 10, "confidence": 0.5, "risk_score": 0.5, "reasoning": "测试"
        })
        processor.quick_thinking_llm.invoke.return_value = MagicMock(content=decision_json)
        result = processor.process_signal("报告", "000001")
        assert result["action"] == cn


# ── _get_default_decision ───────────────────────────────────────────

class TestGetDefaultDecision:

    def test_default_values(self, processor):
        result = processor._get_default_decision()
        assert result["action"] == "持有"
        assert result["target_price"] is None
        assert result["confidence"] == 0.5
        assert result["risk_score"] == 0.5
        assert "默认" in result["reasoning"]


# ── process_signal — 货币感知 ──────────────────────────────────────

class TestProcessSignalCurrencyAwareness:

    def test_us_stock_currency(self, processor):
        """美股使用美元。"""
        decision_json = json.dumps({
            "action": "买入", "target_price": 190, "confidence": 0.7, "risk_score": 0.3, "reasoning": "看好"
        })
        processor.quick_thinking_llm.invoke.return_value = MagicMock(content=decision_json)

        # 验证 LLM 被调用时 system prompt 包含美元
        processor.process_signal("分析...", "AAPL")
        call_args = processor.quick_thinking_llm.invoke.call_args[0][0]
        system_msg = call_args[0][1]
        assert "美元" in system_msg
        assert "$" in system_msg

    def test_china_stock_currency(self, processor):
        """A股使用人民币。"""
        decision_json = json.dumps({
            "action": "买入", "target_price": 45, "confidence": 0.7, "risk_score": 0.3, "reasoning": "看好"
        })
        processor.quick_thinking_llm.invoke.return_value = MagicMock(content=decision_json)

        processor.process_signal("分析...", "000001")
        call_args = processor.quick_thinking_llm.invoke.call_args[0][0]
        system_msg = call_args[0][1]
        assert "人民币" in system_msg
        assert "¥" in system_msg
