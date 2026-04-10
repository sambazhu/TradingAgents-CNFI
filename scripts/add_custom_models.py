import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://admin:tradingagents123@localhost:27017/?authSource=admin")
    db = client['tradingagents']
    
    # 查找活动的配置
    system_config = await db['system_configs'].find_one({'is_active': True})
    if not system_config:
        system_config = await db['system_configs'].find_one({})
        
    if not system_config:
        print("未找到任何系统配置")
        return
        
    llm_configs = system_config.get('llm_configs', [])
    
    # 定义要添加的新模型
    new_models = [
        {
            "provider": "dashscope",
            "model_name": "qwen3.6-plus",
            "model_display_name": "qwen3.6-plus",
            "api_key": "",
            "api_base": "",
            "max_tokens": 8000,
            "temperature": 0.7,
            "timeout": 120,
            "retry_times": 3,
            "enabled": True,
            "description": "User requested qwen3.6-plus",
            "model_category": "",
            "custom_endpoint": None,
            "enable_memory": False,
            "enable_debug": False,
            "priority": 1,
            "input_price_per_1k": 0.001,
            "output_price_per_1k": 0.002,
            "currency": "CNY",
            "capability_level": 4,
            "suitable_roles": ["both"],
            "features": ["tool_calling", "long_context"],
            "recommended_depths": ["标准", "深度"],
            "performance_metrics": {"speed": 3, "cost": 3, "quality": 3}
        },
        {
            "provider": "moonshot",
            "model_name": "kimi-k2.5",
            "model_display_name": "kimi-k2.5",
            "api_key": "",
            "api_base": "https://api.moonshot.cn/v1",
            "max_tokens": 8000,
            "temperature": 0.7,
            "timeout": 120,
            "retry_times": 3,
            "enabled": True,
            "description": "User requested kimi-k2.5",
            "model_category": "",
            "custom_endpoint": None,
            "enable_memory": False,
            "enable_debug": False,
            "priority": 1,
            "input_price_per_1k": 0.001,
            "output_price_per_1k": 0.002,
            "currency": "CNY",
            "capability_level": 4,
            "suitable_roles": ["both"],
            "features": ["tool_calling", "long_context"],
            "recommended_depths": ["标准", "深度"],
            "performance_metrics": {"speed": 3, "cost": 3, "quality": 3}
        }
    ]
    
    # 检查是否已存在
    existing_model_names = [m.get('model_name') for m in llm_configs]
    
    added_count = 0
    for model in new_models:
        if model['model_name'] not in existing_model_names:
            llm_configs.append(model)
            added_count += 1
            print(f"✅ 加入新模型: {model['model_name']}")
        else:
            print(f"⚠️ 模型已存在: {model['model_name']}")
            
    if added_count > 0:
        result = await db['system_configs'].update_one(
            {'_id': system_config['_id']},
            {
                '$set': {
                    'llm_configs': llm_configs,
                    'version': system_config.get('version', 0) + 1
                }
            }
        )
        print(f"数据更新完成, 添加了 {added_count} 个模型, 版本升级至 {system_config.get('version', 0) + 1}")
    else:
        print("没有新模型需要添加")

    client.close()

if __name__ == "__main__":
    asyncio.run(main())
