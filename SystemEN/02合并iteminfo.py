# -*- coding: utf-8 -*-
import os
import re
import zhconv

FILE_NAME = "luafiles514/itemInfo.lua" 
FILE_NAME_2 = "luafiles514/iteminfo_2.lua" 

EN_FILE = os.path.join("en_systemEN", FILE_NAME)
OUT_FILE = os.path.join("systemEN", FILE_NAME)

SOURCE_FILES = [
    (os.path.join("tw_systemEN", FILE_NAME), True),
    (os.path.join("cn_systemEN", FILE_NAME), False),
    (os.path.join("cn_systemEN", FILE_NAME_2), False)
]

def read_text(filepath, is_tw=False):
    if not os.path.exists(filepath): return ""
    
    # 1. 首先尝试纯净的 UTF-8 (以防文件是被 Github 等现代工具转码过的)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        pass # 不是 UTF-8，进入强硬的 ANSI 模式
        
    # 2. 强硬的 ANSI 锁定模式
    if is_tw:
        # 台湾文件：绝对锁定 Big5，防止被误认为 GBK 而产生“狝耿”现象
        with open(filepath, 'r', encoding='big5', errors='ignore') as f:
            return f.read()
    else:
        # EN 和 CN 文件：绝对锁定 GBK，透传韩文材质字节！
        with open(filepath, 'r', encoding='gbk', errors='ignore') as f:
            return f.read()

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fa5]', text))

def extract_string_field(block_str, field_name):
    pattern = re.compile(rf'^[ \t]*{field_name}\s*=\s*(?:(\[=\[.*?\]=\])|("[^"\\]*(?:\\.[^"\\]*)*"))', re.MULTILINE | re.DOTALL)
    m = pattern.search(block_str)
    if m:
        return m.group(1) or m.group(2)
    return None

def extract_table_field(block_str, field_name):
    pattern = re.compile(rf'^[ \t]*{field_name}\s*=\s*[\r\n]*\s*\{{', re.MULTILINE)
    m = pattern.search(block_str)
    if not m: return None
    
    start_idx = m.end() - 1
    count = 0
    in_raw = False
    in_str = False
    escape = False
    end_idx = -1

    for i in range(start_idx, len(block_str)):
        char = block_str[i]
        if not in_raw and not in_str:
            if block_str[i:i+3] == '[=[':
                in_raw = True
            elif char == '"':
                in_str = True
            elif char == '{':
                count += 1
            elif char == '}':
                count -= 1
                if count == 0:
                    end_idx = i
                    break
        elif in_raw:
            if block_str[i:i+3] == ']=]':
                in_raw = False
        elif in_str:
            if escape: escape = False
            elif char == '\\': escape = True
            elif char == '"': in_str = False

    if end_idx != -1:
        return block_str[start_idx : end_idx+1]
    return None

def replace_string_field(block_str, field_name, new_val_str):
    pattern = re.compile(rf'^([ \t]*{field_name}\s*=\s*)(?:\[=\[.*?\]=\]|"[^"\\]*(?:\\.[^"\\]*)*")', re.MULTILINE | re.DOTALL)
    m = pattern.search(block_str)
    if m:
        return block_str[:m.start(1)] + m.group(1) + new_val_str + block_str[m.end():]
    return block_str

def replace_table_field(block_str, field_name, new_val_str):
    pattern = re.compile(rf'^[ \t]*{field_name}\s*=\s*[\r\n]*\s*\{{', re.MULTILINE)
    m = pattern.search(block_str)
    if not m: return block_str
    
    start_idx = m.end() - 1
    count = 0
    in_raw = False
    in_str = False
    escape = False
    end_idx = -1

    for i in range(start_idx, len(block_str)):
        char = block_str[i]
        if not in_raw and not in_str:
            if block_str[i:i+3] == '[=[': in_raw = True
            elif char == '"': in_str = True
            elif char == '{': count += 1
            elif char == '}':
                count -= 1
                if count == 0:
                    end_idx = i
                    break
        elif in_raw:
            if block_str[i:i+3] == ']=]': in_raw = False
        elif in_str:
            if escape: escape = False
            elif char == '\\': escape = True
            elif char == '"': in_str = False

    if end_idx != -1:
        return block_str[:start_idx] + new_val_str + block_str[end_idx+1:]
    return block_str

def merge_iteminfo():
    print("="*60)
    print(f" 🎒 RO 终极物品信息表 (硬核 GBK 字节透传版) ".center(56, " "))
    print("="*60)
    
    en_text = read_text(EN_FILE, is_tw=False)
    if not en_text:
        print("❌ 找不到英文源文件！")
        return

    translations = {}
    
    # 1. 读取并提取中文词库
    for filepath, is_tw in SOURCE_FILES:
        text = read_text(filepath, is_tw=is_tw)
        if not text: continue
        print(f"🔄 读取词库并提取翻译: {filepath} ...")
        
        matches = list(re.finditer(r'^[ \t]*\[(\d+)\]\s*=', text, re.MULTILINE))
        for i, m in enumerate(matches):
            qid = m.group(1)
            start_pos = m.start()
            end_pos = matches[i+1].start() if i+1 < len(matches) else len(text)
            block_str = text[start_pos:end_pos]
            
            if qid not in translations: translations[qid] = {}
            
            for field in ['unidentifiedDisplayName', 'identifiedDisplayName']:
                val = extract_string_field(block_str, field)
                if val and has_chinese(val):
                    if is_tw: val = zhconv.convert(val, 'zh-cn')
                    translations[qid][field] = val
                    
            for field in ['unidentifiedDescriptionName', 'identifiedDescriptionName']:
                val = extract_table_field(block_str, field)
                if val and has_chinese(val):
                    if is_tw: val = zhconv.convert(val, 'zh-cn')
                    translations[qid][field] = val

    print(f"⚙️ 向 EN 骨架注入翻译数据 (共收集 {len(translations)} 词条)，正在精密替换...")
    
    # 2. 对英文骨架进行切片和原样拼装
    out_chunks = []
    replaced_names = 0
    replaced_descs = 0
    
    matches = list(re.finditer(r'^[ \t]*\[(\d+)\]\s*=', en_text, re.MULTILINE))
    
    if matches:
        out_chunks.append(en_text[:matches[0].start()])
        
    for i, m in enumerate(matches):
        qid = m.group(1)
        start_pos = m.start()
        end_pos = matches[i+1].start() if i+1 < len(matches) else len(en_text)
        en_block_str = en_text[start_pos:end_pos]
        
        if qid in translations:
            trans = translations[qid]
            for field in ['unidentifiedDisplayName', 'identifiedDisplayName']:
                if field in trans:
                    new_block = replace_string_field(en_block_str, field, trans[field])
                    if new_block != en_block_str:
                        en_block_str = new_block
                        replaced_names += 1
                        
            for field in ['unidentifiedDescriptionName', 'identifiedDescriptionName']:
                if field in trans:
                    new_block = replace_table_field(en_block_str, field, trans[field])
                    if new_block != en_block_str:
                        en_block_str = new_block
                        replaced_descs += 1
                        
        out_chunks.append(en_block_str)
        
    out_text = "".join(out_chunks)

    # 3. 终极强硬输出：只写 GBK！
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write(out_text)
        
    print("\n" + "="*60)
    print(" 📊 开始执行系统级数据审计... ")
    print("="*60)
    
    en_ids = set(re.findall(r'^[ \t]*\[(\d+)\]\s*=', en_text, re.MULTILINE))
    out_ids = set(re.findall(r'^[ \t]*\[(\d+)\]\s*=', out_text, re.MULTILINE))
    
    print(f"📄 原始 EN 包含物品总数: {len(en_ids)}")
    print(f"📁 最终生成 包含物品总数: {len(out_ids)}")
    
    if len(out_ids) >= len(en_ids) and len(en_ids) > 0:
        print("✅ 审计通过！物品数量完美一致！")
    else:
        print("❌ 警告！发现物品丢失！")

    print(f"\n✅ 成功替换了 {replaced_names} 处物品名称！")
    print(f"✅ 成功替换了 {replaced_descs} 处物品说明区块！")
    print(f"🛡️ 终极编码策略：TW严格Big5解码 / 统一强力GBK字节透传 已生效！")
    print("="*60)

if __name__ == "__main__":
    merge_iteminfo()