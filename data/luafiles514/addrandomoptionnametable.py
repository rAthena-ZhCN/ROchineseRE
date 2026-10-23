# -*- coding: utf-8 -*-
import os
import re
import zhconv

FILE_NAME = "datainfo/addrandomoptionnametable.lua" 

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

def merge_randomoption():
    print("="*60)
    print(f" ✨ RO 随机属性词条表 ({FILE_NAME}) 精准合并 ".center(56, " "))
    print("="*60)
    
    en_text = read_text(EN_FILE)
    cn_text = read_text(CN_FILE)
    tw_text = read_text(TW_FILE)
    
    if not en_text:
        print("❌ 找不到英文源文件！")
        return

    # 1. 建立精准翻译字典: dict["EnumVAR.VAR_MAXHPAMOUNT[1]"] = "MHP + %d"
    translations = {}
    
    def extract_translations(text, is_tw=False):
        for line in text.splitlines():
            # 捕捉锚点和内容: [EnumVAR.xxx[1]] = "翻译内容",
            m = re.search(r'^\s*\[([A-Za-z0-9_\.\[\]]+)\]\s*=\s*"([^"]*)"', line)
            if m:
                key = m.group(1)
                val = m.group(2)
                if is_tw: val = zhconv.convert(val, 'zh-cn')
                
                # 信任 CN/TW 的提取结果（因为像 "MHP + %d" 也是合法翻译）
                # 只要它不是空的，就录入字典
                if val.strip():
                    translations[key] = val

    # 繁体先入库，简体后入库（简体优先级更高，会覆盖繁体）
    if tw_text: extract_translations(tw_text, is_tw=True)
    if cn_text: extract_translations(cn_text, is_tw=False)

    # 2. 对英文骨架进行精准替换
    out_lines = []
    replaced_count = 0
    
    for line in en_text.splitlines():
        # 寻找英文本本中的键值对
        m = re.search(r'^\s*\[([A-Za-z0-9_\.\[\]]+)\]\s*=\s*"([^"]*)"', line)
        if m:
            key = m.group(1)
            # 如果在字典里找到了对应的翻译
            if key in translations:
                # 只替换双引号里面的内容，保留前后的缩进、等号和逗号
                line = re.sub(r'(=\s*")[^"]*(")', r'\g<1>' + translations[key] + r'\g<2>', line)
                replaced_count += 1
                
        out_lines.append(line)

    # 3. 输出保存
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write("\n".join(out_lines))
        
    print(f"🎉 成功替换了 {replaced_count} 条随机附魔属性！")
    print(f"🛡️ 类似 \"MHP + %d\" 这样不带汉字的特殊词条也被完美保留。")

if __name__ == "__main__":
    merge_randomoption()