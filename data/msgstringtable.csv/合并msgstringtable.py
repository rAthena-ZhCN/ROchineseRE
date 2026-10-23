# -*- coding: utf-8 -*-
import os
import re
import zhconv

# ================= 配置区 =================
EN_FILE = "en_msgstringtable.txt"
TW_FILE = "tw_msgstringtable.txt"
CN_FILE = "cn_msgstringtable.txt"
OUT_FILE = "msgstringtable.txt"
# ==========================================

def read_lines_robust(filepath):
    """自适应编码读取文件，返回行列表"""
    if not os.path.exists(filepath):
        print(f"⚠️ 未找到文件: {filepath} (将视为空)")
        return []
    
    strict_encodings = ['utf-8', 'utf-8-sig', 'gbk', 'big5hkscs', 'big5', 'cp950']
    for enc in strict_encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.readlines()
        except UnicodeDecodeError:
            continue

    fallback_encodings = ['cp950', 'big5hkscs', 'utf-8', 'gbk']
    for enc in fallback_encodings:
        try:
            with open(filepath, 'r', encoding=enc, errors='ignore') as f:
                return f.readlines()
        except Exception:
            continue
            
    print(f"❌ 无法读取 {filepath}！")
    return []

def has_chinese(text):
    """检测字符串中是否包含中文字符"""
    return bool(re.search(r'[\u4e00-\u9fa5]', text))

def merge_msgstring():
    print("="*60)
    print(" 💬 RO 客户端系统提示文本 (MsgString) 精准合并器 ".center(56, " "))
    print("="*60)

    print("⏳ 正在读取数据...")
    en_lines = read_lines_robust(EN_FILE)
    cn_lines = read_lines_robust(CN_FILE)
    tw_lines = read_lines_robust(TW_FILE)

    if not en_lines:
        print("❌ 英文骨架文件为空，无法执行合并！")
        return

    print(f"  📌 英文骨架共: {len(en_lines)} 行 (以此为绝对标准)")
    print(f"  📌 简中资源共: {len(cn_lines)} 行")
    print(f"  📌 繁体资源共: {len(tw_lines)} 行")
    print("-" * 60)

    merged_lines = []
    stats = {"cn": 0, "tw_to_cn": 0, "en": 0}

    for i in range(len(en_lines)):
        en_line = en_lines[i].rstrip('\n\r')
        
        # 提取 CN 和 TW 的对应行
        cn_line = cn_lines[i].rstrip('\n\r') if i < len(cn_lines) else ""
        tw_line = tw_lines[i].rstrip('\n\r') if i < len(tw_lines) else ""

        # 核心逻辑：按优先级和“中文纯度”进行选择
        if cn_line and has_chinese(cn_line):
            # 1. 简中有内容且包含中文 -> 最高优先级
            merged_lines.append(cn_line)
            stats["cn"] += 1
        elif tw_line and has_chinese(tw_line):
            # 2. 简中没翻译，但繁体有中文 -> 转换后征用
            merged_lines.append(zhconv.convert(tw_line, 'zh-cn'))
            stats["tw_to_cn"] += 1
        elif cn_line and cn_line != "#":
            # 3. 简中是符号或英文（比如 "%s#"）
            merged_lines.append(cn_line)
            stats["cn"] += 1
        elif tw_line and tw_line != "#":
            # 4. 繁体是符号或英文
            merged_lines.append(zhconv.convert(tw_line, 'zh-cn'))
            stats["tw_to_cn"] += 1
        else:
            # 5. 都没救了，使用英文原版
            merged_lines.append(en_line)
            stats["en"] += 1

    # 强制 GBK 输出
    with open(OUT_FILE, 'w', encoding='gbk', errors='ignore') as f:
        f.write("\n".join(merged_lines) + "\n")
        
    print("=" * 60)
    print("🎉 合并完成！统计报告：")
    print(f"  ✅ 完美采用简中 (CN): {stats['cn']} 行")
    print(f"  🔄 繁体转简体抢救 (TW->CN): {stats['tw_to_cn']} 行")
    print(f"  ⚠️ 无翻译保留英文 (EN): {stats['en']} 行")
    print(f"\n📄 最终文件已生成: {OUT_FILE} (GBK 编码)")
    print("=" * 60)

if __name__ == "__main__":
    merge_msgstring()