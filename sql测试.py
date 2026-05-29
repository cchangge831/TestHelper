import csv
import random

# 合并两张图片中的列名（自动去重，保持顺序）
columns = [
    "日均店内拜访时长计算辅助列", "区域乡镇路线日均店内拜访时长...", 
    "区域乡镇路线店内拜访时长(小时)", "区域乡镇路线计划拜访客户数", 
    "445月", "计划拜访客户数", "区域乡镇路线计划内拜访", 
    "区域乡镇路线拜访成功", "年", "店内拜访时长(小时)", 
    "拜访成功", "计划内拜访", "区域乡镇路线日均店内拜访时长（小时）", 
    "区域乡镇路线店内拜访客户数", "装瓶厂"
]

# 定义每列的数据类型
col_data_types = {
    "日均店内拜访时长计算辅助列": "数值",
    "区域乡镇路线日均店内拜访时长...": "数值",
    "区域乡镇路线店内拜访时长(小时)": "数值",
    "区域乡镇路线计划拜访客户数": "数值",
    "445月": "文本",
    "计划拜访客户数": "数值",
    "区域乡镇路线计划内拜访": "数值",
    "区域乡镇路线拜访成功": "数值",
    "年": "文本",
    "店内拜访时长(小时)": "数值",
    "拜访成功": "数值",
    "计划内拜访": "数值",
    "区域乡镇路线日均店内拜访时长（小时）": "数值",
    "区域乡镇路线店内拜访客户数": "数值",
    "装瓶厂": "文本"
}

# 生成符合数据类型约束的随机值函数
def generate_value(col_name, data_type):
    if data_type == "数值":
        # 根据字段语义生成合理的数值范围
        if "拜访时长" in col_name:
            # 拜访时长：0.5 到 24 小时之间，保留1位小数
            return round(random.uniform(0.5, 24.0), 1)
        elif "拜访客户数" in col_name or "计划拜访客户数" in col_name:
            # 客户数：1 到 100 之间
            return random.randint(1, 100)
        elif "计划内拜访" in col_name or "拜访成功" in col_name:
            # 拜访次数：0 到 50 之间
            return random.randint(0, 50)
        elif "计算辅助列" in col_name:
            # 辅助列：0 到 1000 之间
            return random.randint(0, 1000)
        else:
            # 其他数值：0 到 100 之间
            return random.randint(0, 100)
    else:  # 文本类型
        # 根据列名生成合理的文本示例
        if col_name == "445月":
            # 格式如：2024-05
            return f"202{random.randint(0,5)}-{random.randint(1,12):02d}"
        elif col_name == "年":
            return str(random.randint(2020, 2026))
        elif col_name == "装瓶厂":
            return random.choice(["北京厂", "上海厂", "广州厂", "成都厂", "武汉厂", "沈阳厂", "西安厂"])
        else:
            # 其他文本字段生成通用值
            return f"{col_name[:10]}_{random.randint(1,999)}"

# 生成10行数据
rows = []
for i in range(10):
    row = []
    for col in columns:
        data_type = col_data_types.get(col, "数值")  # 默认为数值类型
        value = generate_value(col, data_type)
        row.append(value)
    rows.append(row)

# 写入CSV文件
with open('starrocks_css_visit_data.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(columns)  # 写入列头
    writer.writerows(rows)    # 写入数据行

print(f"CSV文件 'starrocks_css_visit_data.csv' 已生成，包含 {len(columns)} 列和 10 行数据。")
print(f"总列数: {len(columns)}")
print(f"列名: {', '.join(columns)}")

# 可选：打印前几行预览
print("\n数据预览（前3行）:")
with open('starrocks_css_visit_data.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader):
        if i <= 3:  # 打印表头和前3行数据
            if i == 0:
                print(f"表头: {row}")
            else:
                print(f"第{i}行: {row}")
        else:
            break