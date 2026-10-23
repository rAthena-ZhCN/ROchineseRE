# -*- coding: utf-8 -*-
import os
import re
import zhconv
import xml.etree.ElementTree as ET

# ================= 配置区 =================
EN_FILE = "en_pettalktable.xml"
TW_FILE = "tw_pettalktable.xml"
CN_FILE = "cn_pettalktable.xml"
OUT_FILE = "pettalktable.xml"
# ==========================================

def atbash_cipher(text):
    """
    解密 Gravity 官方的 Atbash 镜像加密
    """
    result = []
    for char in text:
        if 'a' <= char <= 'z':
            result.append(chr(ord('z') - (ord(char) - ord('a'))))
        elif 'A' <= char <= 'Z':
            result.append(chr(ord('Z') - (ord(char) - ord('A'))))
        else:
            result.append(char)
    return ''.join(result)

def read_and_decrypt_xml(filepath):
    """自适应读取 XML，并自动解密被官方加密的文件"""
    if not os.path.exists(filepath):
        return None
        
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'big5hkscs', 'big5', 'cp950']
    content = None
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue
            
    if not content:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
    # 侦测是否为 Atbash 加密（例如 <?cno 或者 <kzg...）
    if '<?cno' in content or '<kzg' in content or '<Nlm' in content:
        content = atbash_cipher(content)
        
    # 剔除 XML 头部声明，防止 ElementTree 因 encoding 报错
    content = re.sub(r'<\?xml.*?\?>', '', content).strip()
    return content

def has_chinese(text):
    """检测字符串中是否包含中文字符"""
    return bool(re.search(r'[\u4e00-\u9fa5]', text)) if text else False

def build_xpath_dict(element, path="", result_dict=None):
    """
    为 XML 树的每一个节点生成独一无二的 XPath
    用于完美解决同一个标签（如 <msg>）出现多次的替换问题
    """
    if result_dict is None:
        result_dict = {}
    tag_counts = {}
    
    for child in element:
        tag = child.tag
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
        idx = tag_counts[tag]
        # 生成类似 root/pet[1]/msg[2] 的唯一路径
        child_path = f"{path}/{tag}[{idx}]" if path else f"{tag}[{idx}]"
        
        if child.text and child.text.strip():
            result_dict[child_path] = child.text.strip()
            
        build_xpath_dict(child, child_path, result_dict)
    return result_dict

def merge_pettalk():
    print("="*60)
    print(" 🐾 RO 宠物对话表 (PetTalkTable) 智能合并器 ".center(56, " "))
    print("="*60)

    print("⏳ 正在读取并解密数据...")
    en_content = read_and_decrypt_xml(EN_FILE)
    cn_content = read_and_decrypt_xml(CN_FILE)
    tw_content = read_and_decrypt_xml(TW_FILE)

    if not en_content:
        print("❌ 英文骨架文件为空，无法执行合并！")
        return

    # 1. 解析英文骨架
    try:
        en_root = ET.fromstring(en_content)
    except Exception as e:
        print(f"❌ 英文 XML 解析失败: {e}")
        return
        
    # 2. 解析简中数据
    cn_dict = {}
    if cn_content:
        try:
            cn_root = ET.fromstring(cn_content)
            cn_dict = build_xpath_dict(cn_root)
            print(f"  ✅ 成功加载简中数据 (提取了 {len(cn_dict)} 句对话)")
        except:
            print("  ⚠️ 简中 XML 解析失败，跳过。")
            
    # 3. 解析繁体数据
    tw_dict = {}
    if tw_content:
        try:
            tw_root = ET.fromstring(tw_content)
            tw_dict = build_xpath_dict(tw_root)
            print(f"  ✅ 成功加载繁体数据 (提取了 {len(tw_dict)} 句对话)")
        except:
            print("  ⚠️ 繁体 XML 解析失败，跳过。")

    print("-" * 60)
    stats = {"cn": 0, "tw_to_cn": 0, "en": 0, "total": 0}

    # 4. 遍历替换逻辑
    def traverse_and_replace(element, path=""):
        tag_counts = {}
        for child in element:
            tag = child.tag
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            idx = tag_counts[tag]
            child_path = f"{path}/{tag}[{idx}]" if path else f"{tag}[{idx}]"
            
            if child.text and child.text.strip():
                stats["total"] += 1
                # 根据 XPath 路径去中文字典里“提货”
                if child_path in cn_dict and has_chinese(cn_dict[child_path]):
                    child.text = cn_dict[child_path]
                    stats["cn"] += 1
                elif child_path in tw_dict and has_chinese(tw_dict[child_path]):
                    child.text = zhconv.convert(tw_dict[child_path], 'zh-cn')
                    stats["tw_to_cn"] += 1
                else:
                    stats["en"] += 1
                    
            traverse_and_replace(child, child_path)

    print("⏳ 正在将中文对话注入英文骨架...")
    traverse_and_replace(en_root)

    # 5. 生成最终文件 (为了兼容老客户端，依然保留 euc-kr 声明但保存为 GBK 实体编码)
    xml_str = '<?xml version="1.0" encoding="euc-kr"?>\n' + ET.tostring(en_root, encoding="unicode")
    
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write(xml_str)

    print("=" * 60)
    print("🎉 合并完成！统计报告：")
    print(f"  🔹 宠物对话总数: {stats['total']}")
    print(f"  ✅ 完美命中简中 (CN): {stats['cn']}")
    print(f"  🔄 繁体转简体抢救 (TW->CN): {stats['tw_to_cn']}")
    print(f"  ⚠️ 无翻译保留英文 (EN): {stats['en']}")
    print(f"\n📄 最终文件已生成: {OUT_FILE} (GBK 编码)")
    print("=" * 60)

if __name__ == "__main__":
    merge_pettalk()