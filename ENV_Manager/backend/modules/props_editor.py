"""
properties 文件编辑器 — 提供键值对的增删改查功能。
支持修改前自动备份为 .bak 文件。
"""
import os
import shutil


def read_props(file_path: str) -> dict:
    """
    读取 properties 文件，返回有序键值对字典。
    跳过空行和 # 开头的注释行。
    """
    props = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                props[key.strip()] = value.strip()
    return props


def write_props(file_path: str, props: dict) -> None:
    """
    将键值对写回 properties 文件。
    写前先备份为 .bak。
    """
    # 备份原文件
    backup_path = file_path + ".bak"
    try:
        shutil.copy2(file_path, backup_path)
    except FileNotFoundError:
        pass  # 首次创建无备份正常

    # 写新内容
    with open(file_path, "w", encoding="utf-8") as f:
        for key, value in props.items():
            f.write(f"{key}={value}\n")


def update_prop(file_path: str, key: str, value: str) -> dict:
    """
    更新单个键值对。若 key 不存在则新增。
    返回操作前和操作后的完整键值对用于前端回显。
    """
    props = read_props(file_path)
    old_value = props.get(key)
    props[key] = value
    write_props(file_path, props)
    return {"key": key, "old_value": old_value, "new_value": value}


def delete_prop(file_path: str, key: str) -> dict:
    """
    删除指定键值对。
    返回被删除的 key 和旧值。
    """
    props = read_props(file_path)
    old_value = props.pop(key, None)
    if old_value is not None:
        write_props(file_path, props)
    return {"key": key, "deleted_value": old_value}


def write_props_batch(file_path: str, new_props: dict) -> dict:
    """
    批量保存全部键值对（全量覆盖）。
    备份一次，然后写入所有内容。
    返回写入的键值对数量。
    """
    # 仅备份一次
    backup_path = file_path + ".bak"
    try:
        shutil.copy2(file_path, backup_path)
    except FileNotFoundError:
        pass

    with open(file_path, "w", encoding="utf-8") as f:
        for key, value in new_props.items():
            f.write(f"{key}={value}\n")

    return {"count": len(new_props), "backup": os.path.basename(backup_path)}
