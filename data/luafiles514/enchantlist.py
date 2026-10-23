# -*- coding: utf-8 -*-
import os
import re
import zhconv

FILE_NAME = "enchant/enchantlist.lua" 

EN_FILE = os.path.join("en_lua files", FILE_NAME)
CN_FILE = os.path.join("cn_lua files", FILE_NAME)
TW_FILE = os.path.join("tw_lua files", FILE_NAME)
OUT_FILE = os.path.join("lua files", FILE_NAME)

def read_text(filepath):
    if not os.path.exists(filepath): return ""
    for enc in ['utf-8', 'gbk', 'big5']:
        try:
            with open(filepath, 'r', encoding=enc) as f: return f.read()
        except: continue
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: return f.read()

def merge_enchantlist():
    print("="*60)
    print(f" 🗡️ RO 附魔配置表 ({FILE_NAME}) 修正防换行版 ".center(56, " "))
    print("="*60)
    
    en_text = read_text(EN_FILE)
    cn_text = read_text(CN_FILE)
    tw_text = read_text(TW_FILE)
    
    if not en_text:
        print("❌ 找不到英文源文件！")
        return

    translations = {}
    
    def extract_translations(text, is_tw=False):
        for line in text.splitlines():
            m = re.search(r'(Table\[\d+\]):SetCaution\s*\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"\s*\)', line)
            if m:
                table_id = m.group(1)
                caution_text = m.group(2)
                
                if is_tw: caution_text = zhconv.convert(caution_text, 'zh-cn')
                if caution_text.strip():
                    translations[table_id] = caution_text

    if tw_text: extract_translations(tw_text, is_tw=True)
    if cn_text: extract_translations(cn_text, is_tw=False)

    out_lines = []
    replaced_count = 0
    
    for line in en_text.splitlines():
        m = re.search(r'(Table\[\d+\]):SetCaution\s*\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"\s*\)', line)
        if m:
            table_id = m.group(1)
            if table_id in translations:
                new_text = translations[table_id]
                # 🚀 核心修复：使用 lambda 函数，彻底阻止 Python 将 \n 转义为真实回车
                line = re.sub(r'(SetCaution\s*\(\s*")[^"\\]*(?:\\.[^"\\]*)*("\s*\))', 
                              lambda match: match.group(1) + new_text + match.group(2), 
                              line)
                replaced_count += 1
                
        out_lines.append(line)

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write("\n".join(out_lines))
        
    print(f"🎉 成功替换了 {replaced_count} 条附魔说明文本！")
    print(f"🛡️ 自动换行 Bug 已修复，\\n 已被完美保留为代码形式。")

if __name__ == "__main__":
    merge_enchantlist()