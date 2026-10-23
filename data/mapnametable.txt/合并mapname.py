# -*- coding: utf-8 -*-
import os
import re
import zhconv

# ================= 配置区 =================
EN_FILE = "en_mapnametable.txt"
TW_FILE = "tw_mapnametable.txt"
# 兼容可能存在的多个简中文件命名（带空格或不带空格）
CN_FILES = ["cn_mapnametable.txt", "cn_mapnametable .txt"]
OUT_FILE = "mapnametable.txt"
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

def parse_txt_to_dict(filepath):
    """将 txt 文件解析为 {MapFile: MapName} 的字典"""
    content = read_content_robust(filepath)
    if not content:
        return {}
        
    data_dict = {}
    # 🛑 核心修改：匹配格式如 prt_fild01.rsw#Prontera Field#
    pattern = re.compile(r'^([^#]+)#(.*)#\s*$')
    
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('//'):
            continue
            
        match = pattern.match(line)
        if match:
            map_file = match.group(1).strip()
            map_name = match.group(2)
            data_dict[map_file] = map_name
            
    return data_dict

def merge_map_names():
    print("="*60)
    print(" 🗺️ RO 客户端地图名称 (MapName) 三合一合并器 ".center(56, " "))
    print("="*60)

    # 1. 读取并合并简中文件
    cn_dict = {}
    print("⏳ 正在解析简体中文数据...")
    for cn_file in CN_FILES:
        temp_dict = parse_txt_to_dict(cn_file)
        if temp_dict:
            cn_dict.update(temp_dict) # 融合字典，后读取的会覆盖同名ID
            print(f"  ✅ 成功加载: {cn_file} ({len(temp_dict)} 条)")

    # 2. 读取繁体文件
    print("⏳ 正在解析繁体中文数据...")
    tw_dict = parse_txt_to_dict(TW_FILE)
    if tw_dict:
        print(f"  ✅ 成功加载: {TW_FILE} ({len(tw_dict)} 条)")

    # 3. 读取英文基础架构
    print("⏳ 正在读取英文基础架构...")
    en_content = read_content_robust(EN_FILE)
    if not en_content:
        print("❌ 英文源文件为空或解析失败，无法构建基础骨架！")
        return

    print("-" * 60)
    
    merged_lines = []
    stats = {"cn": 0, "tw_to_cn": 0, "en": 0, "total": 0}
    
    # 匹配格式: prt_fild01.rsw#Prontera Field#
    pattern = re.compile(r'^([^#]+)#(.*)#(.*)$')

    # 4. 遍历英文骨架进行注入替换
    for line in en_content.splitlines():
        clean_line = line.strip()
        
        # 保留空行和官方注释
        if not clean_line or clean_line.startswith('//'):
            merged_lines.append(line)
            continue
            
        match = pattern.match(line)
        if match:
            map_file = match.group(1).strip()
            en_name = match.group(2)
            trailing = match.group(3) # 捕获行尾可能存在的空格或其他符号
            
            stats["total"] += 1
            
            if map_file in cn_dict:
                # 命中简中
                cn_name = cn_dict[map_file]
                merged_lines.append(f"{map_file}#{cn_name}#{trailing}")
                stats["cn"] += 1
            elif map_file in tw_dict:
                # 命中繁体，转换简中
                tw_name = tw_dict[map_file]
                cn_name = zhconv.convert(tw_name, 'zh-cn')
                merged_lines.append(f"{map_file}#{cn_name}#{trailing}")
                stats["tw_to_cn"] += 1
            else:
                # 英文兜底
                merged_lines.append(line)
                stats["en"] += 1
        else:
            # 格式不符的异常行，原样保留
            merged_lines.append(line)

    # 5. 强制 GBK 输出
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write("\n".join(merged_lines))
        
    print("=" * 60)
    print("🎉 合并完成！统计报告：")
    print(f"  🔹 总地图数: {stats['total']}")
    print(f"  ✅ 完美命中简中 (CN): {stats['cn']}")
    print(f"  🔄 繁体自动转简体 (TW->CN): {stats['tw_to_cn']}")
    print(f"  ⚠️ 无翻译保留英文 (EN): {stats['en']}")
    print(f"\n📄 最终文件已生成: {OUT_FILE} (GBK 编码)")
    print("=" * 60)

if __name__ == "__main__":
    merge_map_names()