"""
分析师公共辅助函数 — 图级别循环模式共用逻辑
"""

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def count_tool_messages(messages) -> int:
    """统计消息历史中的 ToolMessage 数量。"""
    return sum(1 for msg in messages if isinstance(msg, ToolMessage))


def has_tool_results(messages) -> bool:
    """判断是否已有工具执行结果。"""
    return count_tool_messages(messages) > 0


def get_tool_call_count(state, counter_key: str) -> int:
    """从 state 中获取工具调用计数，取 ToolMessage 数量和计数器的较大值。"""
    messages = state.get("messages", [])
    tool_message_count = count_tool_messages(messages)
    stored_count = state.get(counter_key, 0)
    return max(tool_message_count, stored_count)


def force_generate_report(llm, messages, company_name, ticker, market_info, analyst_type):
    """
    当 LLM 不配合（已有工具结果但仍调工具 / 达到上限仍调工具）时，
    不绑定工具，直接要求 LLM 基于消息历史中的数据生成报告。
    """
    currency_info = f"{market_info['currency_name']}（{market_info['currency_symbol']}）"

    force_system_prompt = (
        f"你是专业的股票{analyst_type}分析师。"
        f"你已经收到了股票 {company_name}（代码：{ticker}）的分析数据。"
        f"现在你必须基于这些数据生成完整的{analyst_type}报告！\n\n"
        f"报告必须包含以下内容：\n"
        f"1. 数据概览和关键指标分析\n"
        f"2. 趋势分析和判断\n"
        f"3. 合理价位区间和目标价位建议\n"
        f"4. 基于分析的投资建议（买入/持有/卖出）\n\n"
        f"要求：\n"
        f"- 使用中文撰写报告\n"
        f"- 基于消息历史中的真实数据进行分析\n"
        f"- 价格使用{currency_info}\n"
        f"- 投资建议必须明确（买入/持有/卖出）\n"
        f"- 分析要详细且专业，报告长度不少于800字"
    )

    force_prompt = ChatPromptTemplate.from_messages([
        ("system", force_system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])

    # 不绑定工具，强制 LLM 生成文本
    force_chain = force_prompt | llm

    logger.info(f"🔧 [强制生成报告] {analyst_type} - 使用专门的提示词重新调用LLM...")
    force_result = force_chain.invoke({"messages": messages})

    report = str(force_result.content) if hasattr(force_result, 'content') else f"{analyst_type}分析完成"
    logger.info(f"✅ [强制生成报告] {analyst_type} - 成功生成报告，长度: {len(report)}字符")

    return report


def force_tool_call_and_report(llm, tools, ticker, company_name, market_info,
                                analyst_type, tool_invoke_kwargs):
    """
    当 LLM 完全不调工具时，手动执行工具 + 生成报告。
    用于 LLM 首次调用就不调用工具的降级场景。

    Args:
        llm: LLM 实例
        tools: 工具列表
        ticker: 股票代码
        company_name: 公司名称
        market_info: 市场信息
        analyst_type: 分析师类型（如 "市场分析"）
        tool_invoke_kwargs: 传给工具的参数字典

    Returns:
        str: 生成的报告
    """
    currency_info = f"{market_info['currency_name']}（{market_info['currency_symbol']}）"

    # 手动执行工具
    combined_data = ""
    tool_name = None
    for tool in tools:
        tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', 'unknown')
        try:
            logger.info(f"🔧 [强制工具调用] {analyst_type} - 手动调用工具 {tool_name}")
            combined_data = tool.invoke(tool_invoke_kwargs)
            logger.info(f"✅ [强制工具调用] {analyst_type} - 工具调用成功，数据长度: {len(str(combined_data))}")
            break
        except Exception as e:
            logger.error(f"❌ [强制工具调用] {analyst_type} - 工具 {tool_name} 调用失败: {e}")
            combined_data = f"工具调用失败: {e}"

    # 生成分析报告
    analysis_prompt = (
        f"基于以下真实数据，对{company_name}（股票代码：{ticker}）进行详细的{analyst_type}：\n\n"
        f"{combined_data}\n\n"
        f"请提供：\n"
        f"1. 数据概览和关键指标分析\n"
        f"2. 趋势分析和判断\n"
        f"3. 合理价位区间和目标价位建议（使用{currency_info}）\n"
        f"4. 投资建议（买入/持有/卖出）\n\n"
        f"要求：\n"
        f"- 基于提供的真实数据进行分析\n"
        f"- 正确使用公司名称\"{company_name}\"和股票代码\"{ticker}\"\n"
        f"- 价格使用{currency_info}\n"
        f"- 投资建议使用中文\n"
        f"- 分析要详细且专业，报告长度不少于800字"
    )

    try:
        analysis_chain = ChatPromptTemplate.from_messages([
            ("system", f"你是专业的股票{analyst_type}分析师，基于提供的真实数据进行分析。"),
            ("human", "{analysis_request}")
        ]) | llm

        analysis_result = analysis_chain.invoke({"analysis_request": analysis_prompt})
        report = str(analysis_result.content) if hasattr(analysis_result, 'content') else str(analysis_result)
        logger.info(f"✅ [强制工具调用] {analyst_type} - 报告生成完成，长度: {len(report)}")
    except Exception as e:
        logger.error(f"❌ [强制工具调用] {analyst_type} - 报告生成失败: {e}")
        report = f"{analyst_type}报告生成失败：{e}"

    return report
