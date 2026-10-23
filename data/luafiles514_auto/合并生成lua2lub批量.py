# -*- coding: utf-8 -*-
import os
import re
import subprocess
import zhconv

# ================= 1. 全局配置区 =================
EN_DIR = "en_lua files"
CN_DIR = "cn_lua files"
TW_DIR = "tw_lua files"
OUT_DIR = "lua files"
LOG_FILE = "merge_validation.log" # 质检报告日志

LUAC_PATH = "luac5.1.exe"

PATH_MAPPING_CN = {"korea": "china", "_kr": "_ch", "korean": "chinese"}
PATH_MAPPING_TW = {"korea": "taiwan", "_kr": "_tw", "korean": "taiwanese"}
# =================================================

def read_lua_text(filepath):
    if not os.path.exists(filepath): return ""
    for enc in ['utf-8', 'utf-8-sig', 'gbk', 'big5']:
        try:
            with open(filepath, 'r', encoding=enc) as f: return f.read()
        except: continue
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: return f.read()

def compile_to_lub(lua_content, out_filepath):
    temp_lua = out_filepath.replace('.lub', '.temp.lua')
    if not temp_lua.endswith('.lua'): temp_lua += '.lua'
    os.makedirs(os.path.dirname(out_filepath), exist_ok=True)
    with open(temp_lua, 'w', encoding='gbk', errors='ignore') as f: f.write(lua_content)
    if out_filepath.endswith('.lua'):
        os.replace(temp_lua, out_filepath)
        return True
    cmd = [LUAC_PATH, '-o', out_filepath, temp_lua]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if os.path.exists(temp_lua): os.remove(temp_lua)
    return result.returncode == 0

def map_path(rel_path, mapping_dict):
    mapped = rel_path
    for kr_str, local_str in mapping_dict.items():
        mapped = re.sub(re.escape(kr_str), local_str, mapped, flags=re.IGNORECASE)
    return mapped

def get_fingerprint(line):
    """提取代码骨架指纹，将字符串替换为 <STR>"""
    clean = re.sub(r'--.*$', '', line) # 去除注释
    return re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', '"<STR>"', clean.strip())

def parse_lua_structure(text, is_tw=False):
    """智能解析引擎：提取包含中文的行，记录上下文和骨架指纹"""
    if not text: return {}
    
    db = {}
    stack = ["ROOT"]
    
    for line in text.splitlines():
        clean = line.strip()
        if not clean or clean.startswith('--'): continue
        
        # 追踪进入 Table
        m_open = re.search(r'([a-zA-Z0-9_]+|\[\s*"?.*?"?\s*\])\s*=\s*\{', clean)
        if m_open: stack.append(m_open.group(1))
            
        # 追踪离开 Table
        if clean.startswith('}') or clean.startswith('},'):
            if len(stack) > 1: stack.pop()
            
        current_context = "->".join(stack)
        
        # 提取当前行的字符串
        strings = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', line)
        if strings:
            has_zh = False
            processed_strings = []
            for s in strings:
                if is_tw: s = zhconv.convert(s, 'zh-cn')
                processed_strings.append(s)
                # 只有当包含真正的中文字符时，才认为是有效翻译
                if re.search(r'[\u4e00-\u9fa5]', s): has_zh = True
                
            if has_zh:
                fp = get_fingerprint(line)
                if current_context not in db: db[current_context] = {}
                db[current_context][fp] = processed_strings
                
    return db

def validate_formatting(en_text, merged_text):
    """终极质检员：对比符号数量，确保代码结构未被破坏"""
    errors = []
    if en_text.count('{') != merged_text.count('{'):
        errors.append("左大括号 '{' 数量不匹配！")
    if en_text.count('}') != merged_text.count('}'):
        errors.append("右大括号 '}' 数量不匹配！")
    if en_text.count('"') != merged_text.count('"'):
        errors.append("双引号 '\"' 数量不匹配，可能存在字符串未闭合！")
    return errors

def smart_merge(en_text, cn_text, tw_text, filename):
    if not en_text: return "", []
    
    # 1. 扫描中文和繁体，建立带有上下文和指纹的数据库
    cn_db = parse_lua_structure(cn_text, is_tw=False)
    tw_db = parse_lua_structure(tw_text, is_tw=True)
    
    merged_lines = []
    stack = ["ROOT"]
    
    # 2. 遍历英文骨架，进行指纹比对和注入
    for line in en_text.splitlines():
        clean = line.strip()
        
        m_open = re.search(r'([a-zA-Z0-9_]+|\[\s*"?.*?"?\s*\])\s*=\s*\{', clean)
        if m_open and not clean.startswith('--'): stack.append(m_open.group(1))
            
        if clean.startswith('}') or clean.startswith('},'):
            if len(stack) > 1: stack.pop()
            
        current_context = "->".join(stack)
        
        if '"' in line:
            fp = get_fingerprint(line)
            trans_strings = None
            
            # 优先检查简中数据库是否有对应的指纹
            if current_context in cn_db and fp in cn_db[current_context]:
                trans_strings = cn_db[current_context][fp]
            # 其次检查繁体数据库
            elif current_context in tw_db and fp in tw_db[current_context]:
                trans_strings = tw_db[current_context][fp]
                
            if trans_strings:
                # 找到匹配的翻译！安全替换
                iterator = iter(trans_strings)
                def replacer(match):
                    try: return '"' + next(iterator) + '"'
                    except StopIteration: return match.group(0)
                line = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', replacer, line)

        merged_lines.append(line)
        
    merged_text = '\n'.join(merged_lines)
    
    # 3. 执行最终质检
    validation_errors = validate_formatting(en_text, merged_text)
    
    return merged_text, validation_errors

def run_v4_pipeline():
    print("="*70)
    print(" 🤖 RO 客户端本地化流水线 V4 (智能特征质检版) ".center(66, " "))
    print("="*70)
    
    total = 0
    success = 0
    warnings = 0
    
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write("=== V4 合并质检报告 ===\n\n")
        
        for root, dirs, files in os.walk(EN_DIR):
            for file in files:
                if not (file.endswith('.lua') or file.endswith('.lub')): continue
                
                total += 1
                rel_path = os.path.relpath(os.path.join(root, file), EN_DIR)
                en_filepath = os.path.join(EN_DIR, rel_path)
                out_filepath = os.path.join(OUT_DIR, rel_path)
                
                cn_rel_path = map_path(rel_path, PATH_MAPPING_CN).replace('.lub', '.lua')
                tw_rel_path = map_path(rel_path, PATH_MAPPING_TW).replace('.lub', '.lua')
                
                en_text = read_lua_text(en_filepath)
                cn_text = read_lua_text(os.path.join(CN_DIR, cn_rel_path))
                tw_text = read_lua_text(os.path.join(TW_DIR, tw_rel_path))
                
                print(f"🔄 处理: {rel_path} ...", end="")
                
                merged_text, errors = smart_merge(en_text, cn_text, tw_text, rel_path)
                
                if errors:
                    print(" [⚠️ 质检警告]")
                    warnings += 1
                    log.write(f"[警告] 文件: {rel_path}\n")
                    for err in errors: log.write(f"  - {err}\n")
                    log.write("\n")
                else:
                    if compile_to_lub(merged_text, out_filepath):
                        print(" [✅ 通过质检 & 编译成功]")
                        success += 1
                    else:
                        print(" [❌ 编译失败]")

    print("="*70)
    print(f"🎉 V4 智能作业完成！")
    print(f"总计处理文件: {total} 个")
    print(f"完美通过并编译: {success} 个")
    if warnings > 0:
        print(f"⚠️ 发现 {warnings} 个文件存在格式警告，详情请查看 {LOG_FILE}！")
    print("="*70)

if __name__ == "__main__":
    run_v4_pipeline()