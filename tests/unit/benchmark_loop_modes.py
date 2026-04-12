"""
对比测试：图级别循环 vs 节点内闭环 的执行耗时

测试方法：
- 用 mock LLM 模拟真实延迟（默认 100ms/次）
- 用 mock 工具模拟数据获取（默认 50ms/次）
- 跑 N 轮取平均值
- 对比纯框架开销（0ms 延迟）和 模拟真实延迟两种场景

运行：./venv/bin/python -m pytest tests/unit/benchmark_loop_modes.py -v -s
"""

import time
import statistics
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END, START, MessagesState
from typing import Annotated
from typing_extensions import TypedDict


# ── 配置 ────────────────────────────────────────────────────────────

LLM_DELAY_MS = 0.100       # 每次 LLM 调用模拟 100ms
TOOL_DELAY_MS = 0.050       # 每次工具调用模拟 50ms
ROUNDS = 20                 # 每个场景跑 20 轮取均值


# ── Mock 工厂 ───────────────────────────────────────────────────────

def make_mock_llm(response_with_tools=True, delay=LLM_DELAY_MS):
    """创建 mock LLM。

    第1次调用：返回带 tool_calls 的 AIMessage
    第2次调用：返回纯文本报告（无 tool_calls）
    """
    call_count = [0]

    def invoke(messages, **kwargs):
        time.sleep(delay)
        call_count[0] += 1
        if response_with_tools and call_count[0] == 1:
            return AIMessage(
                content="",
                tool_calls=[{"name": "get_data", "args": {"ticker": "000001"}, "id": "tc_1"}],
            )
        else:
            return AIMessage(content="这是一份详细的分析报告。" * 30)

    mock = MagicMock()
    mock.invoke = invoke
    mock.bind_tools = MagicMock(return_value=mock)
    return mock


def make_mock_tool(delay=TOOL_DELAY_MS):
    """创建 mock 工具函数。"""
    def tool_func(**kwargs):
        time.sleep(delay)
        return "股票数据: 开盘价10.5, 收盘价10.8, 最高价11.0, 最低价10.3"

    tool_func.name = "get_data"
    return tool_func


# ── 模式 A：图级别循环（上游原版模式）─────────────────────────────────

class AnalystState(MessagesState):
    report: Annotated[str, "Analysis report"]
    tool_call_count: Annotated[int, "Tool call counter"]


def create_graph_level_graph(llm_delay=LLM_DELAY_MS, tool_delay=TOOL_DELAY_MS):
    """构建图级别循环的分析师图。"""

    llm = make_mock_llm(delay=llm_delay)
    tool = make_mock_tool(delay=tool_delay)

    def analyst_node(state):
        result = llm.invoke(state["messages"])
        report = ""
        if not result.tool_calls:
            report = result.content
        return {"messages": [result], "report": report}

    def tools_node(state):
        last = state["messages"][-1]
        results = []
        for tc in last.tool_calls:
            data = tool(**tc["args"])
            results.append(ToolMessage(content=str(data), tool_call_id=tc["id"]))
        return {"messages": results}

    def should_continue(state):
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "end"

    graph = StateGraph(AnalystState)
    graph.add_node("analyst", analyst_node)
    graph.add_node("tools", tools_node)
    graph.add_edge(START, "analyst")
    graph.add_conditional_edges("analyst", should_continue, {"tools": "tools", "end": END})
    graph.add_edge("tools", "analyst")
    return graph.compile()


# ── 模式 B：节点内闭环（CN 版 Market/News/Social 模式）────────────────

def create_node_internal_graph(llm_delay=LLM_DELAY_MS, tool_delay=TOOL_DELAY_MS):
    """构建节点内闭环的分析师图。"""

    llm = make_mock_llm(delay=llm_delay)
    tool = make_mock_tool(delay=tool_delay)

    def analyst_node(state):
        # 第1次 LLM 调用
        result = llm.invoke(state["messages"])

        if result.tool_calls:
            # 节点内执行工具
            tool_results = []
            for tc in result.tool_calls:
                data = tool(**tc["args"])
                tool_results.append(ToolMessage(content=str(data), tool_call_id=tc["id"]))

            # 第2次 LLM 调用，生成报告
            messages = state["messages"] + [result] + tool_results
            final = llm.invoke(messages)
            report = final.content
            clean_msg = AIMessage(content=report)
        else:
            report = result.content
            clean_msg = result

        return {"messages": [clean_msg], "report": report}

    graph = StateGraph(AnalystState)
    graph.add_node("analyst", analyst_node)
    graph.add_edge(START, "analyst")
    graph.add_edge("analyst", END)
    return graph.compile()


# ── 基准测试 ────────────────────────────────────────────────────────

class TestBenchmark:

    def _run_benchmark(self, graph, label, rounds=ROUNDS):
        """运行 N 轮并打印统计。"""
        times = []
        initial_state = {
            "messages": [HumanMessage(content="分析 000001")],
            "report": "",
            "tool_call_count": 0,
        }

        for i in range(rounds):
            start = time.perf_counter()
            result = graph.invoke(initial_state)
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        avg = statistics.mean(times)
        med = statistics.median(times)
        std = statistics.stdev(times) if len(times) > 1 else 0
        mn = min(times)
        mx = max(times)

        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}")
        print(f"  轮次: {rounds}")
        print(f"  平均: {avg*1000:.1f} ms")
        print(f"  中位: {med*1000:.1f} ms")
        print(f"  最小: {mn*1000:.1f} ms")
        print(f"  最大: {mx*1000:.1f} ms")
        print(f"  标准差: {std*1000:.1f} ms")
        print(f"{'='*60}")

        return {"avg": avg, "med": med, "min": mn, "max": mx, "label": label}

    def test_with_simulated_latency(self):
        """模拟真实延迟：LLM 100ms + 工具 50ms。"""
        print("\n" + "="*60)
        print("  场景：模拟真实延迟 (LLM=100ms, Tool=50ms)")
        print("  预期：两种模式 LLM 调用次数相同（2次），耗时应接近")
        print("="*60)

        g_graph = create_graph_level_graph(llm_delay=0.100, tool_delay=0.050)
        g_node = create_node_internal_graph(llm_delay=0.100, tool_delay=0.050)

        r1 = self._run_benchmark(g_graph, "图级别循环 (模拟延迟)", ROUNDS)
        r2 = self._run_benchmark(g_node, "节点内闭环 (模拟延迟)", ROUNDS)

        diff_pct = (r1["avg"] - r2["avg"]) / r2["avg"] * 100
        print(f"\n  差异: 图级别比节点内闭环 {'慢' if diff_pct > 0 else '快'} {abs(diff_pct):.1f}%")
        print(f"  绝对差: {abs(r1['avg'] - r2['avg'])*1000:.1f} ms")

    def test_pure_framework_overhead(self):
        """纯框架开销：LLM 和工具延迟为 0。"""
        print("\n" + "="*60)
        print("  场景：纯框架开销 (LLM=0ms, Tool=0ms)")
        print("  预期：图级别循环因多次状态转移会有额外开销")
        print("="*60)

        g_graph = create_graph_level_graph(llm_delay=0, tool_delay=0)
        g_node = create_node_internal_graph(llm_delay=0, tool_delay=0)

        r1 = self._run_benchmark(g_graph, "图级别循环 (纯开销)", ROUNDS)
        r2 = self._run_benchmark(g_node, "节点内闭环 (纯开销)", ROUNDS)

        diff_pct = (r1["avg"] - r2["avg"]) / r2["avg"] * 100 if r2["avg"] > 0 else 0
        print(f"\n  差异: 图级别比节点内闭环 {'慢' if diff_pct > 0 else '快'} {abs(diff_pct):.1f}%")
        print(f"  绝对差: {abs(r1['avg'] - r2['avg'])*1000:.1f} ms")

    def test_multi_tool_calls(self):
        """多次工具调用场景：Market 分析师可能调用 get_data + get_indicators。"""
        print("\n" + "="*60)
        print("  场景：多次工具调用 (2个工具)")
        print("="*60)

        # 构建会调 2 次工具的 mock
        def make_multi_tool_llm(delay=LLM_DELAY_MS):
            call_count = [0]
            mock = MagicMock()
            def invoke(messages, **kwargs):
                time.sleep(delay)
                call_count[0] += 1
                if call_count[0] == 1:
                    return AIMessage(content="", tool_calls=[
                        {"name": "get_data", "args": {"ticker": "000001"}, "id": "tc_1"},
                        {"name": "get_indicators", "args": {"ticker": "000001"}, "id": "tc_2"},
                    ])
                else:
                    return AIMessage(content="完整技术分析报告。" * 30)
            mock.invoke = invoke
            mock.bind_tools = MagicMock(return_value=mock)
            return mock

        tool = make_mock_tool()

        # 图级别
        def analyst_graph_node(state):
            llm = make_multi_tool_llm()
            result = llm.invoke(state["messages"])
            report = "" if result.tool_calls else result.content
            return {"messages": [result], "report": report}

        def tools_graph_node(state):
            last = state["messages"][-1]
            results = []
            for tc in last.tool_calls:
                data = tool(**tc["args"])
                results.append(ToolMessage(content=str(data), tool_call_id=tc["id"]))
            return {"messages": results}

        def should_continue(state):
            last = state["messages"][-1]
            if hasattr(last, "tool_calls") and last.tool_calls:
                return "tools"
            return "end"

        g = StateGraph(AnalystState)
        g.add_node("analyst", analyst_graph_node)
        g.add_node("tools", tools_graph_node)
        g.add_edge(START, "analyst")
        g.add_conditional_edges("analyst", should_continue, {"tools": "tools", "end": END})
        g.add_edge("tools", "analyst")
        graph_compiled = g.compile()

        # 节点内
        def analyst_node_internal(state):
            llm = make_multi_tool_llm()
            result = llm.invoke(state["messages"])
            if result.tool_calls:
                tool_results = []
                for tc in result.tool_calls:
                    data = tool(**tc["args"])
                    tool_results.append(ToolMessage(content=str(data), tool_call_id=tc["id"]))
                messages = state["messages"] + [result] + tool_results
                final = llm.invoke(messages)
                report = final.content
            else:
                report = result.content
            return {"messages": [AIMessage(content=report)], "report": report}

        g2 = StateGraph(AnalystState)
        g2.add_node("analyst", analyst_node_internal)
        g2.add_edge(START, "analyst")
        g2.add_edge("analyst", END)
        node_compiled = g2.compile()

        r1 = self._run_benchmark(graph_compiled, "图级别循环 (2工具)", ROUNDS)
        r2 = self._run_benchmark(node_compiled, "节点内闭环 (2工具)", ROUNDS)

        diff_pct = (r1["avg"] - r2["avg"]) / r2["avg"] * 100 if r2["avg"] > 0 else 0
        print(f"\n  差异: 图级别比节点内闭环 {'慢' if diff_pct > 0 else '快'} {abs(diff_pct):.1f}%")
