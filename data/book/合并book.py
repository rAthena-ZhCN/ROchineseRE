# -*- coding: utf-8 -*-
import os
import zhconv

# ================= 配置区 =================
EN_DIR = "en_book"
CN_DIR = "cn_book"
TW_DIR = "tw_book"
OUT_DIR = "book"
# ==========================================

def read_content_robust(filepath):
    """自适应编码读取文件，带防爆破双重容错机制"""
    strict_encodings = ['utf-8', 'utf-8-sig', 'gbk', 'big5hkscs', 'big5', 'cp950']
    for enc in strict_encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue

    fallback_encodings = ['cp950', 'big5hkscs', 'utf-8', 'gbk']
    for enc in fallback_encodings:
        try:
            with open(filepath, 'r', encoding=enc, errors='ignore') as f:
                return f.read()
        except Exception:
            continue
            
    print(f"❌ 无法读取 {filepath}，所有编码尝试均失败！")
    return ""

def merge_books():
    print("="*60)
    print(" 📚 RO 客户端书籍全集 (Book) 智能合并器 ".center(56, " "))
    print("="*60)

    # 确保输出文件夹存在
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    # 1. 收集所有三个文件夹中的唯一文件名，构建全集集合
    all_filenames = set()
    for directory in [EN_DIR, CN_DIR, TW_DIR]:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                # 过滤掉可能存在的隐藏文件或非文本文件
                if os.path.isfile(os.path.join(directory, filename)):
                    all_filenames.add(filename)
        else:
            print(f"⚠️ 警告: 未找到文件夹 '{directory}'，将跳过。")

    if not all_filenames:
        print("❌ 没有找到任何书籍文件，无法执行合并！")
        return

    print(f"📌 共发现 {len(all_filenames)} 本独特的书籍文件，准备执行融合...")
    print("-" * 60)

    stats = {"cn": 0, "tw_to_cn": 0, "en": 0, "total": len(all_filenames)}

    # 2. 遍历每一本书，执行优先级提取
    for filename in all_filenames:
        cn_path = os.path.join(CN_DIR, filename)
        tw_path = os.path.join(TW_DIR, filename)
        en_path = os.path.join(EN_DIR, filename)
        out_path = os.path.join(OUT_DIR, filename)

        content = ""
        source = ""

        if os.path.exists(cn_path):
            # 优先级 1: 简中原件
            content = read_content_robust(cn_path)
            stats["cn"] += 1
            source = "CN"
        elif os.path.exists(tw_path):
            # 优先级 2: 繁体转换
            raw_content = read_content_robust(tw_path)
            content = zhconv.convert(raw_content, 'zh-cn')
            stats["tw_to_cn"] += 1
            source = "TW->CN"
        elif os.path.exists(en_path):
            # 优先级 3: 英文兜底
            content = read_content_robust(en_path)
            stats["en"] += 1
            source = "EN"
            
        if content:
            # RO 客户端书籍文件同样需要 GBK (ANSI) 编码来防乱码
            with open(out_path, 'w', encoding='gbk', errors='ignore') as f:
                f.write(content)

    print("=" * 60)
    print("🎉 合并完成！全集统计报告：")
    print(f"  🔹 最终书籍总数: {stats['total']} 本")
    print(f"  ✅ 完美采用简中 (CN): {stats['cn']} 本")
    print(f"  🔄 繁体转简体抢救 (TW->CN): {stats['tw_to_cn']} 本")
    print(f"  ⚠️ 无翻译保留英文 (EN): {stats['en']} 本")
    print(f"\n📄 最终全集已生成至: [{OUT_DIR}] 文件夹 (GBK 编码)")
    print("=" * 60)

if __name__ == "__main__":
    merge_books()