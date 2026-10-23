# -*- coding: utf-8 -*-
import os
import re
import zhconv

FILE_NAME = "agit/agitconfig.lua" 

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

def merge_agitconfig():
    print("="*60)
    print(f" 🏰 RO 据点配置文件 ({FILE_NAME}) 精准合并 ".center(56, " "))
    print("="*60)
    
    en_text = read_text(EN_FILE)
    cn_text = read_text(CN_FILE)
    tw_text = read_text(TW_FILE)
    
    if not en_text:
        print("❌ 找不到英文源文件！")
        return

    # 1. 建立精准翻译字典: dict["prtg_cas01.gat"] = "克林喜德"
    translations = {}
    
    def extract_translations(text, is_tw=False):
        current_key = None
        for line in text.splitlines():
            # 捕捉锚点: ["prtg_cas01.gat"] = {
            m_key = re.search(r'\["([^"]+\.gat)"\]\s*=\s*\{', line)
            if m_key:
                current_key = m_key.group(1)
            
            # 捕捉需要翻译的目标行: Name = "克林喜德",
            m_str = re.search(r'Name\s*=\s*"([^"]+)"', line)
            if m_str and current_key:
                val = m_str.group(1)
                if is_tw: val = zhconv.convert(val, 'zh-cn')
                # 过滤防乱码
                if re.search(r'[\u4e00-\u9fa5]', val):
                    translations[current_key] = val

    if tw_text: extract_translations(tw_text, is_tw=True)
    if cn_text: extract_translations(cn_text, is_tw=False)

    # 2. 对英文骨架进行“外科手术”替换
    out_lines = []
    current_key = None
    replaced_count = 0
    
    for line in en_text.splitlines():
        # 追踪当前锚点
        m_key = re.search(r'\["([^"]+\.gat)"\]\s*=\s*\{', line)
        if m_key:
            current_key = m_key.group(1)
            
        # 如果当前锚点在字典里，且遇到 Name 行，执行微创替换！
        if current_key in translations:
            if re.search(r'Name\s*=\s*"', line):
                line = re.sub(r'(Name\s*=\s*")[^"]+(")', r'\g<1>' + translations[current_key] + r'\g<2>', line)
                replaced_count += 1
                
        out_lines.append(line)

    # 3. 输出保存
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write("\n".join(out_lines))
        
    print(f"🎉 成功替换了 {replaced_count} 个据点名称！")
    print(f"🛡️ 内部代码 (如 EFST_MOVE_AGIT) 毫发无损，完美避开错位问题。")

if __name__ == "__main__":
    merge_agitconfig()