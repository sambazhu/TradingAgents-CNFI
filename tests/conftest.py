import os
import sys

# 将项目根目录加入 sys.path，确保 `import tradingagents` 可用
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# --- 通用 fixtures 用于单元测试 ---

class MockAIMessage:
    """轻量 mock，模拟 LangChain AIMessage 的 tool_calls 属性。"""

    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []


class MockHumanMessage:
    """轻量 mock，模拟 LangChain HumanMessage。"""

    def __init__(self, content=""):
        self.content = content


def make_mock_state(messages=None, **kwargs):
    """构造最小 state dict，用于 ConditionalLogic 测试。"""
    if messages is None:
        messages = [MockAIMessage(content="test")]
    state = {"messages": messages}
    state.update(kwargs)
    return state

