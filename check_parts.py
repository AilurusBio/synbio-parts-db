from pymongo import MongoClient

# 连接数据库
client = MongoClient("mongodb://localhost:27017/")
db = client.synbio_db

# 查询不同类型的元件
pipeline = [
    {
        "$group": {
            "_id": "$type_info.main_type",
            "count": {"$sum": 1},
            "sub_types": {"$addToSet": "$type_info.sub_types"}
        }
    }
]

print("元件类型统计:")
for result in db.parts.aggregate(pipeline):
    print(f"\n类型: {result['_id']}")
    print(f"数量: {result['count']}")
    print(f"子类型: {result['sub_types']}")

# 查询一些示例元件
print("\n示例元件:")
for part in db.parts.find().limit(5):
    print(f"\nID: {part.get('_id')}")
    print(f"类型: {part.get('type_info', {}).get('main_type')}")
    print(f"名称: {part.get('name')}")
    print(f"描述: {part.get('description')}") 