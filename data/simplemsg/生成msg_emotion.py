# -*- coding: utf-8 -*-
import os
import base64
import zhconv

# ================= 配置区 =================
TW_FILE = "tw_msg_emotion.csv"
OUT_FILE = "cn_msg_emotion.csv" # 或者你可以直接命名为 msg_emotion.csv
# ==========================================

def process_emotion():
    print("="*60)
    print(" 😃 RO 客户端表情系统 (msg_emotion) 繁简转换器 ".center(56, " "))
    print("="*60)

    if not os.path.exists(TW_FILE):
        print(f"❌ 找不到文件: {TW_FILE}")
        return
        
    out_lines = []
    success_count = 0
    
    # 使用 utf-8-sig 防止潜在的 BOM 头干扰
    with open(TW_FILE, 'r', encoding='utf-8-sig') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
                
            parts = line.split(',')
            if len(parts) >= 2:
                # 第一列是 Base64 编码的 Key
                key_b64 = parts[0]
                # 第二列是 Base64 编码的 繁体文本
                val_b64 = parts[1]
                
                try:
                    # 1. 解码繁体文本
                    tw_text = base64.b64decode(val_b64).decode('utf-8')
                    
                    # 2. 转换为简体中文
                    cn_text = zhconv.convert(tw_text, 'zh-cn')
                    
                    # 3. 重新 Base64 编码
                    cn_b64 = base64.b64encode(cn_text.encode('utf-8')).decode('utf-8')
                    
                    # 4. 组合新行 (严格保持官方的 2 列结构)
                    out_lines.append(f"{key_b64},{cn_b64}")
                    success_count += 1
                except Exception as e:
                    print(f"⚠️ 第 {i+1} 行解码失败: {val_b64}，将保留原样。错误: {e}")
                    out_lines.append(line)
            else:
                out_lines.append(line)
                
    # 写入新文件 (因为全是纯英文 Base64，所以直接存为普通 utf-8 即可)
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(out_lines) + "\n")
        
    print(f"🎉 转换完成！共处理了 {success_count} 条表情文本。")
    print(f"📄 已生成完美兼容的简体文件: {OUT_FILE}")
    print("="*60)

if __name__ == "__main__":
    process_emotion()