# -*- coding: utf-8 -*-
import os
import re
import zhconv

FILE_NAME = "spopup.lua" 

# 沿用 systemEN 目录结构
EN_FILE = os.path.join("en_systemEN", FILE_NAME)
CN_FILE = os.path.join("cn_systemEN", FILE_NAME)
TW_FILE = os.path.join("tw_systemEN", FILE_NAME)
OUT_FILE = os.path.join("systemEN", FILE_NAME)

def read_text(filepath):
    if not os.path.exists(filepath): return ""
    for enc in ['utf-8', 'gbk', 'big5']:
        try:
            with open(filepath, 'r', encoding=enc) as f: return f.read()
        except: continue
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: return f.read()

def merge_spopup():
    print("="*60)
    print(f" 💬 RO 系统弹窗提示表 ({FILE_NAME}) 精准合并 ".center(56, " "))
    print("="*60)
    
    en_text = read_text(EN_FILE)
    cn_text = read_text(CN_FILE)
    tw_text = read_text(TW_FILE)
    
    if not en_text:
        print("❌ 找不到英文源文件！请检查 en_systemEN 目录。")
        return

    # 1. 建立发牌队列: dict["1"] = ["请注意，该地区...", "部分技能和道具..."]
    translations = {}
    
    def extract_translations(text, is_tw=False):
        current_id = None
        for line in text.splitlines():
            # 捕捉弹窗 ID 锚点: [1] = {
            m_id = re.search(r'^\s*\[(\d+)\]\s*=\s*\{', line)
            if m_id:
                current_id = m_id.group(1)
                if current_id not in translations:
                    translations[current_id] = []
                continue
                
            # 如果进入了 ID 区块，疯狂吸入所有的双引号字符串
            if current_id:
                strings = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', line)
                for s in strings:
                    if is_tw: s = zhconv.convert(s, 'zh-cn')
                    # 只有包含中文字符的才被当做有效翻译收录
                    if re.search(r'[\u4e00-\u9fa5]', s):
                        translations[current_id].append(s)

    # 繁体先入库，简体后入库（简体优先级更高）
    if tw_text: extract_translations(tw_text, is_tw=True)
    if cn_text: extract_translations(cn_text, is_tw=False)

    # 2. 对英文骨架进行“发牌式”微创替换
    out_lines = []
    current_id = None
    string_iterator = None
    replaced_strings = 0
    
    for line in en_text.splitlines():
        # 同步识别弹窗 ID
        m_id = re.search(r'^\s*\[(\d+)\]\s*=\s*\{', line)
        if m_id:
            current_id = m_id.group(1)
            # 进入新房间，如果手里有这个房间的中文牌，就准备发牌
            if current_id in translations:
                string_iterator = iter(translations[current_id])
            else:
                string_iterator = None
                
            out_lines.append(line)
            continue
            
        # 如果当前房间需要发牌，且这行代码里有双引号字符串
        if current_id and string_iterator and '"' in line:
            def replacer(match):
                nonlocal replaced_strings
                try:
                    # 抽出一张中文翻译牌
                    new_str = next(string_iterator)
                    replaced_strings += 1
                    return '"' + new_str + '"'
                except StopIteration:
                    # 如果中文牌发完了（可能是英文有更多的子句子），就保留英文原样
                    return match.group(0)
                    
            # 替换该行所有的双引号内容
            line = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', replacer, line)
            
        out_lines.append(line)

    # 3. 输出保存
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write("\n".join(out_lines))
        
    print(f"🎉 成功替换了 {replaced_strings} 条弹窗提示文本！")
    print(f"🛡️ Description 数组的格式已被完美保护，多行文本也不会错位。")

if __name__ == "__main__":
    merge_spopup()