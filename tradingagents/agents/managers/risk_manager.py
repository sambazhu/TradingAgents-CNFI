import time
import json

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
from tradingagents.agents.utils.llm_invocation import (
    invoke_llm_with_retry,
    trim_prompt_text,
)
logger = get_logger("default")


def create_risk_manager(llm, memory):
    def risk_manager_node(state) -> dict:

        company_name = state["company_of_interest"]

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        market_research_report = state["market_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        sentiment_report = state["sentiment_report"]
        trader_plan = state["investment_plan"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"

        # 安全检查：确保memory不为None
        if memory is not None:
            past_memories = memory.get_memories(curr_situation, n_matches=2)
        else:
            logger.warning(f"⚠️ [DEBUG] memory为None，跳过历史记忆检索")
            past_memories = []

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        history_for_prompt = trim_prompt_text(
            history, 15000, label="Risk Manager history", logger=logger
        )
        memory_for_prompt = trim_prompt_text(
            past_memory_str, 4000, label="Risk Manager memory", logger=logger
        )

        prompt = f"""作为风险管理委员会主席和辩论主持人，您的目标是评估三位风险分析师——激进、中性和安全/保守——之间的辩论，并确定交易员的最佳行动方案。力求清晰和果断。

**评级量表**（必须使用以下之一）：
- **买入**: 强烈看好，建议建仓或加仓
- **增持**: 前景看好，逐步增加持仓
- **持有**: 维持当前仓位，暂不操作
- **减持**: 降低持仓，部分止盈
- **卖出**: 清仓或回避入场

决策指导原则：
1. **评级**: 明确给出 买入/增持/持有/减持/卖出 之一。
2. **总结关键论点**：提取每位分析师的最强观点，重点关注与背景的相关性。
3. **提供理由**：用辩论中的直接引用和反驳论点支持您的建议。
4. **完善交易员计划**：从交易员的原始计划**{trader_plan}**开始，根据分析师的见解进行调整。
5. **从过去的错误中学习**：使用**{memory_for_prompt}**中的经验教训来解决先前的误判，改进您现在做出的决策。

交付成果：
1. **评级**: 明确给出 买入/增持/持有/减持/卖出 之一。
2. **执行摘要**: 简洁的行动计划，涵盖入场策略、仓位管理、关键风险水平和时间周期。
3. **投资论点**: 基于辩论和过去反思的详细推理。

---

**分析师辩论历史：**
{history_for_prompt}

---

专注于可操作的见解和持续改进。建立在过去经验教训的基础上，批判性地评估所有观点，确保每个决策都能带来更好的结果。请用中文撰写所有分析内容和建议。"""

        # 📊 统计 prompt 大小
        prompt_length = len(prompt)
        # 粗略估算 token 数量（中文约 1.5-2 字符/token，英文约 4 字符/token）
        estimated_tokens = int(prompt_length / 1.8)  # 保守估计

        logger.info(f"📊 [Risk Manager] Prompt 统计:")
        logger.info(f"   - 辩论历史长度: {len(history)} 字符")
        logger.info(f"   - 交易员计划长度: {len(trader_plan)} 字符")
        logger.info(f"   - 历史记忆长度: {len(past_memory_str)} 字符")
        logger.info(f"   - 总 Prompt 长度: {prompt_length} 字符")
        logger.info(f"   - 估算输入 Token: ~{estimated_tokens} tokens")

        response_content = ""
        try:
            start_time = time.time()
            response = invoke_llm_with_retry(
                llm,
                prompt,
                logger=logger,
                role_name="Risk Manager",
                max_retries=3,
            )
            elapsed_time = time.time() - start_time
            response_content = response.content.strip()

            response_length = len(response_content)
            estimated_output_tokens = int(response_length / 1.8)
            usage_info = ""
            if hasattr(response, 'response_metadata') and response.response_metadata:
                metadata = response.response_metadata
                if 'token_usage' in metadata:
                    token_usage = metadata['token_usage']
                    usage_info = f", 实际Token: 输入={token_usage.get('prompt_tokens', 'N/A')} 输出={token_usage.get('completion_tokens', 'N/A')} 总计={token_usage.get('total_tokens', 'N/A')}"

            logger.info(f"⏱️ [Risk Manager] LLM调用耗时: {elapsed_time:.2f}秒")
            logger.info(f"📊 [Risk Manager] 响应统计: {response_length} 字符, 估算~{estimated_output_tokens} tokens{usage_info}")
            logger.info(f"✅ [Risk Manager] LLM调用成功")
        except Exception as e:
            logger.error(f"❌ [Risk Manager] 多次调用失败，将使用默认决策: {str(e)}")

        # 如果所有重试都失败，生成默认决策
        if not response_content:
            logger.error(f"❌ [Risk Manager] 所有LLM调用尝试失败，使用默认决策")
            response_content = f"""**默认建议：持有**

由于技术原因无法生成详细分析，基于当前市场状况和风险控制原则，建议对{company_name}采取持有策略。

**理由：**
1. 市场信息不足，避免盲目操作
2. 保持现有仓位，等待更明确的市场信号
3. 控制风险，避免在不确定性高的情况下做出激进决策

**建议：**
- 密切关注市场动态和公司基本面变化
- 设置合理的止损和止盈位
- 等待更好的入场或出场时机

注意：此为系统默认建议，建议结合人工分析做出最终决策。"""

        new_risk_debate_state = {
            "judge_decision": response_content,
            "history": risk_debate_state["history"],
            "risky_history": risk_debate_state["risky_history"],
            "safe_history": risk_debate_state["safe_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_risky_response": risk_debate_state["current_risky_response"],
            "current_safe_response": risk_debate_state["current_safe_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        logger.info(f"📋 [Risk Manager] 最终决策生成完成，内容长度: {len(response_content)} 字符")
        
        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": response_content,
        }

    return risk_manager_node
