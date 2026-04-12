"""
市场分析师 - 图级别工具循环模式
与 fundamentals_analyst.py 保持一致的模式：
- 首次调用：LLM 返回 tool_calls → 图路由到 tools_market → ToolNode 执行
- 二次进入：LLM 看到工具结果 → 生成报告
- 降级路径：LLM 不调工具时手动执行 + 生成报告
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, ToolMessage

from tradingagents.utils.tool_logging import log_analyst_module
from tradingagents.utils.logging_init import get_logger
from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler
from tradingagents.agents.analysts._common import (
    has_tool_results,
    get_tool_call_count,
    force_generate_report,
    force_tool_call_and_report,
)

logger = get_logger("default")


def _get_company_name(ticker: str, market_info: dict) -> str:
    """根据股票代码获取公司名称。"""
    try:
        if market_info['is_china']:
            from tradingagents.dataflows.interface import get_china_stock_info_unified
            stock_info = get_china_stock_info_unified(ticker)
            if stock_info and "股票名称:" in stock_info:
                company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                logger.info(f"✅ [市场分析师] 获取股票名称: {ticker} -> {company_name}")
                return company_name
            else:
                logger.warning(f"⚠️ [市场分析师] 无法解析股票名称: {ticker}，尝试降级")
                try:
                    from tradingagents.dataflows.data_source_manager import get_china_stock_info_unified as get_info_dict
                    info_dict = get_info_dict(ticker)
                    if info_dict and info_dict.get('name'):
                        return info_dict['name']
                except Exception as e:
                    logger.error(f"❌ [市场分析师] 降级方案失败: {e}")
                return f"股票代码{ticker}"

        elif market_info['is_hk']:
            try:
                from tradingagents.dataflows.providers.hk.improved_hk import get_hk_company_name_improved
                return get_hk_company_name_improved(ticker)
            except Exception:
                clean_ticker = ticker.replace('.HK', '').replace('.hk', '')
                return f"港股{clean_ticker}"

        elif market_info['is_us']:
            us_stock_names = {
                'AAPL': '苹果公司', 'TSLA': '特斯拉', 'NVDA': '英伟达',
                'MSFT': '微软', 'GOOGL': '谷歌', 'AMZN': '亚马逊',
                'META': 'Meta', 'NFLX': '奈飞'
            }
            return us_stock_names.get(ticker.upper(), f"美股{ticker}")

        else:
            return f"股票{ticker}"

    except Exception as e:
        logger.error(f"❌ [市场分析师] 获取公司名称失败: {e}")
        return f"股票{ticker}"


def create_market_analyst(llm, toolkit):

    @log_analyst_module("market")
    def market_analyst_node(state):
        logger.debug(f"📈 [市场分析师] ===== 节点开始 =====")

        # 工具调用计数（防无限循环）
        tool_call_count = get_tool_call_count(state, "market_tool_call_count")
        max_tool_calls = 3
        messages = state.get("messages", [])

        logger.info(f"🔧 [市场分析师] 工具调用计数: {tool_call_count}/{max_tool_calls}")
        logger.info(f"🔧 [市场分析师] 消息数量: {len(messages)}, 已有工具结果: {has_tool_results(messages)}")

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # 获取市场信息
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(ticker)
        company_name = _get_company_name(ticker, market_info)

        logger.info(f"📈 [市场分析师] 分析: {company_name}({ticker}), 市场: {market_info['market_name']}")

        # 绑定工具
        tools = [toolkit.get_stock_market_data_unified]

        # 构建 prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "你是一位专业的股票技术分析师，与其他分析师协作。\n"
             "\n"
             "📋 **分析对象：**\n"
             "- 公司名称：{company_name}\n"
             "- 股票代码：{ticker}\n"
             "- 所属市场：{market_name}\n"
             "- 计价货币：{currency_name}（{currency_symbol}）\n"
             "- 分析日期：{current_date}\n"
             "\n"
             "🔧 **工具使用：**\n"
             "你可以使用以下工具：{tool_names}\n"
             "⚠️ 重要工作流程：\n"
             "1. 如果消息历史中没有工具结果，立即调用 get_stock_market_data_unified 工具\n"
             "   - ticker: {ticker}\n"
             "   - start_date: {current_date}\n"
             "   - end_date: {current_date}\n"
             "   注意：系统会自动扩展到365天历史数据，你只需要传递当前分析日期即可\n"
             "2. 如果消息历史中已经有工具结果（ToolMessage），立即基于工具数据生成最终分析报告\n"
             "3. 不要重复调用工具！一次工具调用就足够了！\n"
             "4. 接收到工具数据后，必须立即生成完整的技术分析报告，不要再调用任何工具\n"
             "\n"
             "📝 **输出格式要求（必须严格遵守）：**\n"
             "\n"
             "## 📊 股票基本信息\n"
             "- 公司名称：{company_name}\n"
             "- 股票代码：{ticker}\n"
             "- 所属市场：{market_name}\n"
             "- 分析日期：{current_date}\n"
             "\n"
             "## 📈 技术指标分析\n"
             "[在这里分析移动平均线、MACD、RSI、布林带等技术指标，提供具体数值]\n"
             "\n"
             "## 📉 价格趋势分析\n"
             "[在这里分析价格趋势，考虑{market_name}市场特点]\n"
             "\n"
             "## 💰 资金流向分析\n"
             "[在这里分析主力资金、大单/中单/小单资金流向情况]\n"
             "\n"
             "## 📊 估值分析\n"
             "[在这里分析PE、PB、股息率等估值指标，判断是否被低估或高估]\n"
             "\n"
             "## 💭 投资建议\n"
             "[在这里给出明确的投资建议：买入/持有/卖出]\n"
             "\n"
             "⚠️ **重要提醒：**\n"
             "- 必须使用上述格式输出，不要自创标题格式\n"
             "- 所有价格数据使用{currency_name}（{currency_symbol}）表示\n"
             "- 确保在分析中正确使用公司名称\"{company_name}\"和股票代码\"{ticker}\"\n"
             "- 不要在标题中使用\"技术分析报告\"等自创标题\n"
             "- 如果你有明确的技术面投资建议（买入/持有/卖出），请在投资建议部分明确标注\n"
             "- 不要使用'最终交易建议'前缀，因为最终决策需要综合所有分析师的意见\n"
             "\n"
             "请使用中文，基于真实数据进行分析。"),
            MessagesPlaceholder(variable_name="messages"),
        ])

        tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in tools]
        prompt = prompt.partial(
            tool_names=", ".join(tool_names),
            current_date=current_date,
            ticker=ticker,
            company_name=company_name,
            market_name=market_info['market_name'],
            currency_name=market_info['currency_name'],
            currency_symbol=market_info['currency_symbol'],
        )

        # 检测阿里百炼模型并创建新实例
        if hasattr(llm, '__class__') and 'DashScope' in llm.__class__.__name__:
            from tradingagents.llm_adapters import ChatDashScopeOpenAI
            fresh_llm = ChatDashScopeOpenAI(
                model=llm.model_name,
                api_key=getattr(llm, 'openai_api_key', None),
                base_url=getattr(llm, 'openai_api_base', None),
                temperature=llm.temperature,
                max_tokens=getattr(llm, 'max_tokens', 2000)
            )
        else:
            fresh_llm = llm

        # Google 模型特殊处理
        if GoogleToolCallHandler.is_google_model(fresh_llm):
            logger.info(f"📈 [市场分析师] 检测到Google模型，使用统一工具调用处理器")
            chain = prompt | fresh_llm.bind_tools(tools)
            result = chain.invoke({"messages": state["messages"]})

            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker, company_name=company_name, analyst_type="市场分析",
                specific_requirements="重点关注市场数据、价格走势、交易量变化等市场指标。"
            )
            report, _ = GoogleToolCallHandler.handle_google_tool_calls(
                result=result, llm=fresh_llm, tools=tools, state=state,
                analysis_prompt_template=analysis_prompt_template, analyst_name="市场分析师"
            )
            return {
                "messages": [result],
                "market_report": report,
                "market_tool_call_count": tool_call_count,
            }

        # 标准模型处理
        chain = prompt | fresh_llm.bind_tools(tools)
        logger.info(f"📈 [市场分析师] 调用LLM...")
        result = chain.invoke({"messages": state["messages"]})
        logger.info(f"📈 [市场分析师] LLM调用完成, tool_calls={len(result.tool_calls) if hasattr(result, 'tool_calls') else 0}")

        # ── 分支处理 ──────────────────────────────────────────────────

        if len(result.tool_calls) > 0:
            # LLM 返回了 tool_calls
            if has_tool_results(messages):
                # 已有工具结果但仍调工具 → 强制生成报告
                logger.warning(f"⚠️ [市场分析师] 已有工具结果但LLM仍调工具，强制生成报告")
                report = force_generate_report(
                    fresh_llm, messages, company_name, ticker, market_info, "市场分析"
                )
                return {
                    "messages": [result],
                    "market_report": report,
                    "market_tool_call_count": tool_call_count,
                }

            if tool_call_count >= max_tool_calls:
                # 达到上限 → 强制生成报告
                logger.warning(f"⚠️ [市场分析师] 达到工具调用上限({tool_call_count}/{max_tool_calls})，强制生成报告")
                report = force_generate_report(
                    fresh_llm, messages, company_name, ticker, market_info, "市场分析"
                )
                return {
                    "messages": [result],
                    "market_report": report,
                    "market_tool_call_count": tool_call_count,
                }

            # 正常首次调用 → 返回 tool_calls，让图路由到 tools_market
            logger.info(f"✅ [市场分析师] 正常工具调用，返回等待工具执行")
            return {
                "messages": [result],
                "market_tool_call_count": tool_call_count,
            }

        else:
            # LLM 没有调工具
            if has_tool_results(messages):
                # 有工具结果 + LLM 生成文本 → 这就是报告
                report = result.content
                if len(report) < 200:
                    logger.warning(f"⚠️ [市场分析师] 报告过短({len(report)}字符)，强制重新生成")
                    report = force_generate_report(
                        fresh_llm, messages, company_name, ticker, market_info, "市场分析"
                    )
                logger.info(f"✅ [市场分析师] 报告生成完成，长度: {len(report)}")
                return {
                    "messages": [result],
                    "market_report": report,
                    "market_tool_call_count": tool_call_count,
                }

            # 完全没有工具结果 → LLM 不调工具的降级
            logger.warning(f"⚠️ [市场分析师] LLM未调用工具，启动降级: 手动执行工具 + 生成报告")
            report = force_tool_call_and_report(
                fresh_llm, tools, ticker, company_name, market_info,
                "市场分析",
                {"ticker": ticker, "start_date": current_date, "end_date": current_date},
            )
            return {
                "messages": [AIMessage(content=report)],
                "market_report": report,
                "market_tool_call_count": tool_call_count,
            }

    return market_analyst_node
