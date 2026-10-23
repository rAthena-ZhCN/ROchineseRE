# -*- coding: utf-8 -*-
import os
import zhconv

# ================= 配置区 =================
# 请确保这三个文件与本脚本在同一目录下，或者写绝对路径
EN_FILE = "en_OngoingQuests.lua"
CN_FILE = "cn_OngoingQuests.lua"
TW_FILE = "tw_OngoingQuests.lua"
OUT_FILE = "OngoingQuests.lua"
# ==========================================

def read_lua_content(filepath):
    """自适应编码读取 Lua 文件，带防爆破双重容错机制"""
    if not os.path.exists(filepath):
        print(f"⚠️ 未找到文件: {filepath} (将跳过)")
        return ""
    
    # 1. 第一梯队：严格模式（保证字符 100% 完美）
    # 增加了 utf-8-sig(带BOM的UTF-8) 和 cp950(更全的繁体字库)
    strict_encodings = ['utf-8', 'utf-8-sig', 'gbk', 'big5hkscs', 'big5', 'cp950', 'utf-16le']
    for enc in strict_encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
                print(f"  ✅ 成功以 [{enc}] 编码(严格模式)读取 {filepath}")
                return content
        except UnicodeDecodeError:
            continue

    # 2. 第二梯队：容错模式（忽略个别无法识别的坏字节，强行读取）
    # 如果台湾繁体客户端里夹杂了几个非法符号，直接剥离坏字，绝不崩溃
    fallback_encodings = ['cp950', 'big5hkscs', 'utf-8', 'gbk']
    for enc in fallback_encodings:
        try:
            with open(filepath, 'r', encoding=enc, errors='ignore') as f:
                content = f.read()
                print(f"  ⚠️ 成功以 [{enc}] 编码(容错模式)强行读取 {filepath}，已过滤坏字符")
                return content
        except Exception:
            continue
            
    print(f"❌ 无法读取 {filepath}，所有编码尝试均失败！")
    return ""
    
def extract_quests(content):
    """
    智能解析 Lua Table，并包含“反编译残缺字符串”自愈机制
    """
    import re
    quests = {}
    pattern = re.compile(r'\[\s*(\d+)\s*\]\s*=\s*\{')
    
    total_repaired = 0 # 记录修复了多少个残缺字符串

    def repair_broken_string(block_text):
        nonlocal total_repaired
        lines = block_text.split('\n')
        repaired_lines = []
        for line in lines:
            # 计算有效双引号的数量 (排除被转义的 \")
            clean_line = line.replace('\\"', '')
            
            # 如果双引号是奇数个，说明字符串残缺了
            if clean_line.count('"') % 2 != 0:
                original_line = line.rstrip()
                
                # 🛑 【核心升级】：精准切除反编译留下的坏死问号 '?'，并替换为闭合的双引号 '"'
                if original_line.endswith('?,'):
                    line = original_line[:-2] + '",'
                elif original_line.endswith('?}'):
                    line = original_line[:-2] + '"}'
                elif original_line.endswith('?},'):
                    line = original_line[:-3] + '"},'
                elif original_line.endswith('?'):
                    line = original_line[:-1] + '"'
                # 兼容普通缺失的情况（没有问号，单纯是被吃了引号）
                elif original_line.endswith(','):
                    line = original_line[:-1] + '",'
                elif original_line.endswith('}'):
                    line = original_line[:-1] + '"}'
                elif original_line.endswith('},'):
                    line = original_line[:-2] + '"},'
                else:
                    line = original_line + '"'
                    
                total_repaired += 1
            repaired_lines.append(line)
            
        return '\n'.join(repaired_lines)
    for match in pattern.finditer(content):
        quest_id = int(match.group(1))
        start_index = match.end() - 1 
        
        brace_count = 0
        end_index = -1
        in_quote = False
        escape = False
        
        for i in range(start_index, len(content)):
            char = content[i]
            
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
                
            if char == '"':
                in_quote = not in_quote
                continue
                
            if not in_quote:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_index = i
                        break
                        
        if end_index != -1:
            block_content = content[start_index:end_index+1]
            # 🛡️ 在存入字典前，先进行语法自愈扫描！
            healed_content = repair_broken_string(block_content)
            quests[quest_id] = healed_content
            
    if total_repaired > 0:
        print(f"  🩺 语法自愈系统启动：成功修复了 {total_repaired} 处未闭合的字符串！")
        
    return quests

def merge_lua():
    print("="*60)
    print(" ? RO 客户端 Lua 任务文本三合一合并器 ".center(56, " "))
    print("="*60)

    # 1. 提取三方数据
    print("? 正在解析英文基础架构...")
    en_quests = extract_quests(read_lua_content(EN_FILE))
    
    print("? 正在解析简体中文数据...")
    cn_quests = extract_quests(read_lua_content(CN_FILE))
    
    print("? 正在解析繁体中文数据...")
    tw_quests = extract_quests(read_lua_content(TW_FILE))
    
    if not en_quests:
        print("? 英文源文件为空或解析失败，无法构建基础骨架！")
        return

    print("-" * 60)
    
    # 2. 合并逻辑
    merged_lines = [
        "--[[",
        "    Generated by L10N Merge Script",
        "    Base: EN | Override: CN -> TW(to_CN)",
        "--]]\n",
        "QuestInfoList = {}\n",
        "QuestInfoList = {\n"
    ]
    
    stats = {"cn": 0, "tw_to_cn": 0, "en": 0}
    
    # 遍历英文 ID，保证最全的骨架
    for qid in sorted(en_quests.keys()):
        if qid in cn_quests:
            block = cn_quests[qid]
            stats["cn"] += 1
        elif qid in tw_quests:
            # 命中繁体！使用 zhconv 转换为简体中文
            tw_block = tw_quests[qid]
            block = zhconv.convert(tw_block, 'zh-cn')
            stats["tw_to_cn"] += 1
        else:
            block = en_quests[qid]
            stats["en"] += 1
            
        # 写入文件，保持缩进美观
        merged_lines.append(f"    [{qid}] = {block},")
        
    merged_lines.append("\n}")

    # 3. 强制 GBK 输出
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write("\n".join(merged_lines))
        
    print("=" * 60)
    print("? 合并完成！统计报告：")
    print(f"  ? 总任务数: {len(en_quests)}")
    print(f"  ? 完美命中简中 (CN): {stats['cn']}")
    print(f"  ? 繁体自动转简体 (TW->CN): {stats['tw_to_cn']}")
    print(f"  ?? 无翻译保留英文 (EN): {stats['en']}")
    print(f"\n? 最终文件已生成: {OUT_FILE} (GBK 编码)")
    print("=" * 60)

if __name__ == "__main__":
    merge_lua()