# -*- coding: utf-8 -*-
import os
import re
import zhconv

FILE_NAME = "tipbox.lua" 

# 沿用 systemEN 目录结构
EN_FILE = os.path.join("en_systemEN", FILE_NAME)
CN_FILE = os.path.join("cn_systemEN", FILE_NAME)
TW_FILE = os.path.join("tw_systemEN", FILE_NAME)
OUT_FILE = os.path.join("systemEN", FILE_NAME)

def read_text(filepath, is_tw=False):
    """采用和 itemInfo 一致的终极编码识别引擎"""
    if not os.path.exists(filepath): return ""
    try:
        with open(filepath, 'r', encoding='utf-8') as f: 
            return f.read()
    except UnicodeDecodeError:
        pass
        
    if is_tw:
        # 台湾繁体专属解码
        with open(filepath, 'r', encoding='big5', errors='ignore') as f: 
            return f.read()
    else:
        # EN 和 CN 使用 GB18030 字节级无损容器，绝对保护韩文材质路径
        with open(filepath, 'r', encoding='gb18030', errors='ignore') as f: 
            return f.read()

def merge_tipbox():
    print("="*60)
    print(f" 💡 RO 百科提示箱 ({FILE_NAME}) 终极保真合并 ".center(56, " "))
    print("="*60)
    
    en_text = read_text(EN_FILE, is_tw=False)
    cn_text = read_text(CN_FILE, is_tw=False)
    tw_text = read_text(TW_FILE, is_tw=True)
    
    if not en_text:
        print("❌ 找不到英文源文件！请检查 en_systemEN 目录。")
        return

    # 1. 建立综合翻译字典
    translations = {}
    
    def extract_translations(text, is_tw=False):
        current_id = None
        in_page = False
        
        for line in text.splitlines():
            m_id = re.search(r'^\s*\[(\d+)\]\s*=\s*\{', line)
            if m_id:
                current_id = m_id.group(1)
                if current_id not in translations:
                    translations[current_id] = {'Title': None, 'Page': []}
                in_page = False
                continue
                
            if current_id:
                m_title = re.search(r'Title\s*=\s*"([^"\\]*(?:\\.[^"\\]*)*)"', line)
                if m_title:
                    val = m_title.group(1)
                    if is_tw: val = zhconv.convert(val, 'zh-cn')
                    if re.search(r'[\u4e00-\u9fa5]', val):
                        translations[current_id]['Title'] = val
                    continue
                    
                if re.search(r'Page\s*=\s*\{', line):
                    in_page = True
                    
                if re.search(r'PageEX\s*=\s*\{', line) or re.match(r'^\s*\},?\s*$', line):
                    in_page = False
                    
                if in_page:
                    strings = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', line)
                    for s in strings:
                        if is_tw: s = zhconv.convert(s, 'zh-cn')
                        if re.search(r'[\u4e00-\u9fa5]', s):
                            translations[current_id]['Page'].append(s)

    if tw_text: extract_translations(tw_text, is_tw=True)
    if cn_text: extract_translations(cn_text, is_tw=False)

    # 2. 对英文骨架进行状态机保护式替换
    out_lines = []
    current_id = None
    in_page = False
    page_iter = None
    replaced_count = 0
    
    for line in en_text.splitlines():
        m_id = re.search(r'^\s*\[(\d+)\]\s*=\s*\{', line)
        if m_id:
            current_id = m_id.group(1)
            in_page = False
            if current_id in translations:
                page_iter = iter(translations[current_id]['Page'])
            else:
                page_iter = None
            out_lines.append(line)
            continue
            
        if current_id and current_id in translations:
            if re.search(r'Title\s*=\s*"', line):
                new_title = translations[current_id]['Title']
                if new_title:
                    line = re.sub(r'(Title\s*=\s*")[^"\\]*(?:\\.[^"\\]*)*(")', 
                                  lambda m: m.group(1) + new_title + m.group(2), 
                                  line)
                    replaced_count += 1
            
            if re.search(r'Page\s*=\s*\{', line):
                in_page = True
            if re.search(r'PageEX\s*=\s*\{', line) or re.match(r'^\s*\},?\s*$', line):
                in_page = False
                
            if in_page and page_iter and '"' in line:
                def replacer(match):
                    nonlocal replaced_count
                    try:
                        new_str = next(page_iter)
                        replaced_count += 1
                        return '"' + new_str + '"'
                    except StopIteration:
                        return match.group(0)
                        
                line = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', replacer, line)

        out_lines.append(line)

    # 3. 输出保存
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    
    # 🚀 强制以 GB18030 输出，确保材质路径原样奉还客户端
    with open(OUT_FILE, 'w', encoding='gb18030', errors='ignore') as f:
        f.write("\n".join(out_lines))
        
    print(f"🎉 成功替换了 {replaced_count} 条百科标题与内容说明！")
    print(f"🛡️ GB18030 字节保真已部署，Image 路径乱码已被完美修复！")

if __name__ == "__main__":
    merge_tipbox()