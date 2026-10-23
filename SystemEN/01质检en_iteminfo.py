# -*- coding: utf-8 -*-
import os
import re

# 🎯 目标文件路径 (根据你的报错日志，我已经为你适配了路径)
TARGET_FILE = os.path.join("en_systemEN", "luafiles514", "itemInfo.lua")

def fix_lua_syntax(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 找不到文件: {file_path}")
        return

    print("="*60)
    print(f" 🛠️ 启动 Lua 语法修复引擎 (无损字节装甲版) ".center(56, " "))
    print(f" 目标文件: {file_path} ".center(58, " "))
    print("="*60)

    # ==========================================
    # 🚀 核心黑科技：智能编码嗅探 + 字节装甲兜底
    # ==========================================
    detected_encoding = None
    lines = []
    
    # 1. 优先尝试正常解码 (韩国 CP949 优先)
    encodings_to_try = ['cp949', 'utf-8-sig', 'gb18030', 'big5']
    
    for enc in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                lines = f.readlines()
            detected_encoding = enc
            print(f"✅ 成功识别文件编码: [{enc}]")
            break
        except UnicodeDecodeError:
            continue
            
    # 2. 如果常规解码全军覆没，启动终极字节装甲 (surrogateescape)
    if not detected_encoding:
        print("⚠️ 常规编码无法完全解析，已启动 [无损字节装甲 (surrogateescape)] 保护底层数据...")
        detected_encoding = 'utf-8-surrogate'
        # errors='surrogateescape' 会将所有无法解码的字节转化为特殊的 Unicode 代理对，写入时完美还原。
        with open(file_path, 'r', encoding='utf-8', errors='surrogateescape') as f:
            lines = f.readlines()

    fixed_lines = []
    in_raw_string = False
    fix_quote_count = 0
    
    for i, original_line in enumerate(lines):
        line = original_line
        
        if not in_raw_string:
            if '[=[' in line and ']=]' not in line:
                in_raw_string = True
            
            # 逐字符状态机引擎
            quote_count = 0
            in_str = False
            j = 0
            while j < len(line):
                if not in_str and line[j:j+3] == '[=[':
                    idx = line.find(']=]', j)
                    if idx != -1:
                        j = idx + 3
                        continue
                    else:
                        break 
                        
                if not in_str and line[j:j+2] == '--':
                    break 
                    
                if line[j] == '"':
                    in_str = not in_str
                    quote_count += 1
                    
                elif line[j] == '\\' and in_str:
                    j += 2 
                    continue
                    
                j += 1

            # 🚨 判定：双引号数量为奇数
            if quote_count % 2 != 0:
                m = re.search(r'([\?？]?)([\s\}\,]*)$', original_line)
                if m:
                    if m.group(1):
                        line = original_line[:m.start(1)] + '"' + m.group(2)
                        action_msg = "替换退化乱码 ? 为 \""
                    else:
                        line = original_line[:m.start(2)] + '"' + m.group(2)
                        action_msg = "在尾部强行补充缺失的 \""
                        
                    fix_quote_count += 1
                    print(f"🔧 [第 {i+1} 行] {action_msg}:")
                    print(f"   🔴 原始: {original_line.strip()}")
                    print(f"   🟢 修复: {line.strip()}\n")

        else:
            if ']=]' in line:
                in_raw_string = False

        fixed_lines.append(line)

    # 全局格式质检
    full_text = "".join(fixed_lines)
    clean_text = re.sub(r'\[=\[.*?\]=\]', '', full_text, flags=re.DOTALL)
    clean_text = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', '', clean_text)
    clean_text = re.sub(r'--.*', '', clean_text)
    brace_balance = clean_text.count('{') - clean_text.count('}')

    # ==========================================
    # 💾 无损保存：原路返回底层字节
    # ==========================================
    if detected_encoding == 'utf-8-surrogate':
        with open(file_path, 'w', encoding='utf-8', errors='surrogateescape') as f:
            f.writelines(fixed_lines)
    else:
        with open(file_path, 'w', encoding=detected_encoding) as f:
            f.writelines(fixed_lines)

    print("="*60)
    print(f"🎉 修复质检完成！")
    print(f"🩹 共成功修复了 {fix_quote_count} 处真正的未闭合错误。")
    if brace_balance == 0:
        print("✅ 全局大括号 { } 校验通过，代码结构完美健康！")
    else:
        print(f"⚠️ 警告: 全局大括号 {{ }} 数量不匹配！差值为: {brace_balance}")
    print("="*60)

if __name__ == "__main__":
    fix_lua_syntax(TARGET_FILE)