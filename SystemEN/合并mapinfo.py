# -*- coding: utf-8 -*-
import os
import re
import zhconv

FILE_NAME = "mapInfo.lua" 

EN_FILE = os.path.join("en_systemEN", FILE_NAME)
CN_FILE = os.path.join("cn_systemEN", FILE_NAME)
TW_FILE = os.path.join("tw_systemEN", FILE_NAME)
OUT_FILE = os.path.join("systemEN", FILE_NAME)

def read_text(filepath, is_tw=False):
    if not os.path.exists(filepath): return ""
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return f.read()
    except UnicodeDecodeError:
        pass
    if is_tw:
        with open(filepath, 'r', encoding='big5', errors='ignore') as f: return f.read()
    else:
        with open(filepath, 'r', encoding='gb18030', errors='ignore') as f: return f.read()

def merge_mapinfo():
    print("="*60)
    print(f" 🗺️ RO 地图信息表 ({FILE_NAME}) 无损装甲版 ".center(56, " "))
    print("="*60)
    
    en_text = read_text(EN_FILE, is_tw=False)
    cn_text = read_text(CN_FILE, is_tw=False)
    tw_text = read_text(TW_FILE, is_tw=True)
    
    if not en_text:
        print("❌ 找不到英文源文件！")
        return

    translations = {}
    
    def extract_translations(text, is_tw=False):
        current_map = None
        for line in text.splitlines():
            m_map = re.search(r'\[\s*"([^"]+)"\s*\]\s*=\s*\{', line)
            if m_map:
                current_map = m_map.group(1)
                if current_map not in translations: translations[current_map] = {}
                continue
            if current_map:
                for key in ['displayName', 'mainTitle', 'subTitle']:
                    m_val = re.search(rf'{key}\s*=\s*"([^"\\]*(?:\\.[^"\\]*)*)"', line)
                    if m_val:
                        val = m_val.group(1)
                        if is_tw: val = zhconv.convert(val, 'zh-cn')
                        if re.search(r'[\u4e00-\u9fa5]', val):
                            translations[current_map][key] = val

    if tw_text: extract_translations(tw_text, is_tw=True)
    if cn_text: extract_translations(cn_text, is_tw=False)

    out_lines = []
    current_map = None
    replaced_count = 0
    
    for line in en_text.splitlines():
        m_map = re.search(r'\[\s*"([^"]+)"\s*\]\s*=\s*\{', line)
        if m_map:
            current_map = m_map.group(1)
            
        if current_map and current_map in translations:
            trans = translations[current_map]
            if 'displayName' in trans and re.search(r'displayName\s*=\s*"', line):
                line = re.sub(r'(displayName\s*=\s*")[^"]*(")', lambda m: m.group(1) + trans['displayName'] + m.group(2), line)
                replaced_count += 1
            if 'mainTitle' in trans and re.search(r'mainTitle\s*=\s*"', line):
                line = re.sub(r'(mainTitle\s*=\s*")[^"]*(")', lambda m: m.group(1) + trans['mainTitle'] + m.group(2), line)
                replaced_count += 1
            if 'subTitle' in trans and re.search(r'subTitle\s*=\s*"', line):
                line = re.sub(r'(subTitle\s*=\s*")[^"]*(")', lambda m: m.group(1) + trans['subTitle'] + m.group(2), line)
                replaced_count += 1
                
        out_lines.append(line)

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='gb18030', errors='ignore') as f:
        f.write("\n".join(out_lines))
        
    print(f"🎉 成功替换了 {replaced_count} 条地图中英名称！(BGM材质已保真)")

if __name__ == "__main__":
    merge_mapinfo()