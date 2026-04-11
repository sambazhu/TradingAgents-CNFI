"""ConditionalLogic 单元测试 — 图路由条件判断。"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from conftest import MockAIMessage, make_mock_state
from tradingagents.graph.conditional_logic import ConditionalLogic


@pytest.fixture
def logic():
    return ConditionalLogic(max_debate_rounds=1, max_risk_discuss_rounds=1)


# ── should_continue_market ──────────────────────────────────────────

class TestShouldContinueMarket:

    def test_has_tool_calls(self, logic):
        msg = MockAIMessage(content="", tool_calls=[{"name": "get_stock_data"}])
        state = make_mock_state(messages=[msg])
        assert logic.should_continue_market(state) == "tools_market"

    def test_no_tool_calls(self, logic):
        msg = MockAIMessage(content="分析完成", tool_calls=[])
        state = make_mock_state(messages=[msg])
        assert logic.should_continue_market(state) == "Msg Clear Market"

    def test_max_tool_calls_reached(self, logic):
        msg = MockAIMessage(content="", tool_calls=[{"name": "get_stock_data"}])
        state = make_mock_state(messages=[msg], market_tool_call_count=3)
        assert logic.should_continue_market(state) == "Msg Clear Market"

    def test_report_already_exists(self, logic):
        msg = MockAIMessage(content="", tool_calls=[{"name": "get_stock_data"}])
        report = "这是一份非常详细的市场分析报告，包含了各种技术指标和市场趋势分析的内容" * 3
        state = make_mock_state(messages=[msg], market_report=report)
        assert logic.should_continue_market(state) == "Msg Clear Market"

    def test_short_report_still_runs_tools(self, logic):
        msg = MockAIMessage(content="", tool_calls=[{"name": "get_stock_data"}])
        state = make_mock_state(messages=[msg], market_report="短报告")
        assert logic.should_continue_market(state) == "tools_market"


# ── should_continue_social ──────────────────────────────────────────

class TestShouldContinueSocial:

    def test_has_tool_calls(self, logic):
        msg = MockAIMessage(content="", tool_calls=[{"name": "get_sentiment"}])
        state = make_mock_state(messages=[msg])
        assert logic.should_continue_social(state) == "tools_social"

    def test_no_tool_calls(self, logic):
        msg = MockAIMessage(content="完成", tool_calls=[])
        state = make_mock_state(messages=[msg])
        assert logic.should_continue_social(state) == "Msg Clear Social"

    def test_max_tool_calls(self, logic):
        msg = MockAIMessage(content="", tool_calls=[{"name": "get_sentiment"}])
        state = make_mock_state(messages=[msg], sentiment_tool_call_count=3)
        assert logic.should_continue_social(state) == "Msg Clear Social"


# ── should_continue_news ────────────────────────────────────────────

class TestShouldContinueNews:

    def test_has_tool_calls(self, logic):
        msg = MockAIMessage(content="", tool_calls=[{"name": "get_news"}])
        state = make_mock_state(messages=[msg])
        assert logic.should_continue_news(state) == "tools_news"

    def test_no_tool_calls(self, logic):
        msg = MockAIMessage(content="完成", tool_calls=[])
        state = make_mock_state(messages=[msg])
        assert logic.should_continue_news(state) == "Msg Clear News"

    def test_max_tool_calls(self, logic):
        msg = MockAIMessage(content="", tool_calls=[{"name": "get_news"}])
        state = make_mock_state(messages=[msg], news_tool_call_count=3)
        assert logic.should_continue_news(state) == "Msg Clear News"


# ── should_continue_fundamentals ────────────────────────────────────

class TestShouldContinueFundamentals:

    def test_has_tool_calls(self, logic):
        msg = MockAIMessage(content="", tool_calls=[{"name": "get_fundamentals"}])
        state = make_mock_state(messages=[msg])
        assert logic.should_continue_fundamentals(state) == "tools_fundamentals"

    def test_no_tool_calls(self, logic):
        msg = MockAIMessage(content="完成", tool_calls=[])
        state = make_mock_state(messages=[msg])
        assert logic.should_continue_fundamentals(state) == "Msg Clear Fundamentals"

    def test_max_tool_calls_is_1(self, logic):
        """基本面分析 max_tool_calls=1，一次调用后就强制结束。"""
        msg = MockAIMessage(content="", tool_calls=[{"name": "get_fundamentals"}])
        state = make_mock_state(messages=[msg], fundamentals_tool_call_count=1)
        assert logic.should_continue_fundamentals(state) == "Msg Clear Fundamentals"

    def test_report_already_exists(self, logic):
        msg = MockAIMessage(content="", tool_calls=[{"name": "get_fundamentals"}])
        # 报告长度需 >100 才触发"已完成"判断
        report = "基本面分析报告内容，包含PE、PB、ROE等核心财务指标的详细分析" * 4
        state = make_mock_state(messages=[msg], fundamentals_report=report)
        assert logic.should_continue_fundamentals(state) == "Msg Clear Fundamentals"


# ── should_continue_debate ──────────────────────────────────────────

class TestShouldContinueDebate:

    def test_reached_max(self, logic):
        """max_debate_rounds=1, max_count=2*1=2。"""
        state = make_mock_state(
            investment_debate_state={
                "count": 2,
                "current_response": "Bull analysis...",
                "bull_history": "",
                "bear_history": "",
                "history": "",
                "judge_decision": "",
            }
        )
        assert logic.should_continue_debate(state) == "Research Manager"

    def test_not_reached_max_bull_to_bear(self, logic):
        state = make_mock_state(
            investment_debate_state={
                "count": 0,
                "current_response": "Bull analysis...",
                "bull_history": "",
                "bear_history": "",
                "history": "",
                "judge_decision": "",
            }
        )
        assert logic.should_continue_debate(state) == "Bear Researcher"

    def test_not_reached_max_bear_to_bull(self, logic):
        state = make_mock_state(
            investment_debate_state={
                "count": 1,
                "current_response": "Bear rebuttal...",
                "bull_history": "",
                "bear_history": "",
                "history": "",
                "judge_decision": "",
            }
        )
        assert logic.should_continue_debate(state) == "Bull Researcher"

    def test_higher_debate_rounds(self):
        """max_debate_rounds=2 → max_count=4。"""
        logic2 = ConditionalLogic(max_debate_rounds=2, max_risk_discuss_rounds=1)
        state = make_mock_state(
            investment_debate_state={
                "count": 3,
                "current_response": "Bear...",
                "bull_history": "",
                "bear_history": "",
                "history": "",
                "judge_decision": "",
            }
        )
        assert logic2.should_continue_debate(state) == "Bull Researcher"


# ── should_continue_risk_analysis ───────────────────────────────────

class TestShouldContinueRiskAnalysis:

    def test_reached_max(self, logic):
        """max_risk_discuss_rounds=1, max_count=3*1=3。"""
        state = make_mock_state(
            risk_debate_state={
                "count": 3,
                "latest_speaker": "Risky Analyst",
                "risky_history": "",
                "safe_history": "",
                "neutral_history": "",
                "history": "",
                "current_risky_response": "",
                "current_safe_response": "",
                "current_neutral_response": "",
                "judge_decision": "",
            }
        )
        assert logic.should_continue_risk_analysis(state) == "Risk Judge"

    def test_risky_to_safe(self, logic):
        state = make_mock_state(
            risk_debate_state={
                "count": 0,
                "latest_speaker": "Risky Analyst",
                "risky_history": "",
                "safe_history": "",
                "neutral_history": "",
                "history": "",
                "current_risky_response": "",
                "current_safe_response": "",
                "current_neutral_response": "",
                "judge_decision": "",
            }
        )
        assert logic.should_continue_risk_analysis(state) == "Safe Analyst"

    def test_safe_to_neutral(self, logic):
        state = make_mock_state(
            risk_debate_state={
                "count": 1,
                "latest_speaker": "Safe Analyst",
                "risky_history": "",
                "safe_history": "",
                "neutral_history": "",
                "history": "",
                "current_risky_response": "",
                "current_safe_response": "",
                "current_neutral_response": "",
                "judge_decision": "",
            }
        )
        assert logic.should_continue_risk_analysis(state) == "Neutral Analyst"

    def test_neutral_to_risky(self, logic):
        state = make_mock_state(
            risk_debate_state={
                "count": 2,
                "latest_speaker": "Neutral Analyst",
                "risky_history": "",
                "safe_history": "",
                "neutral_history": "",
                "history": "",
                "current_risky_response": "",
                "current_safe_response": "",
                "current_neutral_response": "",
                "judge_decision": "",
            }
        )
        assert logic.should_continue_risk_analysis(state) == "Risky Analyst"
