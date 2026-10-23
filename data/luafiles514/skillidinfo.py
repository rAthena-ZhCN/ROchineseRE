# -*- coding: utf-8 -*-
import os
import re
import zhconv

FILE_NAME = "skillinfoz/skillinfolist.lua" 

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

def merge_skillinfolist():
    print("="*60)
    print(f" ⚔️ RO 技能信息表 ({FILE_NAME}) 精准合并 ".center(56, " "))
    print("="*60)
    
    en_text = read_text(EN_FILE)
    cn_text = read_text(CN_FILE)
    tw_text = read_text(TW_FILE)
    
    if not en_text:
        print("❌ 找不到英文源文件！")
        return

    # 1. 建立技能翻译字典: dict["SKID.NPC_TARGET_MARKER"] = "目标标记"
    translations = {}
    
    def extract_translations(text, is_tw=False):
        current_skid = None
        for line in text.splitlines():
            # 捕捉门牌号 (技能ID): [SKID.NPC_TARGET_MARKER] = {
            m_skid = re.search(r'\[\s*(SKID\.[a-zA-Z0-9_]+)\s*\]\s*=\s*\{', line)
            if m_skid:
                current_skid = m_skid.group(1)
            
            # 捕捉需要翻译的挂画 (技能名): SkillName = "Target Marker",
            m_name = re.search(r'SkillName\s*=\s*"([^"]+)"', line)
            if m_name and current_skid:
                val = m_name.group(1)
                
                # 繁体转简体，且必须包含中文，防韩文乱码
                if is_tw: val = zhconv.convert(val, 'zh-cn')
                if re.search(r'[\u4e00-\u9fa5]', val):
                    translations[current_skid] = val

    if tw_text: extract_translations(tw_text, is_tw=True)
    if cn_text: extract_translations(cn_text, is_tw=False) # 简体覆盖繁体

    # 2. 对英文骨架进行微创手术替换
    out_lines = []
    current_skid = None
    replaced_count = 0
    
    for line in en_text.splitlines():
        # 同步英文本本中的当前门牌号
        m_skid = re.search(r'\[\s*(SKID\.[a-zA-Z0-9_]+)\s*\]\s*=\s*\{', line)
        if m_skid:
            current_skid = m_skid.group(1)
            
        # 如果当前门牌号有对应的中文翻译，并且正好走到了挂画（SkillName）前
        if current_skid in translations:
            if re.search(r'SkillName\s*=\s*"', line):
                new_val = translations[current_skid]
                # 仅精准替换双引号内的内容，保留所有的空格、逗号和等号
                line = re.sub(r'(SkillName\s*=\s*")[^"]+(")', r'\g<1>' + new_val + r'\g<2>', line)
                replaced_count += 1
                
        out_lines.append(line)

    # 3. 输出保存
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write("\n".join(out_lines))
        
    print(f"🎉 成功替换了 {replaced_count} 条技能名称！")
    print(f"🛡️ 所有的底层阵列如 AttackRange, SkillScale 均被完美保护。")

if __name__ == "__main__":
    merge_skillinfolist()