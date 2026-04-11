"""DEFAULT_CONFIG 单元测试 — 默认配置结构与类型。"""

import pytest
from tradingagents.default_config import DEFAULT_CONFIG


class TestDefaultConfigKeys:

    EXPECTED_KEYS = [
        "project_dir", "results_dir", "data_dir", "data_cache_dir",
        "llm_provider", "deep_think_llm", "quick_think_llm", "backend_url",
        "output_language", "max_debate_rounds", "max_risk_discuss_rounds",
        "max_recur_limit", "online_tools", "online_news", "realtime_data",
        "gildata_enabled",
    ]

    def test_all_expected_keys_present(self):
        for key in self.EXPECTED_KEYS:
            assert key in DEFAULT_CONFIG, f"Missing key: {key}"


class TestDefaultConfigTypes:

    def test_llm_provider_is_str(self):
        assert isinstance(DEFAULT_CONFIG["llm_provider"], str)

    def test_deep_think_llm_is_str(self):
        assert isinstance(DEFAULT_CONFIG["deep_think_llm"], str)

    def test_quick_think_llm_is_str(self):
        assert isinstance(DEFAULT_CONFIG["quick_think_llm"], str)

    def test_backend_url_is_str(self):
        assert isinstance(DEFAULT_CONFIG["backend_url"], str)

    def test_max_debate_rounds_is_int(self):
        assert isinstance(DEFAULT_CONFIG["max_debate_rounds"], int)

    def test_max_risk_discuss_rounds_is_int(self):
        assert isinstance(DEFAULT_CONFIG["max_risk_discuss_rounds"], int)

    def test_max_recur_limit_is_int(self):
        assert isinstance(DEFAULT_CONFIG["max_recur_limit"], int)

    def test_gildata_enabled_is_bool(self):
        assert isinstance(DEFAULT_CONFIG["gildata_enabled"], bool)

    def test_online_tools_is_bool(self):
        assert isinstance(DEFAULT_CONFIG["online_tools"], bool)

    def test_online_news_is_bool(self):
        assert isinstance(DEFAULT_CONFIG["online_news"], bool)

    def test_realtime_data_is_bool(self):
        assert isinstance(DEFAULT_CONFIG["realtime_data"], bool)


class TestDefaultConfigValues:

    def test_output_language_is_chinese(self):
        assert DEFAULT_CONFIG["output_language"] == "中文"

    def test_max_debate_rounds_positive(self):
        assert DEFAULT_CONFIG["max_debate_rounds"] >= 1

    def test_max_risk_discuss_rounds_positive(self):
        assert DEFAULT_CONFIG["max_risk_discuss_rounds"] >= 1

    def test_max_recur_limit_reasonable(self):
        assert DEFAULT_CONFIG["max_recur_limit"] >= 10

    def test_dirs_are_strings(self):
        for key in ("project_dir", "results_dir", "data_dir", "data_cache_dir"):
            assert isinstance(DEFAULT_CONFIG[key], str)
            assert len(DEFAULT_CONFIG[key]) > 0
