import csv
import random
from datetime import datetime, timedelta

# 定义列名及其数据类型（根据图片内容，去除重复列）
columns = {
    "t": "数值",
    "d": "文本",
    "指标类型": "文本",
    "qty_day": "数值",
    "type": "文本",
    "产品名称-报表端展示": "文本"
}

# 生成10行数据
data = []
for _ in range(10):
    row = {}
    
    # t: 数值（示例：时间戳或序号）
    row["t"] = random.randint(1, 1000)
    
    # d: 文本（示例：日期字符串）
    start_date = datetime(2023, 1, 1)
    random_days = random.randint(0, 365*2)
    row["d"] = (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")
    
    # 指标类型: 文本（从几个常见指标中选取）
    indicators = ["销售额", "销量", "订单量", "客流量", "转化率"]
    row["指标类型"] = random.choice(indicators)
    
    # qty_day: 数值（示例：0到10000之间的整数）
    row["qty_day"] = random.randint(0, 10000)
    
    # type: 文本（示例：类别）
    types = ["A类", "B类", "C类", "旗舰款", "普通款"]
    row["type"] = random.choice(types)
    
    # 产品名称-报表端展示: 文本（示例：产品名）
    product_names = ["智能手表Pro", "无线耳机X3", "便携充电宝", "高清摄像头Lite", "蓝牙音箱Max"]
    row["产品名称-报表端展示"] = random.choice(product_names)
    
    data.append(row)

# 写入CSV文件
filename = "订单与零售趋势图打榜_目标柱状图.csv"
with open(filename, mode='w', newline='', encoding='utf-8-sig') as file:
    writer = csv.DictWriter(file, fieldnames=columns.keys())
    writer.writeheader()
    writer.writerows(data)

print(f"文件 '{filename}' 已生成，共 {len(data)} 行数据。")