# -*- coding: utf-8 -*-
import os
import re
import zhconv

# 🛠️ 无视大小写的目录雷达
def find_file_ignore_case(folder, target_name):
    if not os.path.exists(folder): return None
    for f in os.listdir(folder):
        if f.lower() == target_name.lower(): return os.path.join(folder, f)
    return None

EN_FILE = find_file_ignore_case("en_systemEN", "ongoingquests.lua") or os.path.join("en_systemEN", "ongoingquests.lua")
CN_FILE = find_file_ignore_case("cn_systemEN", "ongoingquests.lua") or os.path.join("cn_systemEN", "ongoingquests.lua")
TW_FILE = find_file_ignore_case("tw_systemEN", "ongoingquests.lua") or os.path.join("tw_systemEN", "ongoingquests.lua")
OUT_FILE = os.path.join("systemEN", "ongoingquests.lua")

def read_text(filepath, is_tw=False):
    if not os.path.exists(filepath): return ""
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return f.read()
    except UnicodeDecodeError: pass
    if is_tw:
        with open(filepath, 'r', encoding='big5', errors='ignore') as f: return f.read()
    else:
        with open(filepath, 'r', encoding='gb18030', errors='ignore') as f: return f.read()

def get_quest_blocks(text, is_tw=False):
    """🚀 升级版区块提取：无视换行，纯粹依赖大括号物理追踪"""
    blocks = {}
    if not text: return blocks
    
    # 只要找到 [数字] = { 就开始追踪
    pattern = re.finditer(r'\[(\d+)\]\s*=\s*\{', text)
    for m in pattern:
        qid = m.group(1)
        start_idx = m.start()
        brace_idx = m.end() - 1 
        
        count = 0
        in_str = False
        escape = False
        end_idx = -1
        
        for i in range(brace_idx, len(text)):
            c = text[i]
            if not in_str:
                if c == '"': in_str = True
                elif c == '{': count += 1
                elif c == '}':
                    count -= 1
                    if count == 0:
                        end_idx = i
                        break
            else:
                if escape: escape = False
                elif c == '\\': escape = True
                elif c == '"': in_str = False
                
        if end_idx != -1:
            content = text[start_idx : end_idx+1]
            if is_tw: content = zhconv.convert(content, 'zh-cn')
            blocks[qid] = content
            
    return blocks

def extract_lua_field(block, field_name):
    """🚀 升级版字段提取：去掉 ^ 锚点，加入 \\b 单词边界，完美兼容单行内多字段"""
    
    # 1. 提取单行字符串: Title = "..."
    # 使用 \b 确保匹配的是确切的单词（比如 Title，而不是 subTitle）
    m_str = re.search(rf'\b{field_name}\s*=\s*"[^"\\]*(?:\\.[^"\\]*)*"', block)
    if m_str: return m_str.group(0)
        
    # 2. 提取大括号数组: Description = { ... }
    m_tbl = re.search(rf'\b{field_name}\s*=\s*\{{', block)
    if m_tbl:
        start_idx = m_tbl.start()
        content_start = m_tbl.end() - 1
        count = 0
        in_str = False
        escape = False
        for i in range(content_start, len(block)):
            c = block[i]
            if not in_str:
                if c == '"': in_str = True
                elif c == '{': count += 1
                elif c == '}':
                    count -= 1
                    if count == 0:
                        return block[start_idx : i+1]
            else:
                if escape: escape = False
                elif c == '\\': escape = True
                elif c == '"': in_str = False
    return None

def merge_ongoingquests():
    print("="*60)
    print(f" 📜 RO 正在进行的任务表 (终极排版兼容版) ".center(52, " "))
    print("="*60)
    
    en_text = read_text(EN_FILE, is_tw=False)
    cn_text = read_text(CN_FILE, is_tw=False)
    tw_text = read_text(TW_FILE, is_tw=True)
    
    if not en_text:
        print(f"❌ 找不到英文源文件！路径: {EN_FILE}")
        return

    en_blocks = get_quest_blocks(en_text)
    cn_blocks = get_quest_blocks(cn_text)
    tw_blocks = get_quest_blocks(tw_text, is_tw=True)

    out_text = en_text
    replaced_count = 0
    added_count = 0

    for qid, en_block in en_blocks.items():
        source_block = cn_blocks.get(qid) or tw_blocks.get(qid)
        if source_block:
            new_en_block = en_block
            block_modified = False
            
            for field in ['Title', 'Summary', 'Description', 'TargetName', 'Info']:
                src_field_str = extract_lua_field(source_block, field)
                en_field_str = extract_lua_field(new_en_block, field)
                
                if src_field_str and en_field_str:
                    new_en_block = new_en_block.replace(en_field_str, src_field_str)
                    block_modified = True
                    
            if block_modified and new_en_block != en_block:
                out_text = out_text.replace(en_block, new_en_block)
                replaced_count += 1

    added_blocks = []
    all_cn_tw_ids = set(cn_blocks.keys()) | set(tw_blocks.keys())
    missing_ids = [qid for qid in all_cn_tw_ids if qid not in en_blocks]
    
    for qid in missing_ids:
        added_blocks.append(cn_blocks.get(qid) or tw_blocks.get(qid))
        added_count += 1

    if added_blocks:
        last_brace_idx = out_text.rfind('\n}')
        if last_brace_idx != -1:
            prefix = out_text[:last_brace_idx].rstrip()
            if not prefix.endswith(','): prefix += ','
            insertion = '\n' + ',\n'.join(added_blocks) + '\n}'
            out_text = prefix + insertion + out_text[last_brace_idx+2:]

    if os.path.dirname(OUT_FILE):
        os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
        
    with open(OUT_FILE, 'w', encoding='gb18030', errors='ignore') as f:
        f.write(out_text)
        
    print(f"✅ 处理完毕: 成功替换了 {replaced_count} 个任务的文本与数组！")
    if added_count > 0:
        print(f"✨ 发现并追加了 {added_count} 个 EN 中缺失的新任务！")
    print("="*60)

if __name__ == "__main__":
    merge_ongoingquests()