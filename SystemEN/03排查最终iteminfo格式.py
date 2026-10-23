# -*- coding: utf-8 -*-
import os
import re

# 🎯 在这里配置你需要质检的文件路径
TARGET_FILE = os.path.join("systemEN/luafiles514", "itemInfo.lua")

def fix_lua_syntax(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 找不到文件: {file_path}")
        return

    print("="*60)
    print(f" 🛠️ 启动 Lua 语法自动修复引擎 ".center(56, " "))
    print(f" 目标文件: {file_path} ".center(58, " "))
    print("="*60)

    # 使用之前合并脚本采用的 GB18030 无损读取
    try:
        with open(file_path, 'r', encoding='gb18030') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return

    fixed_lines = []
    in_raw_string = False
    fix_quote_count = 0
    
    for i, line in enumerate(lines):
        original_line = line
        
        # 维护多行原始字符串 [=[ ]=] 的状态（跳过这些行不做奇偶校验）
        if not in_raw_string:
            if '[=[' in line and ']=]' not in line:
                in_raw_string = True
        else:
            if ']=]' in line:
                in_raw_string = False
            fixed_lines.append(original_line)
            continue

        if not in_raw_string:
            # 清理转义的引号 (\") 和行内的多行字符串，以便准确计算真实的双引号数量
            clean_line = re.sub(r'\\.', '', line)
            clean_line = re.sub(r'\[=\[.*?\]=\]', '', clean_line)
            
            quote_count = clean_line.count('"')
            
            # 🚨 核心逻辑：如果一行中的双引号数量是奇数，说明字符串未闭合！
            if quote_count % 2 != 0:
                # 模式1：原本的右引号变成了 '?'，例如： "文本内容?, 
                # 正则解析：寻找行尾（忽略可能存在的空格、逗号、右大括号）的最后一个 '?'
                m_question = re.search(r'\?(\s*\}?\s*,?\s*)$', line)
                if m_question:
                    # 将那个作恶的 '?' 替换为 '"'
                    line = line[:m_question.start()] + '"' + line[m_question.start()+1:]
                    fix_quote_count += 1
                    print(f"🔧 [第 {i+1} 行] 修复 ? 为 \":")
                    print(f"   🔴 原始: {original_line.strip()}")
                    print(f"   🟢 修复: {line.strip()}\n")
                else:
                    # 模式2：完全丢失了右引号，例如： "文本内容,
                    # 我们在行尾（逗号、右大括号之前）强行补上 '"'
                    m_end = re.search(r'(\s*\}?\s*,?\s*)$', line)
                    if m_end:
                        line = line[:m_end.start()] + '"' + line[m_end.start():]
                        fix_quote_count += 1
                        print(f"🔧 [第 {i+1} 行] 强行补充缺失的 \":")
                        print(f"   🔴 原始: {original_line.strip()}")
                        print(f"   🟢 修复: {line.strip()}\n")

        fixed_lines.append(line)

    # ==========================================
    # 🔍 全局格式质检：大括号 { } 配对验证
    # ==========================================
    full_text = "".join(fixed_lines)
    # 剥离所有字符串和注释，只看代码骨架
    clean_text = re.sub(r'\[=\[.*?\]=\]', '', full_text, flags=re.DOTALL)
    clean_text = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', '', clean_text)
    clean_text = re.sub(r'--.*', '', clean_text)
    
    brace_balance = clean_text.count('{') - clean_text.count('}')

    # 保存修复后的文件 (原位覆盖)
    with open(file_path, 'w', encoding='gb18030') as f:
        f.writelines(fixed_lines)

    print("="*60)
    print(f"🎉 修复质检完成！")
    print(f"🩹 共成功修复了 {fix_quote_count} 处未闭合的字符串错误。")
    if brace_balance == 0:
        print("✅ 全局大括号 { } 校验通过，未发现结构性缺失！")
    else:
        print(f"⚠️ 警告: 全局大括号 {{ }} 数量不匹配！差值为: {brace_balance} (可能是官方源码中存在多余或遗漏的括号)")
    print("="*60)

if __name__ == "__main__":
    fix_lua_syntax(TARGET_FILE)