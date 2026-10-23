# -*- coding: utf-8 -*-
import os
import re
import zhconv

# ================= 配置区 =================
EN_FILE = "en_metalprocessitemlist.txt"
TW_FILE = "tw_metalprocessitemlist.txt"
# 依然保留对多个简中碎片的兼容
CN_FILES = ["cn_metalprocessitemlist.txt", "cn_metalprocessitemlist .txt"]
OUT_FILE = "metalprocessitemlist.txt"
# ==========================================

def read_content_robust(filepath):
    """自适应编码读取文件，带防爆破双重容错机制"""
    if not os.path.exists(filepath):
        print(f"⚠️ 未找到文件: {filepath} (将跳过)")
        return ""
    
    strict_encodings = ['utf-8', 'utf-8-sig', 'gbk', 'big5hkscs', 'big5', 'cp950', 'utf-16le']
    for enc in strict_encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue

    fallback_encodings = ['cp950', 'big5hkscs', 'utf-8', 'gbk']
    for enc in fallback_encodings:
        try:
            with open(filepath, 'r', encoding=enc, errors='ignore') as f:
                return f.read()
        except Exception:
            continue
            
    print(f"❌ 无法读取 {filepath}，所有编码尝试均失败！")
    return ""

def parse_txt_to_blocks(filepath):
    """
    将文件解析为多行区块字典
    核心机制：解决同一种物品有多种配方（重复 ID）的覆盖问题
    """
    content = read_content_robust(filepath)
    if not content:
        return {}
        
    data_dict = {}
    id_counts = {} # 记录某个ID出现了几次
    
    current_id = None
    unique_id = None
    current_lines = []
    
    for line in content.splitlines():
        stripped = line.strip()
        
        # 匹配区块头部，例如: 998#
        match = re.match(r'^(\d+)#$', stripped)
        if match:
            current_id = match.group(1)
            # 生成带序号的唯一ID，如: 998_0, 12118_1
            count = id_counts.get(current_id, 0)
            unique_id = f"{current_id}_{count}"
            id_counts[current_id] = count + 1
            
            current_lines = []
        
        # 匹配区块尾部
        elif stripped == "#" and current_id is not None:
            data_dict[unique_id] = current_lines
            current_id = None
            unique_id = None
            
        # 记录区块中间的配方材料
        elif current_id is not None:
            current_lines.append(line)
            
    return data_dict

def merge_metal_process():
    print("="*60)
    print(" 🛠️ RO 客户端合成配方表 (MetalProcess) 三合一合并器 ".center(56, " "))
    print("="*60)

    # 1. 读取并合并简中文件
    cn_dict = {}
    print("⏳ 正在解析简体中文数据...")
    for cn_file in CN_FILES:
        temp_dict = parse_txt_to_blocks(cn_file)
        if temp_dict:
            cn_dict.update(temp_dict)
            print(f"  ✅ 成功加载: {cn_file} ({len(temp_dict)} 个配方区块)")

    # 2. 读取繁体文件
    print("⏳ 正在解析繁体中文数据...")
    tw_dict = parse_txt_to_blocks(TW_FILE)
    if tw_dict:
        print(f"  ✅ 成功加载: {TW_FILE} ({len(tw_dict)} 个配方区块)")

    # 3. 读取英文基础架构
    print("⏳ 正在读取英文基础架构...")
    en_content = read_content_robust(EN_FILE)
    if not en_content:
        print("❌ 英文源文件为空或解析失败，无法构建基础骨架！")
        return

    print("-" * 60)
    
    merged_lines = []
    stats = {"cn": 0, "tw_to_cn": 0, "en": 0, "total": 0}
    
    current_id = None
    unique_id = None
    en_buffer = []
    en_id_counts = {}
    
    # 4. 遍历英文骨架进行注入替换
    for line in en_content.splitlines():
        stripped = line.strip()
        
        match = re.match(r'^(\d+)#$', stripped)
        if match:
            # 遇到新配方头
            current_id = match.group(1)
            count = en_id_counts.get(current_id, 0)
            unique_id = f"{current_id}_{count}"
            en_id_counts[current_id] = count + 1
            
            merged_lines.append(line)
            en_buffer = []
            
        elif stripped == "#" and current_id is not None:
            # 遇到配方尾部，开始决定注入什么内容
            stats["total"] += 1
            
            if unique_id in cn_dict:
                # 命中简中
                merged_lines.extend(cn_dict[unique_id])
                stats["cn"] += 1
            elif unique_id in tw_dict:
                # 命中繁体，转换简中
                tw_lines = tw_dict[unique_id]
                converted_lines = [zhconv.convert(l, 'zh-cn') for l in tw_lines]
                merged_lines.extend(converted_lines)
                stats["tw_to_cn"] += 1
            else:
                # 英文兜底
                merged_lines.extend(en_buffer)
                stats["en"] += 1
                
            merged_lines.append(line) # 加上结尾的 #
            current_id = None
            unique_id = None
            
        elif current_id is not None:
            # 区块内容缓冲
            en_buffer.append(line)
        else:
            # 区块外的空行或注释，直接保留
            merged_lines.append(line)

    # 5. 强制 GBK 输出
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write("\n".join(merged_lines))
        
    print("=" * 60)
    print("🎉 合并完成！统计报告：")
    print(f"  🔹 总配方数: {stats['total']}")
    print(f"  ✅ 完美命中简中 (CN): {stats['cn']}")
    print(f"  🔄 繁体自动转简体 (TW->CN): {stats['tw_to_cn']}")
    print(f"  ⚠️ 无翻译保留英文 (EN): {stats['en']}")
    print(f"\n📄 最终文件已生成: {OUT_FILE} (GBK 编码)")
    print("=" * 60)

if __name__ == "__main__":
    merge_metal_process()