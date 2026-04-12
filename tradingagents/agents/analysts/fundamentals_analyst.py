"""
基本面分析师 - 统一工具架构版本（图级别工具循环模式）

与 Market 分析师保持一致的模式：
- 首次调用：LLM 返回 tool_calls → 图路由到 tools_fundamentals → ToolNode 执行
- 二次进入：LLM 看到工具结果 → 生成报告
- 降级路径：LLM 不调工具时手动执行 + 生成报告
"""

from datetime import datetime, timedelta

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


def _get_company_name_for_fundamentals(ticker: str, market_info: dict) -> str:
    """为基本面分析师获取公司名称。"""
    try:
        if market_info['is_china']:
            from tradingagents.dataflows.interface import get_china_stock_info_unified
            stock_info = get_china_stock_info_unified(ticker)
            if stock_info and "股票名称:" in stock_info:
                company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                logger.info(f"✅ [基本面分析师] 成功获取中国股票名称: {ticker} -> {company_name}")
                return company_name
            else:
                logger.warning(f"⚠️ [基本面分析师] 无法解析股票名称: {ticker}，尝试降级")
                try:
                    from tradingagents.dataflows.data_source_manager import get_china_stock_info_unified as get_info_dict
                    info_dict = get_info_dict(ticker)
                    if info_dict and info_dict.get('name'):
                        return info_dict['name']
                except Exception as e:
                    logger.error(f"❌ [基本面分析师] 降级方案失败: {e}")
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
        logger.error(f"❌ [基本面分析师] 获取公司名称失败: {e}")
        return f"股票{ticker}"


def create_fundamentals_analyst(llm, toolkit):

    @log_analyst_module("fundamentals")
    def fundamentals_analyst_node(state):
        logger.debug(f"📊 [基本面分析师] ===== 节点开始 =====")

        # 工具调用计数（防无限循环）
        tool_call_count = get_tool_call_count(state, "fundamentals_tool_call_count")
        max_tool_calls = 1  # 一次工具调用就能获取所有数据
        messages = state.get("messages", [])

        logger.info(f"🔧 [基本面分析师] 工具调用计数: {tool_call_count}/{max_tool_calls}")
        logger.info(f"🔧 [基本面分析师] 消息数量: {len(messages)}, 已有工具结果: {has_tool_results(messages)}")

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # 基本面分析数据范围：固定获取10天数据
        try:
            end_date_dt = datetime.strptime(current_date, "%Y-%m-%d")
            start_date_dt = end_date_dt - timedelta(days=10)
            start_date = start_date_dt.strftime("%Y-%m-%d")
            logger.info(f"📅 [基本面分析师] 数据范围: {start_date} 至 {current_date} (固定10天)")
        except Exception as e:
            logger.warning(f"⚠️ [基本面分析师] 日期解析失败: {e}")
            start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

        # 获取市场信息
        from tradingagents.utils.stock_utils import StockUtils
        logger.info(f"📊 [基本面分析师] 正在分析股票: {ticker}")

        logger.info(f"🔍 [股票代码追踪] 基本面分析师接收到的原始股票代码: '{ticker}' (类型: {type(ticker)})")

        market_info = StockUtils.get_market_info(ticker)
        company_name = _get_company_name_for_fundamentals(ticker, market_info)

        logger.info(f"📊 [基本面分析师] 使用统一基本面分析工具，自动识别股票类型")

        # 绑定工具
        tools = [toolkit.get_stock_fundamentals_unified]

        tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in tools]
        logger.info(f"📊 [基本面分析师] 绑定的工具: {tool_names}")
        logger.info(f"📊 [基本面分析师] 目标市场: {market_info['market_name']}")

        # 构建 prompt — 与原版保持一致
        system_message = (
            f"你是一位专业的股票基本面分析师。"
            f"⚠️ 绝对强制要求：你必须调用工具获取真实数据！不允许任何假设或编造！"
            f"任务：分析{company_name}（股票代码：{ticker}，{market_info['market_name']}）"
            f"🔴 立即调用 get_stock_fundamentals_unified 工具"
            f"参数：ticker='{ticker}', start_date='{start_date}', end_date='{current_date}', curr_date='{current_date}'"
            "📊 分析要求："
            "- 基于真实数据进行深度基本面分析"
            f"- 计算并提供合理价位区间（使用{market_info['currency_name']}{market_info['currency_symbol']}）"
            "- 分析当前股价是否被低估或高估"
            "- 提供基于基本面的目标价位建议"
            "- 包含PE、PB、PEG等估值指标分析"
            "- 结合市场特点进行分析"
            "🌍 语言和货币要求："
            "- 所有分析内容必须使用中文"
            "- 投资建议必须使用中文：买入、持有、卖出"
            "- 绝对不允许使用英文：buy、hold、sell"
            f"- 货币单位使用：{market_info['currency_name']}（{market_info['currency_symbol']}）"
            "🚫 严格禁止："
            "- 不允许说'我将调用工具'"
            "- 不允许假设任何数据"
            "- 不允许编造公司信息"
            "- 不允许直接回答而不调用工具"
            "- 不允许回复'无法确定价位'或'需要更多信息'"
            "- 不允许使用英文投资建议（buy/hold/sell）"
            "✅ 你必须："
            "- 立即调用统一基本面分析工具"
            "- 等待工具返回真实数据"
            "- 基于真实数据进行分析"
            "- 提供具体的价位区间和目标价"
            "- 使用中文投资建议（买入/持有/卖出）"
            "现在立即开始调用工具！不要说任何其他话！"
        )

        system_prompt = (
            "🔴 强制要求：你必须调用工具获取真实数据！"
            "🚫 绝对禁止：不允许假设、编造或直接回答任何问题！"
            "✅ 工作流程："
            "1. 【第一次调用】如果消息历史中没有工具结果（ToolMessage），立即调用 get_stock_fundamentals_unified 工具"
            "2. 【收到数据后】如果消息历史中已经有工具结果（ToolMessage），🚨 绝对禁止再次调用工具！🚨"
            "3. 【生成报告】收到工具数据后，必须立即生成完整的基本面分析报告，包含："
            "   - 公司基本信息和财务数据分析"
            "   - PE、PB、PEG等估值指标分析"
            "   - 当前股价是否被低估或高估的判断"
            "   - 合理价位区间和目标价位建议"
            "   - 基于基本面的投资建议（买入/持有/卖出）"
            "4. 🚨 重要：工具只需调用一次！一次调用返回所有需要的数据！不要重复调用！🚨"
            "5. 🚨 如果你已经看到ToolMessage，说明工具已经返回数据，直接生成报告，不要再调用工具！🚨"
            "可用工具：{tool_names}。\n{system_message}"
            "当前日期：{current_date}。"
            "分析目标：{company_name}（股票代码：{ticker}）。"
            "请确保在分析中正确区分公司名称和股票代码。"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])

        prompt = prompt.partial(
            system_message=system_message,
            tool_names=", ".join(tool_names),
            current_date=current_date,
            ticker=ticker,
            company_name=company_name,
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
            logger.info(f"📊 [基本面分析师] 检测到Google模型，使用统一工具调用处理器")
            chain = prompt | fresh_llm.bind_tools(tools)
            result = chain.invoke({"messages": state["messages"]})

            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker, company_name=company_name, analyst_type="基本面分析",
                specific_requirements="重点关注财务数据、盈利能力、估值指标、行业地位等基本面因素。"
            )
            report, _ = GoogleToolCallHandler.handle_google_tool_calls(
                result=result, llm=fresh_llm, tools=tools, state=state,
                analysis_prompt_template=analysis_prompt_template, analyst_name="基本面分析师"
            )
            return {"fundamentals_report": report}

        # 标准模型处理
        chain = prompt | fresh_llm.bind_tools(tools)
        logger.info(f"📊 [基本面分析师] 开始调用LLM...")
        result = chain.invoke({"messages": state["messages"]})
        logger.info(f"📊 [基本面分析师] LLM调用完成")

        # ── 分支处理 ──────────────────────────────────────────────────

        if len(result.tool_calls) > 0:
            # LLM 返回了 tool_calls
            if has_tool_results(messages):
                # 已有工具结果但仍调工具 → 强制生成报告
                logger.warning(f"⚠️ [基本面分析师] 已有工具结果但LLM仍调工具，强制生成报告")
                report = force_generate_report(
                    fresh_llm, messages, company_name, ticker, market_info, "基本面分析"
                )
                return {
                    "messages": [result],
                    "fundamentals_report": report,
                    "fundamentals_tool_call_count": tool_call_count,
                }

            if tool_call_count >= max_tool_calls:
                # 达到上限 → 强制生成报告
                logger.warning(f"⚠️ [基本面分析师] 达到工具调用上限({tool_call_count}/{max_tool_calls})，强制生成报告")
                report = force_generate_report(
                    fresh_llm, messages, company_name, ticker, market_info, "基本面分析"
                )
                return {
                    "messages": [result],
                    "fundamentals_report": report,
                    "fundamentals_tool_call_count": tool_call_count,
                }

            # 正常首次调用 → 返回 tool_calls，让图路由到 tools_fundamentals
            logger.info(f"✅ [基本面分析师] 正常工具调用，返回等待工具执行")
            return {
                "messages": [result],
            }

        else:
            # LLM 没有调工具
            if has_tool_results(messages):
                # 有工具结果 + LLM 生成文本 → 这就是报告
                report = result.content
                if len(report) < 500:
                    logger.warning(f"⚠️ [基本面分析师] 报告过短({len(report)}字符)，强制重新生成")
                    report = force_generate_report(
                        fresh_llm, messages, company_name, ticker, market_info, "基本面分析"
                    )
                logger.info(f"✅ [基本面分析师] 报告生成完成，长度: {len(report)}")
                return {
                    "messages": [result],
                    "fundamentals_report": report,
                    "fundamentals_tool_call_count": tool_call_count,
                }

            # 完全没有工具结果 → LLM 不调工具的降级
            logger.warning(f"⚠️ [基本面分析师] LLM未调用工具，启动降级: 手动执行工具 + 生成报告")
            report = force_tool_call_and_report(
                fresh_llm, tools, ticker, company_name, market_info,
                "基本面分析",
                {"ticker": ticker, "start_date": start_date, "end_date": current_date, "curr_date": current_date},
            )
            return {
                "messages": [AIMessage(content=report)],
                "fundamentals_report": report,
                "fundamentals_tool_call_count": tool_call_count,
            }

    return fundamentals_analyst_node
