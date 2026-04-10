import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://admin:tradingagents123@localhost:27017/?authSource=admin")
    db = client['tradingagents']
    system_config = await db['system_configs'].find_one({'is_active': True})
    
    if not system_config:
        print("No active system_config found")
        return
        
    llm_configs = system_config.get('llm_configs', [])
    updated = False
    
    for model in llm_configs:
        if model.get('model_name') == 'kimi-k2.5':
            model['provider'] = 'dashscope'
            model['api_base'] = ''
            print("✅ 成功修改 kimi-k2.5 供应商为 dashscope 并重置了 api_base")
            updated = True
            
    if updated:
        await db['system_configs'].update_one(
            {'_id': system_config['_id']},
            {
                '$set': {
                    'llm_configs': llm_configs,
                    'version': system_config.get('version', 0) + 1
                }
            }
        )
        print("✅ 数据库更新成功")
    else:
        print("⚠️ 未找到名为 kimi-k2.5 的模型配置")
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
