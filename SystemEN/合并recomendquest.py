# -*- coding: utf-8 -*-
import os
import re
import zhconv

FILES_TO_PROCESS = ["RecommendedQuests.lua", "RecommendedQuests_basic.lua"]

def read_text(filepath, is_tw=False):
    if not os.path.exists(filepath): return ""
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return f.read()
    except: pass
    if is_tw:
        with open(filepath, 'r', encoding='big5', errors='ignore') as f: return f.read()
    else:
        with open(filepath, 'r', encoding='gb18030', errors='ignore') as f: return f.read()

def get_quest_blocks(text, is_tw=False):
    blocks = {}
    if not text: return blocks
    pattern = re.compile(r'^(\s*)\[(\d+)\]\s*=\s*\{(.*?^\1\})', re.MULTILINE | re.DOTALL)
    for m in pattern.finditer(text):
        qid = m.group(2)
        content = m.group(0)
        if is_tw: content = zhconv.convert(content, 'zh-cn')
        blocks[qid] = content
    return blocks

def process_file(file_name):
    print("="*60)
    print(f" 📜 推荐任务表: {file_name} 无损装甲版 ".center(56, " "))
    print("="*60)
    
    en_file = os.path.join("en_systemEN", file_name)
    cn_file = os.path.join("cn_systemEN", file_name)
    tw_file = os.path.join("tw_systemEN", file_name)
    out_file = os.path.join("systemEN", file_name)

    en_text = read_text(en_file, is_tw=False)
    cn_text = read_text(cn_file, is_tw=False)
    tw_text = read_text(tw_file, is_tw=True)
    
    if not en_text: return

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
            for field in ['Title', 'Summary']:
                m_src = re.search(r'(' + field + r'\s*=\s*")[^"\\]*(?:\\.[^"\\]*)*(")', source_block)
                if m_src:
                    new_en_block = re.sub(r'(' + field + r'\s*=\s*")[^"\\]*(?:\\.[^"\\]*)*(")', 
                                          lambda m, src=m_src.group(0): src, new_en_block)
                    
            for field in ['QuestInfo1', 'QuestInfo2', 'QuestInfo3']:
                m_src = re.search(r'(' + field + r'\s*=\s*\{.*?\}(?:,|$))', source_block, re.DOTALL | re.MULTILINE)
                if m_src:
                    new_en_block = re.sub(r'' + field + r'\s*=\s*\{.*?\}(?:,|$)',
                                          lambda m, src=m_src.group(1): src, new_en_block, flags=re.DOTALL | re.MULTILINE)
                    
            if new_en_block != en_block:
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

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='gb18030', errors='ignore') as f:
        f.write(out_text)
        
    print(f"✅ 替换了 {replaced_count} 个任务，追加了 {added_count} 个新任务！(材质安全)")

if __name__ == "__main__":
    for f in FILES_TO_PROCESS:
        process_file(f)