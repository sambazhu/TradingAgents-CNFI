import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://admin:tradingagents123@localhost:27017/?authSource=admin")
    db = client['tradingagents']
    
    # 获取最新的一条分析任务
    task = await db['analysis_tasks'].find().sort('created_at', -1).limit(1).to_list(1)
    if not task:
        print("未找到分析任务")
        return
        
    task = task[0]
    print(f"✅ 最新分析任务 ID: {task['_id']}")
    print(f"✅ 状态: {task.get('status')}")
    print(f"✅ 分析股票: {task.get('config', {}).get('symbol')} {task.get('config', {}).get('stock_name')}")
    print("\n---------- 分析报告摘要 (前 2000 字) ----------\n")
    
    # 读取最终内容
    content = task.get('final_content', '')
    if not content and 'steps' in task:
        for s in reversed(task['steps']):
            if s.get('status') == 'completed' and s.get('result'):
                content = s['result']
                print(f"(从步骤 {s.get('name')} 中提取的内容)")
                break
                
    if content:
        print(content[:2000])
        if len(content) > 2000:
            print(f"\n... (内容过长，共 {len(content)} 字，已截断)")
    else:
        print("内容为空")

if __name__ == "__main__":
    asyncio.run(main())
