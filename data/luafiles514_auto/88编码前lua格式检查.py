# -*- coding: utf-8 -*-
import os
import re
import sys

# 🎯 填写你需要遍历的主文件夹路径
TARGET_DIR = "lua files"

def split_code_comment(line):
    """安全剥离注释"""
    in_str = False
    escape = False
    for i in range(len(line)):
        c = line[i]
        if escape: escape = False
        elif c == '\\': escape = True
        elif c == '"': in_str = not in_str
        elif not in_str and line[i:i+2] == '--':
            return line[:i], line[i:]
    return line, ""

def fix_unclosed_quote(line):
    """X光级别的未闭合引号修复逻辑"""
    last_quote = -1
    in_str = False
    escape = False
    for i, c in enumerate(line):
        if escape: escape = False
        elif c == '\\': escape = True
        elif c == '"':
            in_str = not in_str
            last_quote = i

    last_corrupt = -1
    for i in range(len(line)-1, -1, -1):
        if line[i] in ('?', '？') or '\udc00' <= line[i] <= '\udcff':
            last_corrupt = i
            break

    if last_corrupt > last_quote:
        return line[:last_corrupt] + '"' + line[last_corrupt+1:], "替换内部退化乱码 ? 为 \""

    m = re.search(r'([\s\}\,]*)$', line)
    if m and m.start() > last_quote:
        return line[:m.start()] + '"' + line[m.start():], "在尾部符号前补充 \""

    return line.rstrip() + '"\n', "在行尾强行补充 \""

def ask_user(prompt_msg):
    """处理用户交互输入"""
    while True:
        choice = input(f"{prompt_msg} [y:修复 / n:跳过 / q:终止程序]: ").strip().lower()
        if choice in ('y', 'n', 'q'):
            if choice == 'q':
                print("\n🛑 收到终止指令，安全退出程序。")
                sys.exit(0)
            return choice == 'y'
        print("⚠️ 输入无效，请输入 y, n 或 q。")

def process_lua_file(file_path):
    detected_encoding = None
    lines = []
    
    encodings_to_try = ['cp949', 'utf-8-sig', 'gb18030', 'big5']
    for enc in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                lines = f.readlines()
            detected_encoding = enc
            break
        except UnicodeDecodeError:
            continue
            
    if not detected_encoding:
        detected_encoding = 'utf-8-surrogate'
        with open(file_path, 'r', encoding='utf-8', errors='surrogateescape') as f:
            lines = f.readlines()

    fixed_lines = []
    in_raw_string = False
    brace_balance = 0
    
    file_modified = False
    fix_quote_count = 0
    fix_brace_count = 0

    for i, original_line in enumerate(lines):
        line = original_line
        
        if not in_raw_string:
            if '[=[' in line and ']=]' not in line:
                in_raw_string = True
        else:
            if ']=]' in line:
                in_raw_string = False
            fixed_lines.append(original_line)
            continue

        if not in_raw_string:
            code_part, comment_part = split_code_comment(line)
            
            # --- 1. 双引号未闭合侦测与交互 ---
            quote_count = 0
            escape = False
            for c in code_part:
                if escape: escape = False
                elif c == '\\': escape = True
                elif c == '"': quote_count += 1
                
            if quote_count % 2 != 0:
                proposed_code, msg = fix_unclosed_quote(code_part)
                proposed_line = proposed_code + comment_part
                
                print(f"\n" + "-"*60)
                print(f"🚨 [引号异常] 文件: {file_path} (第 {i+1} 行)")
                print(f"💡 诊断: {msg}")
                if i > 0:
                    print(f"   上文: {lines[i-1].strip()}")
                print(f"   🔴 原始: {original_line.strip()}")
                print(f"   🟢 建议: {proposed_line.strip()}")
                print("-" * 60)
                
                if ask_user("❓ 是否应用此引号修复?"):
                    line = proposed_line
                    file_modified = True
                    fix_quote_count += 1
                    print("✅ 已应用修复。")
                    code_part, comment_part = split_code_comment(line) # 更新用于后续括号统计
                else:
                    print("⏭️ 已跳过。")

            # --- 2. 智能大括号 { } 恢复侦测与交互 ---
            clean_code = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', '', code_part)
            
            if re.match(r'^[a-zA-Z0-9_]+\s*=', line) and brace_balance > 0:
                print(f"\n" + "-"*60)
                print(f"🚨 [结构断裂] 文件: {file_path} (第 {i+1} 行)")
                print(f"💡 诊断: 发现新的全局变量声明，但上一个模块似乎未闭合。")
                print(f"   当前缺失 '}}' 数量: {brace_balance}")
                if i > 0:
                    print(f"   上文: {lines[i-1].strip()}")
                print(f"   🔴 当前行: {original_line.strip()}")
                print(f"   🟢 建议: 在此行上方强行插入 {brace_balance} 个 '}}'")
                print("-" * 60)
                
                if ask_user("❓ 是否在上方补全缺失的 '}'?"):
                    for _ in range(brace_balance):
                        fixed_lines.append("}\n")
                    fix_brace_count += brace_balance
                    brace_balance = 0
                    file_modified = True
                    print("✅ 已补全大括号。")
                else:
                    print("⏭️ 已跳过 (大括号失衡状态将保留)。")
                
            open_b = clean_code.count('{')
            close_b = clean_code.count('}')
            brace_balance += (open_b - close_b)

        fixed_lines.append(line)

    # --- 3. EOF 大括号侦测与交互 ---
    if brace_balance > 0:
        print(f"\n" + "-"*60)
        print(f"🚨 [结尾未闭合] 文件: {file_path} (到达文件末尾)")
        print(f"💡 诊断: 文件已经结束，但大括号未完全闭合。")
        print(f"   当前缺失 '}}' 数量: {brace_balance}")
        print(f"   上文: {lines[-1].strip() if lines else '空文件'}")
        print(f"   🟢 建议: 在文件最末尾补全 {brace_balance} 个 '}}'")
        print("-" * 60)
        
        if ask_user("❓ 是否在文件末尾补全缺失的 '}'?"):
            for _ in range(brace_balance):
                fixed_lines.append("}\n")
            fix_brace_count += brace_balance
            file_modified = True
            print("✅ 已在末尾补全大括号。")
        else:
            print("⏭️ 已跳过。")

    # 4. 原样保存
    if file_modified:
        if detected_encoding == 'utf-8-surrogate':
            with open(file_path, 'w', encoding='utf-8', errors='surrogateescape') as f:
                f.writelines(fixed_lines)
        else:
            with open(file_path, 'w', encoding=detected_encoding) as f:
                f.writelines(fixed_lines)
                
    return file_modified, fix_quote_count, fix_brace_count

def run_interactive_fixer():
    print("="*60)
    print(f" 🚀 启动交互式 Lua 语法扫描与手术级修复机 ".center(50, " "))
    print("="*60)
    
    if not os.path.exists(TARGET_DIR):
        print(f"❌ 找不到目录: {TARGET_DIR}")
        return

    total_files = 0
    fixed_files = 0
    total_quotes = 0
    total_braces = 0

    for root, dirs, files in os.walk(TARGET_DIR):
        for file in files:
            if file.lower().endswith(".lua"):
                file_path = os.path.join(root, file)
                total_files += 1
                try:
                    is_fixed, qc, bc = process_lua_file(file_path)
                    if is_fixed:
                        fixed_files += 1
                        total_quotes += qc
                        total_braces += bc
                except Exception as e:
                    print(f"\n🔴 [异常跳过] {file_path}\n   ↳ {e}")

    print("\n" + "="*60)
    print(f"🎉 巡检完毕！共扫描 {total_files} 个 Lua 文件。")
    print(f"🩹 实际应用修复的文件数: {fixed_files} 个。")
    print(f"   - 修复引号: {total_quotes} 处")
    print(f"   - 补全括号: {total_braces} 处")
    print("="*60)
    print("✨ 你的文件已完成安全排雷，可以进行 lub 编译了！")

if __name__ == "__main__":
    run_interactive_fixer()