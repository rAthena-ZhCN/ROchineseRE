# -*- coding: utf-8 -*-
import os
import re
import zhconv

FILE_NAME = "itemreform/ItemReformSystem.lua" 

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

def merge_item_reform():
    print("="*60)
    print(f" 🛡️ 装备升级系统 ({FILE_NAME}) 双重锚点合并 ".center(56, " "))
    print("="*60)
    
    en_text = read_text(EN_FILE)
    cn_text = read_text(CN_FILE)
    tw_text = read_text(TW_FILE)
    
    if not en_text:
        print("❌ 找不到英文源文件！")
        return

    # 1. 建立双重锚点字典: dict[("Avd_Knife", "明风扁_")] = "InformationString = { ... }"
    translations = {}
    
    def extract_translations(text, is_tw=False):
        # 使用正则表达式按区块分割：[数字] = { 
        # parts 数组里，奇数项是头部如 "[3] = {"，偶数项是里面的具体内容
        parts = re.split(r'^(\s*\[\d+\]\s*=\s*\{)', text, flags=re.MULTILINE)
        
        for i in range(2, len(parts), 2):
            block = parts[i]
            
            # 提取联合锚点：源道具与目标道具
            base_m = re.search(r'BaseItem\s*=\s*"([^"]+)"', block)
            res_m = re.search(r'ResultItem\s*=\s*"([^"]+)"', block)
            # 提取整个信息字符串区块
            info_m = re.search(r'(InformationString\s*=\s*\{[^}]+\})', block)
            
            if base_m and res_m and info_m:
                base_item = base_m.group(1)
                result_item = res_m.group(1)
                info_str = info_m.group(1)
                
                if is_tw: info_str = zhconv.convert(info_str, 'zh-cn')
                
                # 只有包含中文才收录，防止将乱码区块错误录入
                if re.search(r'[\u4e00-\u9fa5]', info_str):
                    translations[(base_item, result_item)] = info_str

    # 繁体先入库，简体后入库（简体优先级更高）
    if tw_text: extract_translations(tw_text, is_tw=True)
    if cn_text: extract_translations(cn_text, is_tw=False)

    # 2. 对英文骨架进行手术替换
    parts = re.split(r'^(\s*\[\d+\]\s*=\s*\{)', en_text, flags=re.MULTILINE)
    replaced_count = 0
    
    for i in range(2, len(parts), 2):
        block = parts[i]
        
        # 寻找英文区块的联合锚点
        base_m = re.search(r'BaseItem\s*=\s*"([^"]+)"', block)
        res_m = re.search(r'ResultItem\s*=\s*"([^"]+)"', block)
        
        if base_m and res_m:
            key = (base_m.group(1), res_m.group(1))
            
            # 如果匹配上了，就执行 InformationString 整体掉包
            if key in translations:
                new_info_str = translations[key]
                # 使用 lambda 防止 \n 被强行换行
                new_block = re.sub(r'InformationString\s*=\s*\{[^}]+\}', 
                                   lambda m: new_info_str, 
                                   block, count=1)
                if new_block != block:
                    parts[i] = new_block
                    replaced_count += 1

    out_text = "".join(parts)

    # 3. 输出保存
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write(out_text)
        
    print(f"🎉 成功匹配并替换了 {replaced_count} 条装备升级说明！")
    print(f"🛡️ 索引号 ([1], [2]) 错乱已免疫！")
    print(f"🛡️ Material 材料区的韩文乱码已被完美隔离！")

if __name__ == "__main__":
    merge_item_reform()