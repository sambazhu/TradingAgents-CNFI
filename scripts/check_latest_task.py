import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://admin:tradingagents123@localhost:27017/?authSource=admin")
    db = client['tradingagents']
    
    # 获取最近5条任务
    tasks = await db['analysis_tasks'].find().sort('created_at', -1).limit(5).to_list(5)
    
    for i, task in enumerate(tasks):
        print(f"[{i+1}] 任务ID: {task.get('_id')} | 状态: {task.get('status')} | 股票: {task.get('config', {}).get('symbol')} {task.get('config', {}).get('stock_name')}")
        if task.get('status') == 'completed':
            print(f"    --> (已完成) 最终内容长度: {len(task.get('final_content', ''))}")
            if len(task.get('final_content', '')) > 0 and i == 0:
                print("    [内容片段]:", task.get('final_content', '')[:500])
        else:
            steps = task.get('steps', [])
            print(f"    --> (未完成) 步骤进度: {len([s for s in steps if s.get('status') == 'completed'])} / {len(steps)}")
            
if __name__ == "__main__":
    asyncio.run(main())
