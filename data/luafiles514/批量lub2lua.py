# -*- coding: utf-8 -*-
import os
import subprocess

# ================= 配置区 =================
# 反编译工具的路径 (如果你的工具在 SpyBin 文件夹下，请改为 "SpyBin/luadec5.1.exe")
LUADEC_PATH = "luadec5.1.exe" 

# 需要执行批量反编译的文件夹列表
TARGET_DIRS = ["cn_lua files", "tw_lua files"]

# 是否在成功解码出 .lua 后，删除原来的 .lub 文件？(True: 删除 / False: 保留)
DELETE_ORIGINAL_LUB = False
# ==========================================

def batch_decompile_lub():
    print("="*70)
    print(" 🔓 RO 客户端 LUB 批量原地反编译器 ".center(66, " "))
    print("="*70)

    if not os.path.exists(LUADEC_PATH):
        print(f"❌ 找不到反编译工具: {LUADEC_PATH}")
        print("请确保 luadec5.1.exe 与本脚本在同一目录下！")
        return

    total_files = 0
    success_count = 0
    fail_count = 0

    for target_dir in TARGET_DIRS:
        if not os.path.exists(target_dir):
            print(f"⚠️ 找不到文件夹: [{target_dir}]，已跳过。")
            continue

        print(f"\n📂 开始深度扫描文件夹: [{target_dir}]")
        
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith(".lub"):
                    total_files += 1
                    lub_path = os.path.join(root, file)
                    # 将后缀替换为 .lua
                    lua_path = lub_path[:-4] + ".lua"

                    # 核心命令: luadec5.1.exe "文件路径"
                    cmd = [LUADEC_PATH, lub_path]
                    
                    try:
                        # 执行反编译，捕获标准输出 (luadec 默认将结果打印到屏幕，我们需要把它拦截并写入文件)
                        # 使用 gbk 编码读取，防止中文路径或客户端文本乱码报错
                        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='gbk', errors='ignore')

                        # 如果返回码是 0 (成功)，并且输出内容包含 "--" 或 "{" 等 Lua 特征
                        if result.returncode == 0 and len(result.stdout.strip()) > 10:
                            # 将拦截到的明文代码写入 .lua 文件
                            with open(lua_path, 'w', encoding='gbk', errors='ignore') as f:
                                f.write(result.stdout)
                                
                            print(f"  ✅ 成功解码: {os.path.relpath(lub_path, target_dir)}")
                            success_count += 1
                            
                            # 原地替换：如果配置了删除，则干掉老文件
                            if DELETE_ORIGINAL_LUB:
                                os.remove(lub_path)
                                
                        else:
                            print(f"  ❌ 解码失败 (工具报错或无输出): {os.path.relpath(lub_path, target_dir)}")
                            fail_count += 1
                            
                    except Exception as e:
                        print(f"  ❌ 执行异常: {os.path.relpath(lub_path, target_dir)} | 错误: {e}")
                        fail_count += 1

    print("\n" + "="*70)
    print(f"🎉 批量反编译作业完成！")
    print(f"  🔹 发现 .lub 总数: {total_files}")
    print(f"  ✅ 成功原地转为 .lua: {success_count}")
    print(f"  ❌ 失败或无法解析: {fail_count}")
    print("="*70)

if __name__ == "__main__":
    batch_decompile_lub()