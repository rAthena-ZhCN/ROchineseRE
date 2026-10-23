# -*- coding: utf-8 -*-
import os
import re
import zhconv
import bson  # 依赖 pymongo 库中的 bson

# ================= 配置区 =================
# 配置需要处理的文件组：(英文文件, 繁体文件, [简体文件列表], 输出文件名)
TASK_LIST = [
    (
        "en_reputegroupdata.bson", 
        "tw_reputegroupdata.bson", 
        ["cn_reputegroupdata.bson"], 
        "reputegroupdata.bson"
    ),
    (
        "en_reputeinfodata.bson", 
        "tw_reputeinfodata.bson", 
        ["cn_reputeinfodata.bson"], 
        "reputeinfodata.bson"
    )
]
# ==========================================

def load_bson(filepath):
    """读取并解码 BSON 文件"""
    if not os.path.exists(filepath):
        print(f"⚠️ 未找到文件: {filepath}")
        return []
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
            # BSON 文件可能包含多个连续的 Document
            return bson.decode_all(data)
    except Exception as e:
        print(f"❌ 无法解析 BSON 文件 {filepath}: {e}")
        return []

def save_bson(filepath, docs):
    """将字典重新编码为 BSON 并保存"""
    with open(filepath, 'wb') as f:
        for doc in docs:
            f.write(bson.encode(doc))

def has_chinese(text):
    """检测字符串中是否包含中文字符"""
    return bool(re.search(r'[\u4e00-\u9fa5]', text))

def build_path_dict(data, current_path="", paths=None):
    """
    将 BSON 嵌套结构拍扁，生成 {路径: 文本} 的字典。
    例如: {"reputeInfo": {"1": {"Name": "兽人部落"}}} 
    变成 -> {"/reputeInfo/1/Name": "兽人部落"}
    """
    if paths is None:
        paths = {}
        
    if isinstance(data, dict):
        for k, v in data.items():
            path = f"{current_path}/{k}"
            build_path_dict(v, path, paths)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            path = f"{current_path}[{i}]"
            build_path_dict(v, path, paths)
    elif isinstance(data, str):
        paths[current_path] = data
        
    return paths

def merge_bson_task(en_file, tw_file, cn_files, out_file):
    print("-" * 60)
    print(f"🚀 开始处理: {out_file}")
    
    # 1. 加载文件
    en_docs = load_bson(en_file)
    if not en_docs:
        print("❌ 英文骨架加载失败，跳过。")
        return
        
    tw_docs = load_bson(tw_file)
    
    cn_docs = []
    for cn_f in cn_files:
        docs = load_bson(cn_f)
        if docs:
            cn_docs.extend(docs)

    # 2. 建立中文和繁体路径字典
    cn_paths = build_path_dict(cn_docs)
    tw_paths = build_path_dict(tw_docs)
    
    stats = {"cn": 0, "tw_to_cn": 0, "en": 0}

    # 3. 递归遍历英文骨架，进行精准注入
    def traverse_and_replace(data, current_path=""):
        if isinstance(data, dict):
            for k, v in data.items():
                path = f"{current_path}/{k}"
                if isinstance(v, str):
                    cn_str = cn_paths.get(path, "")
                    tw_str = tw_paths.get(path, "")
                    
                    # 只有当提取到的文本包含中文时，才进行替换 (保护英文ID不被破坏)
                    if cn_str and has_chinese(cn_str):
                        data[k] = cn_str
                        stats["cn"] += 1
                    elif tw_str and has_chinese(tw_str):
                        data[k] = zhconv.convert(tw_str, 'zh-cn')
                        stats["tw_to_cn"] += 1
                    else:
                        stats["en"] += 1
                else:
                    traverse_and_replace(v, path)
                    
        elif isinstance(data, list):
            for i, v in enumerate(data):
                path = f"{current_path}[{i}]"
                if isinstance(v, str):
                    cn_str = cn_paths.get(path, "")
                    tw_str = tw_paths.get(path, "")
                    
                    if cn_str and has_chinese(cn_str):
                        data[i] = cn_str
                        stats["cn"] += 1
                    elif tw_str and has_chinese(tw_str):
                        data[i] = zhconv.convert(tw_str, 'zh-cn')
                        stats["tw_to_cn"] += 1
                    else:
                        stats["en"] += 1
                else:
                    traverse_and_replace(v, path)

    traverse_and_replace(en_docs)

    # 4. 保存为全新 BSON
    save_bson(out_file, en_docs)
    
    print(f"🎉 成功生成: {out_file}")
    print(f"  ✅ 完美命中简中 (CN): {stats['cn']} 处")
    print(f"  🔄 繁体转简体抢救 (TW->CN): {stats['tw_to_cn']} 处")
    print(f"  ⚠️ 无翻译保留英文 (EN): {stats['en']} 处")

def main():
    print("="*60)
    print(" 🗃️ RO 客户端 BSON 二进制数据通用合并器 ".center(56, " "))
    print("="*60)
    for task in TASK_LIST:
        merge_bson_task(*task)
    print("="*60)

if __name__ == "__main__":
    main()