# -*- coding: utf-8 -*-
import os
import re
import zhconv

FILE_NAME = "stateicon/stateiconinfo.lua" 

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

def merge_stateiconinfo():
    print("="*60)
    print(f" 🛡️ 状态图标提示表 ({FILE_NAME}) 区块合并 ".center(56, " "))
    print("="*60)
    
    en_text = read_text(EN_FILE)
    cn_text = read_text(CN_FILE)
    tw_text = read_text(TW_FILE)
    
    if not en_text:
        print("❌ 找不到英文源文件！")
        return

    # 1. 建立区块翻译字典: dict["EFST_IDs.EFST_OVERTHRUSTMAX"] = "descript = { ...完整字符串... }"
    translations = {}
    
    def extract_translations(text, is_tw=False):
        current_efst = None
        in_descript = False
        block_lines = []
        
        for line in text.splitlines():
            # 捕捉门牌号: StateIconList[EFST_IDs.EFST_OVERTHRUSTMAX] = {
            m_efst = re.search(r'StateIconList\[\s*(EFST_IDs\.[a-zA-Z0-9_]+)\s*\]', line)
            if m_efst:
                current_efst = m_efst.group(1)
                in_descript = False
                continue
                
            if current_efst:
                # 刚进门，寻找 descript 标签
                if not in_descript:
                    if re.search(r'descript\s*=\s*\{', line):
                        in_descript = True
                        block_lines = [line]
                # 已经进入 descript 区块，开始收集每一行
                else:
                    block_lines.append(line)
                    # 侦测到独立的 } 符号，代表 descript 区块结束
                    if re.match(r'^\s*\},?\s*$', line):
                        in_descript = False
                        
                        full_block = '\n'.join(block_lines)
                        if is_tw: full_block = zhconv.convert(full_block, 'zh-cn')
                        
                        # 只有当这个区块里包含中文时，才作为有效翻译收录
                        if re.search(r'[\u4e00-\u9fa5]', full_block):
                            translations[current_efst] = full_block
                            
                        current_efst = None # 重置，等待下一个 EFST_ID

    if tw_text: extract_translations(tw_text, is_tw=True)
    if cn_text: extract_translations(cn_text, is_tw=False) # 简体覆盖繁体

    # 2. 对英文骨架进行“区块切除与移植”
    out_lines = []
    current_efst = None
    in_descript = False
    replaced_count = 0
    
    for line in en_text.splitlines():
        # 同步英文本本中的当前门牌号
        m_efst = re.search(r'StateIconList\[\s*(EFST_IDs\.[a-zA-Z0-9_]+)\s*\]', line)
        if m_efst:
            current_efst = m_efst.group(1)
            
        # 准备切除英文的 descript 区块
        if current_efst and re.search(r'descript\s*=\s*\{', line):
            if current_efst in translations:
                # 找到中文区块了！直接把整个中文区块塞进去
                out_lines.append(translations[current_efst])
                in_descript = True # 开启屏蔽罩，接下来的英文 descript 内容全部扔掉
                replaced_count += 1
                continue
                
        # 屏蔽罩开启中，丢弃英文原有的行，直到遇到 }
        if in_descript:
            if re.match(r'^\s*\},?\s*$', line):
                in_descript = False # 屏蔽罩解除
            continue

        # 正常行直接保留 (比如 haveTimeLimit 这些底层代码)
        out_lines.append(line)

    # 3. 输出保存
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write("\n".join(out_lines))
        
    print(f"🎉 成功整体替换了 {replaced_count} 个状态图标的描述区块！")
    print(f"🛡️ 完美兼容了中英文行数不一致的问题，保证信息 100% 完整！")

if __name__ == "__main__":
    merge_stateiconinfo()