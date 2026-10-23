# -*- coding: utf-8 -*-
import os
import base64

CSV_FILE = "en_msgstringtable.csv"
TXT_FILE = "msgstringtable.txt"
OUT_CSV = "msgstringtable.csv"

def convert_txt_to_base64_csv():
    print("="*60)
    print(" 🔄 RO Base64 文本表编译器 (UTF-8 修正版) ".center(50, " "))
    print("="*60)

    if not os.path.exists(CSV_FILE) or not os.path.exists(TXT_FILE):
        print("❌ 找不到 msgstringtable.csv 或 msgstringtable.txt！")
        return

    # 1. 读取官方 CSV
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        csv_lines = f.read().splitlines()

    # 2. 读取你的汉化 TXT (你的 TXT 是 GBK 的，所以这里按 GBK 读入内存)
    with open(TXT_FILE, 'r', encoding='gbk', errors='ignore') as f:
        txt_content = f.read()

    txt_entries = txt_content.split('#')
    txt_entries = [e.strip('\r\n') for e in txt_entries]

    out_lines = []
    replaced_count = 0

    # 3. 开始注入密文
    for i, csv_line in enumerate(csv_lines):
        parts = csv_line.split(',')
        if len(parts) < 2:
            out_lines.append(csv_line)
            continue

        key_b64 = parts[0]

        if i < len(txt_entries) and txt_entries[i].strip() != "":
            cn_text = txt_entries[i]

            # 🚀 核心修正 1：将中文转化为纯正的 UTF-8 字节再进行 Base64 加密！
            # 迎合现代 RO 客户端 UI 引擎的 UTF-8 升级
            val_bytes = cn_text.encode('utf-8', errors='ignore')
            val_b64 = base64.b64encode(val_bytes).decode('utf-8')

            out_lines.append(f"{key_b64},{val_b64}")
            replaced_count += 1
        else:
            out_lines.append(csv_line)

    # 🚀 核心修正 2：使用 'utf-8-sig' 输出，强行加上 BOM 头，防止客户端读取文件开头时崩溃
    with open(OUT_CSV, 'w', encoding='utf-8-sig') as f:
        f.write('\n'.join(out_lines) + '\n')

    print(f"🎉 编译成功！使用了全新的 UTF-8 底层编码。")
    print(f"📁 请将生成的 [{OUT_CSV}] 重命名为 msgstringtable.csv，丢进客户端测试！")
    print("="*60)

if __name__ == "__main__":
    convert_txt_to_base64_csv()