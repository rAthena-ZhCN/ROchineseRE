# -*- coding: utf-8 -*-
import os
import re
import zhconv

FILE_NAME = "achievements.lua" 

EN_FILE = os.path.join("en_systemEN", FILE_NAME)
CN_FILE = os.path.join("cn_systemEN", FILE_NAME)
TW_FILE = os.path.join("tw_systemEN", FILE_NAME)
OUT_FILE = os.path.join("systemEN", FILE_NAME)

def read_text(filepath, is_tw=False):
    if not os.path.exists(filepath): return ""
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return f.read()
    except: pass
    if is_tw:
        with open(filepath, 'r', encoding='big5', errors='ignore') as f: return f.read()
    else:
        with open(filepath, 'r', encoding='gb18030', errors='ignore') as f: return f.read()

def merge_achievements():
    print("="*60)
    print(f" 🏆 RO 成就系统表 ({FILE_NAME}) 无损装甲版 ".center(56, " "))
    print("="*60)
    
    en_text = read_text(EN_FILE, is_tw=False)
    cn_text = read_text(CN_FILE, is_tw=False)
    tw_text = read_text(TW_FILE, is_tw=True)
    
    if not en_text: return

    translations = {}
    def extract_translations(text, is_tw=False):
        current_id = None
        for line in text.splitlines():
            m_id = re.search(r'^\s*\[(\d+)\]\s*=\s*\{', line)
            if m_id:
                current_id = m_id.group(1)
                if current_id not in translations:
                    translations[current_id] = {'title': [], 'summary': [], 'details': [], 'text': []}
                continue
            if current_id:
                m_field = re.search(r'(title|summary|details|text)\s*=\s*"([^"\\]*(?:\\.[^"\\]*)*)"', line)
                if m_field:
                    field = m_field.group(1)
                    val = m_field.group(2)
                    if is_tw: val = zhconv.convert(val, 'zh-cn')
                    if re.search(r'[\u4e00-\u9fa5]', val):
                        translations[current_id][field].append(val)

    if tw_text: extract_translations(tw_text, is_tw=True)
    if cn_text: extract_translations(cn_text, is_tw=False)

    out_lines = []
    current_id = None
    field_iters = {}
    replaced_count = 0
    
    for line in en_text.splitlines():
        m_id = re.search(r'^\s*\[(\d+)\]\s*=\s*\{', line)
        if m_id:
            current_id = m_id.group(1)
            field_iters = {}
            if current_id in translations:
                for k, v in translations[current_id].items(): field_iters[k] = iter(v)
            out_lines.append(line)
            continue
            
        if current_id and current_id in translations:
            m_field = re.search(r'(title|summary|details|text)\s*=\s*"([^"\\]*(?:\\.[^"\\]*)*)"', line)
            if m_field:
                field = m_field.group(1)
                if field in field_iters:
                    try:
                        new_val = next(field_iters[field])
                        line = re.sub(r'(' + field + r'\s*=\s*")[^"\\]*(?:\\.[^"\\]*)*(")', 
                                      lambda m: m.group(1) + new_val + m.group(2), line)
                        replaced_count += 1
                    except StopIteration: pass
        out_lines.append(line)

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='gb18030', errors='ignore') as f:
        f.write("\n".join(out_lines))
        
    print(f"🎉 成功替换了 {replaced_count} 条成就文本！")

if __name__ == "__main__":
    merge_achievements()