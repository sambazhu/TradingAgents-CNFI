import os
import sys
import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置工程搜索路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from tradingagents.agents.analysts.market_analyst import create_market_analyst
from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.utils.logging_init import get_logger

logger = get_logger("test_market_analyst_us")

def main():
    print("\n" + "="*50)
    print("🚀 [孤立环境测试] 市场分析师 (美股通道直连)")
    print("="*50)

    print("🤖 正在连接 DashScope 大模型引擎 (qwen-plus)...")
    llm = ChatOpenAI(
        model="qwen-plus", 
        api_key=os.environ.get("DASHSCOPE_API_KEY", "your-api-key"), 
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    config = {
        "research_depth": "基础",
        "llm_provider": "dashscope", 
        "online_tools": True
    }
    toolkit = Toolkit(config=config)

    print("👨‍💼 正在实例化市场分析师 (Market Analyst)...")
    market_node = create_market_analyst(llm, toolkit)

    ticker = "TSLA"
    prompt_text = (
        f"你是一名专业的技术系统市场分析师。"
        f"请立即调用你手里的 'get_stock_market_data_unified' 工具获取这只股票的量价数据和指标。"
        f"获取数据后，请直接反馈简短的市场评述，不用废话。"
    )
    
    mock_state = {
        "messages": [HumanMessage(content=prompt_text)],
        "company_of_interest": ticker,
        "trade_date": "2024-05-01",  # 用于锚定获取
        "stock_name": "特斯拉"
    }

    print(f"🔄 正在下发分析指令，分析标的：{ticker} (预计需要10-20秒)...")
    
    try:
        response = market_node(mock_state) 
        
        messages = response.get("messages", [])
        final_answer = messages[-1].content
        
        print("\n\n" + "="*50)
        print("✅ [大模型研判] 美股分析大报告输出：")
        print("="*50)
        print(final_answer)
        print("="*50 + "\n")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ [执行异常] {e}")

if __name__ == "__main__":
    main()
