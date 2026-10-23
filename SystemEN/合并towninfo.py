# -*- coding: utf-8 -*-
import os
import re
import zhconv

FILE_NAME = "Towninfo.lua" 

# 沿用 systemEN 目录结构
EN_FILE = os.path.join("en_systemEN", FILE_NAME)
CN_FILE = os.path.join("cn_systemEN", FILE_NAME)
TW_FILE = os.path.join("tw_systemEN", FILE_NAME)
OUT_FILE = os.path.join("systemEN", FILE_NAME)

# 🎯 核心配置：允许的坐标误差范围（曼哈顿距离）
XY_TOLERANCE = 5 

def read_text(filepath):
    if not os.path.exists(filepath): return ""
    for enc in ['utf-8', 'gbk', 'big5']:
        try:
            with open(filepath, 'r', encoding=enc) as f: return f.read()
        except: continue
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: return f.read()

def merge_towninfo():
    print("="*60)
    print(f" 📍 RO 城镇向导信息表 ({FILE_NAME}) 终极版 ".center(56, " "))
    print("="*60)
    
    en_text = read_text(EN_FILE)
    cn_text = read_text(CN_FILE)
    tw_text = read_text(TW_FILE)
    
    if not en_text:
        print("❌ 找不到英文源文件！请检查 en_systemEN 目录。")
        return

    translations = {}
    
    def extract_translations(text, is_tw=False):
        current_map = None
        for line in text.splitlines():
            m_map = re.search(r'^\s*([a-zA-Z0-9_]+)\s*=\s*\{', line)
            if m_map:
                map_name = m_map.group(1)
                if map_name != "mapNPCInfoTable":
                    current_map = map_name
                    if current_map not in translations:
                        translations[current_map] = []
                continue
                
            if current_map:
                # 🚀 升级版雷达：同时兼容 "..." 和 [=[...]=]
                # 正则解析: (?:"|\[=\[) 代表匹配双引号或者 [=[
                # (.*?) 提取里面的内容
                # (?:"|\]=\]) 代表匹配双引号或者 ]=] 结尾
                m_entry = re.search(r'name\s*=\s*(?:"|\[=\[)(.*?)(?:"|\]=\])\s*,\s*X\s*=\s*(\d+)\s*,\s*Y\s*=\s*(\d+)\s*,\s*TYPE\s*=\s*(\d+)', line)
                if m_entry:
                    val = m_entry.group(1)
                    if is_tw: val = zhconv.convert(val, 'zh-cn')
                    if re.search(r'[\u4e00-\u9fa5]', val):
                        translations[current_map].append({
                            'name': val,
                            'x': int(m_entry.group(2)),
                            'y': int(m_entry.group(3)),
                            'type': int(m_entry.group(4))
                        })

    if tw_text: extract_translations(tw_text, is_tw=True)
    if cn_text: extract_translations(cn_text, is_tw=False)

    out_lines = []
    current_map = None
    replaced_count = 0
    
    for line in en_text.splitlines():
        m_map = re.search(r'^\s*([a-zA-Z0-9_]+)\s*=\s*\{', line)
        if m_map:
            map_name = m_map.group(1)
            if map_name != "mapNPCInfoTable":
                current_map = map_name
            out_lines.append(line)
            continue
            
        if current_map and current_map in translations:
            # 同样使用双模态雷达扫描英文本本
            m_entry = re.search(r'name\s*=\s*(?:"|\[=\[)(.*?)(?:"|\]=\])\s*,\s*X\s*=\s*(\d+)\s*,\s*Y\s*=\s*(\d+)\s*,\s*TYPE\s*=\s*(\d+)', line)
            if m_entry:
                en_x = int(m_entry.group(2))
                en_y = int(m_entry.group(3))
                en_type = int(m_entry.group(4))
                
                best_match = None
                min_dist = 9999
                
                for cand in translations[current_map]:
                    if cand['type'] == en_type:
                        dist = abs(cand['x'] - en_x) + abs(cand['y'] - en_y)
                        if dist <= XY_TOLERANCE and dist < min_dist:
                            min_dist = dist
                            best_match = cand['name']
                            
                if best_match:
                    # 🚀 升级版替换：完美保留原有的包装壳 (双引号或方括号)
                    # group(1) 捕获左边的壳 name = [=[
                    # group(3) 捕获右边的壳 ]=]
                    line = re.sub(r'(name\s*=\s*(?:"|\[=\[))(.*?)("|\]=\])', 
                                  lambda m: m.group(1) + best_match + m.group(3), 
                                  line, count=1)
                    replaced_count += 1
                    
        out_lines.append(line)

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write("\n".join(out_lines))
        
    print(f"🎉 成功替换了 {replaced_count} 条城镇向导 (NPC) 名称！")
    print(f"🛡️ 已完美兼容 Lua 多行字符串语法 [=[ ]=] ，替换后不破坏代码结构！")

if __name__ == "__main__":
    merge_towninfo()