# -*- coding: utf-8 -*-
import os
import re
import zhconv

# 文件配置
DESC_FILE = "rune/desc.lua"
SET_DESC_FILE = "rune/set_desc.lua"

def get_source_files(filename):
    return [
        (os.path.join("tw_systemEN", filename), True),
        (os.path.join("cn_systemEN", filename), False)
    ]

def read_text(filepath, is_tw=False):
    if not os.path.exists(filepath): return ""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        pass
        
    if is_tw:
        with open(filepath, 'r', encoding='big5', errors='ignore') as f:
            return f.read()
    else:
        with open(filepath, 'r', encoding='gbk', errors='ignore') as f:
            return f.read()

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fa5]', text))

def extract_table_block(text, start_idx):
    """通用的 AST 大括号截取器，用于提取 RuneSetDescription 的完整数组"""
    count = 0
    in_str = False
    escape = False
    for i in range(start_idx, len(text)):
        char = text[i]
        if not in_str:
            if char == '"': in_str = True
            elif char == '{': count += 1
            elif char == '}':
                count -= 1
                if count == 0: return text[start_idx : i+1]
        else:
            if escape: escape = False
            elif char == '\\': escape = True
            elif char == '"': in_str = False
    return None

# ==========================================
# 模块 1：处理 desc.lua (单行替换)
# ==========================================
def process_desc():
    print("="*60)
    print(f" 🔮 开始处理符文名称表: {DESC_FILE} ".center(56, " "))
    print("="*60)
    
    en_file = os.path.join("en_systemEN", DESC_FILE)
    out_file = os.path.join("systemEN", DESC_FILE)
    en_text = read_text(en_file, is_tw=False)
    
    if not en_text:
        print(f"❌ 找不到英文源文件 {DESC_FILE}！跳过。")
        return

    translations = {}
    
    # 提取翻译
    for filepath, is_tw in get_source_files(DESC_FILE):
        text = read_text(filepath, is_tw=is_tw)
        if not text: continue
        
        # 匹配单行: [RUNEIDTBL.Rp_Ep17_Melee] = { Rune_DisplayName = "可疑零件(近距离)" }
        for m in re.finditer(r'\[(RUNEIDTBL\.[a-zA-Z0-9_]+)\]\s*=\s*\{\s*Rune_DisplayName\s*=\s*"([^"]+)"', text):
            qid = m.group(1)
            val = m.group(2)
            if has_chinese(val):
                if is_tw: val = zhconv.convert(val, 'zh-cn')
                translations[qid] = val

    # 替换 EN
    replaced_count = 0
    def replacer(m):
        nonlocal replaced_count
        qid = m.group(1)
        if qid in translations:
            replaced_count += 1
            return f'[{qid}] = {{ Rune_DisplayName = "{translations[qid]}"'
        return m.group(0)

    out_text = re.sub(r'\[(RUNEIDTBL\.[a-zA-Z0-9_]+)\]\s*=\s*\{\s*Rune_DisplayName\s*=\s*"[^"]+"', replacer, en_text)

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='gbk', errors='ignore') as f:
        f.write(out_text)
        
    print(f"✅ 处理完毕: 成功替换了 {replaced_count} 个符文名称！")

# ==========================================
# 模块 2：处理 set_desc.lua (多行区块替换)
# ==========================================
def process_set_desc():
    print("\n" + "="*60)
    print(f" 📜 开始处理符文套装说明表: {SET_DESC_FILE} ".center(56, " "))
    print("="*60)
    
    en_file = os.path.join("en_systemEN", SET_DESC_FILE)
    out_file = os.path.join("systemEN", SET_DESC_FILE)
    en_text = read_text(en_file, is_tw=False)
    
    if not en_text:
        print(f"❌ 找不到英文源文件 {SET_DESC_FILE}！跳过。")
        return

    translations = {}
    
    # 提取翻译
    for filepath, is_tw in get_source_files(SET_DESC_FILE):
        text = read_text(filepath, is_tw=is_tw)
        if not text: continue
        
        # 定位所有套装 ID: [RUNESETIDTBL.Rt_Ep17_Doubt] = {
        for m in re.finditer(r'\[(RUNESETIDTBL\.[a-zA-Z0-9_]+)\]\s*=\s*\{', text):
            qid = m.group(1)
            block_start = m.end() - 1
            block_str = extract_table_block(text, block_start)
            
            if block_str and qid not in translations:
                translations[qid] = {}
                
            if block_str:
                # 提取名称
                m_name = re.search(r'RuneSetDisplayName\s*=\s*"([^"]+)"', block_str)
                if m_name and has_chinese(m_name.group(1)):
                    val = m_name.group(1)
                    if is_tw: val = zhconv.convert(val, 'zh-cn')
                    translations[qid]['name'] = val
                    
                # 提取套装说明数组
                m_desc = re.search(r'RuneSetDescription\s*=\s*\{', block_str)
                if m_desc:
                    desc_start = m_desc.end() - 1
                    desc_str = extract_table_block(block_str, desc_start)
                    if desc_str and has_chinese(desc_str):
                        if is_tw: desc_str = zhconv.convert(desc_str, 'zh-cn')
                        translations[qid]['desc'] = desc_str

    # 替换 EN 区块
    replaced_names = 0
    replaced_descs = 0
    out_text = en_text
    
    for qid, trans in translations.items():
        # 在 EN 中寻找对应的模块
        m_en = re.search(rf'\[{qid.replace(".", r"\.")}\]\s*=\s*\{{', out_text)
        if m_en:
            block_start = m_en.end() - 1
            en_block = extract_table_block(out_text, block_start)
            
            if en_block:
                new_block = en_block
                
                # 替换名称
                if 'name' in trans:
                    new_block, n = re.subn(r'(RuneSetDisplayName\s*=\s*")[^"]+(")', rf'\g<1>{trans["name"]}\g<2>', new_block)
                    if n > 0: replaced_names += 1
                        
                # 替换数组
                if 'desc' in trans:
                    m_en_desc = re.search(r'RuneSetDescription\s*=\s*\{', new_block)
                    if m_en_desc:
                        en_desc_start = m_en_desc.end() - 1
                        en_desc_str = extract_table_block(new_block, en_desc_start)
                        if en_desc_str:
                            new_block = new_block.replace(en_desc_str, trans['desc'])
                            replaced_descs += 1
                            
                if new_block != en_block:
                    out_text = out_text.replace(en_block, new_block)

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='gbk', errors='ignore') as f:
        f.write(out_text)
        
    print(f"✅ 处理完毕: 成功替换了 {replaced_names} 个套装名称，{replaced_descs} 个套装说明！")
    print("="*60)

if __name__ == "__main__":
    process_desc()
    process_set_desc()