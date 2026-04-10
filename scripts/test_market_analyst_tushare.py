import os
import sys
import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 强制注入配置，只认 Tushare 通道
os.environ["DEFAULT_CHINA_DATA_SOURCE"] = "tushare"
os.environ["TUSHARE_FALLBACK_TO_AKSHARE"] = "false" # 建议强制Tushare失败时不回退，直接拉取报错以便暴露问题

# 设置工程搜索路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from tradingagents.agents.analysts.market_analyst import create_market_analyst
from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.utils.logging_init import get_logger

# 针对LangChain可以开启详细日志抓包看它的Tool调用（可选注释掉以保持静默）
# set_debug(True) 

logger = get_logger("test_market_analyst")

def main():
    print("\n" + "="*50)
    print("🚀 [孤立环境测试] 市场分析师 (A股 + Tushare 通道直连)")
    print("="*50)

    # 1. 创建用于推理的大语言模型（兼容模式）
    print("🤖 正在连接 DashScope 大模型引擎 (qwen-plus)...")
    llm = ChatOpenAI(
        model="qwen-plus", 
        api_key=os.environ.get("DASHSCOPE_API_KEY", "your-api-key"), 
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    # 2. 组装工具箱 (包含 get_stock_market_data_unified)
    config = {
        "research_depth": "基础", # 轻量级获取减少Token消耗
        "llm_provider": "dashscope", 
        "online_tools": True
    }
    toolkit = Toolkit(config=config)

    # 3. 实例化纯净版的 Market Analyst
    print("👨‍💼 正在实例化市场分析师 (Market Analyst)...")
    market_node = create_market_analyst(llm, toolkit)

    # 4. 构造虚拟系统状态流
    ticker = "000001"
    prompt_text = (
        f"你是一名专业的技术系统市场分析师。"
        f"请立即调用你手里的 'get_stock_market_data_unified' 工具获取这只股票的量价数据和指标。"
        f"获取数据后，请直接反馈简短的市场评述，不用废话。"
    )
    
    mock_state = {
        "messages": [HumanMessage(content=prompt_text)],
        "company_of_interest": ticker,
        "trade_date": "2024-05-01",  # 可以填今日日期，作为测试无妨
        "stock_name": "平安银行"
    }

    # 5. 引爆黑盒运行
    print(f"🔄 正在下发分析指令，分析标的：{ticker} (由于请求Tushare网络接口，请耐心等待大约20秒)...")
    
    try:
        response = market_node(mock_state)  # 原生函数调用，不需要ainvoke
        
        # 解析返回的所有消息链
        messages = response.get("messages", [])
        
        # 寻找大模型最后的返回
        final_answer = messages[-1].content
        
        print("\n\n" + "="*50)
        print("✅ [大模型研判] 分析大报告输出：")
        print("="*50)
        print(final_answer)
        print("="*50 + "\n")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ [执行异常] {e}")

if __name__ == "__main__":
    main()
