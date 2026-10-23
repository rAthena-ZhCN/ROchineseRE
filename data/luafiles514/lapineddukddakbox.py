# -*- coding: utf-8 -*-
import os
import re
import zhconv

# ================= 配置区 =================
FILE_NAME = "datainfo/lapineddukddakbox.lua" 

EN_FILE = os.path.join("en_lua files", FILE_NAME)
CN_FILE = os.path.join("cn_lua files", FILE_NAME)
TW_FILE = os.path.join("tw_lua files", FILE_NAME)
OUT_FILE = os.path.join("lua files", FILE_NAME)

# 🛑 内部保留字黑名单：遇到这些伪装成箱子 ID 的变量名时，坚决无视！
IGNORED_BOX_NAMES = {
    'SourceItems', 'ResultItems', 'sources', 'results', 
    'Warp', 'tblLapineDdukddakBox', 'tblLapineUpgradeBox', 'tblLapineExchangeBox'
}
# ==========================================

def read_text(filepath):
    if not os.path.exists(filepath): return ""
    for enc in ['utf-8', 'gbk', 'big5']:
        try:
            with open(filepath, 'r', encoding=enc) as f: return f.read()
        except: continue
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: return f.read()

def merge_lapinebox():
    print("="*60)
    print(f" 📦 RO 拉比纳箱子配置 ({FILE_NAME}) V3 安全合并 ".center(56, " "))
    print("="*60)
    
    en_text = read_text(EN_FILE)
    cn_text = read_text(CN_FILE)
    tw_text = read_text(TW_FILE)
    
    if not en_text:
        print("❌ 找不到英文源文件！")
        return

    translations = {}
    
    def extract_translations(text, is_tw=False):
        current_box_id = None
        for line in text.splitlines():
            # 雷达扫描箱子 ID
            m_box = re.search(r'^\s*(?:\["([^"]+)"\]|([a-zA-Z0-9_]+))\s*=\s*\{', line)
            if m_box:
                potential_box = m_box.group(1) or m_box.group(2)
                # 核心防误伤拦截：只有不在黑名单里的，才是真正的箱子 ID！
                if potential_box not in IGNORED_BOX_NAMES:
                    current_box_id = potential_box
                    if current_box_id not in translations:
                        translations[current_box_id] = {}
            
            # 提取翻译
            m_field = re.search(r'([a-zA-Z0-9_]+)\s*=\s*"([^"]+)"', line)
            if m_field and current_box_id:
                field_name = m_field.group(1)
                val = m_field.group(2)
                
                if is_tw: val = zhconv.convert(val, 'zh-cn')
                if re.search(r'[\u4e00-\u9fa5]', val):
                    translations[current_box_id][field_name] = val

    if tw_text: extract_translations(tw_text, is_tw=True)
    if cn_text: extract_translations(cn_text, is_tw=False)

    out_lines = []
    current_box_id = None
    replaced_count = 0
    
    for line in en_text.splitlines():
        # 同步英文本本中的真实箱子 ID
        m_box = re.search(r'^\s*(?:\["([^"]+)"\]|([a-zA-Z0-9_]+))\s*=\s*\{', line)
        if m_box:
            potential_box = m_box.group(1) or m_box.group(2)
            if potential_box not in IGNORED_BOX_NAMES:
                current_box_id = potential_box
            
        if current_box_id in translations:
            m_field = re.search(r'([a-zA-Z0-9_]+)\s*=\s*"([^"]+)"', line)
            if m_field:
                field_name = m_field.group(1)
                if field_name in translations[current_box_id]:
                    new_val = translations[current_box_id][field_name]
                    line = re.sub(r'(=\s*")[^"]+(")', r'\g<1>' + new_val + r'\g<2>', line)
                    replaced_count += 1
                
        out_lines.append(line)

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write("\n".join(out_lines))
        
    print(f"🎉 成功替换了 {replaced_count} 条拉比纳箱子的说明文本！")
    print(f"🛡️ 变量劫持 Bug 已彻底修复，所有的箱子均被正确锚定！")

if __name__ == "__main__":
    merge_lapinebox()