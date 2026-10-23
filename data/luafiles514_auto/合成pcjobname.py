# -*- coding: utf-8 -*-
import os
import re
import subprocess
import zhconv

# 🎯 严格的路径配置
FILE_NAME = "pcjobname.lua"
EN_FILE = os.path.join("en_lua files", "datainfo", FILE_NAME)
CN_FILE = os.path.join("cn_lua files", "datainfo", FILE_NAME)
TW_FILE = os.path.join("tw_lua files", "datainfo", FILE_NAME)

OUT_DIR = os.path.join("lua files", "datainfo")
OUT_LUA = os.path.join(OUT_DIR, FILE_NAME)
OUT_LUB = os.path.join(OUT_DIR, "pcjobname.lub")

LUAC_EXE = "luac5.1.exe"  # 如果你的编译器叫 luac.exe，请在这里修改

def read_text(filepath, is_tw=False):
    if not os.path.exists(filepath): return ""
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return f.read()
    except UnicodeDecodeError: pass
    if is_tw:
        with open(filepath, 'r', encoding='big5', errors='ignore') as f: return f.read()
    else:
        with open(filepath, 'r', encoding='gb18030', errors='ignore') as f: return f.read()

def build_pcjobname():
    print("="*60)
    print(f" 🛡️ pcjobname 专属防乱码编译机 ".center(54, " "))
    print("="*60)
    
    if not os.path.exists(EN_FILE):
        print(f"❌ 找不到英文源文件: {EN_FILE}")
        return

    en_text = read_text(EN_FILE)
    cn_text = read_text(CN_FILE)
    tw_text = read_text(TW_FILE, is_tw=True)

    # 1. 提取中/繁翻译 (格式: [JOBID.JT_NOVICE] = "初心者")
    translations = {}
    pattern = re.compile(r'\[(JOBID\.[A-Z0-9_]+)\]\s*=\s*"([^"]+)"')
    
    for text, is_tw in [(tw_text, True), (cn_text, False)]:
        if not text: continue
        for m in pattern.finditer(text):
            job_id = m.group(1)
            job_name = m.group(2)
            if is_tw: job_name = zhconv.convert(job_name, 'zh-cn')
            if re.search(r'[\u4e00-\u9fa5]', job_name):
                translations[job_id] = job_name

    print(f"✅ 成功从 CN/TW 提取了 {len(translations)} 个职业翻译。")

    # 2. 精准替换 EN 骨架
    out_lines = []
    replaced_count = 0
    for line in en_text.splitlines():
        m = re.search(r'\[(JOBID\.[A-Z0-9_]+)\]\s*=\s*"', line)
        if m:
            job_id = m.group(1)
            if job_id in translations:
                # 替换掉原本的英文名称
                line = re.sub(r'(\[JOBID\.[A-Z0-9_]+\]\s*=\s*")[^"]*(")', 
                              lambda match: match.group(1) + translations[job_id] + match.group(2), 
                              line)
                replaced_count += 1
        out_lines.append(line)

    print(f"✅ 成功替换了 {replaced_count} 个职业名称到 EN 骨架。")

    # 3. 🛡️ 强制 GB18030 输出 Lua 源码 (防乱码的核心所在)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_LUA, 'w', encoding='gb18030', errors='ignore') as f:
        f.write("\n".join(out_lines))
    
    print(f"💾 中间文件已安全保存为 GB18030 编码: {OUT_LUA}")

    # 4. 调用 luac.exe 编译
    if not os.path.exists(LUAC_EXE):
        print(f"❌ 找不到编译器 {LUAC_EXE}！请把它放在脚本同级目录。")
        return

    print("⚙️ 正在调用 luac 引擎进行编译...")
    try:
        # 执行: luac5.1.exe -o "lua files/datainfo/pcjobname.lub" "lua files/datainfo/pcjobname.lua"
        subprocess.run([LUAC_EXE, "-o", OUT_LUB, OUT_LUA], check=True, capture_output=True)
        print(f"🎉 编译成功！完美封包至: {OUT_LUB}")
    except subprocess.CalledProcessError as e:
        print(f"🔴 编译失败！错误信息: {e.stderr.decode('gbk', errors='ignore')}")
    except Exception as e:
        print(f"🔴 发生异常: {e}")
        
    print("="*60)
    print("💡 下一步: 请直接把生成的 pcjobname.lub 丢进客户端测试，乱码必除！")

if __name__ == "__main__":
    build_pcjobname()