# -*- coding: utf-8 -*-
import os
import subprocess
import time

# 🎯 核心配置区
TARGET_DIR = "lua files"      # 你要遍历的目标主文件夹
LUAC_EXE = "luac5.1.exe"        # 你的 Lua 编译器程序名称 (如果在子目录，请写相对路径，如 "tools/luac.exe")

def compile_all_lua():
    print("="*60)
    print(f" 🚀 启动 RO 客户端 Lua -> Lub 终极编译装配线 ".center(54, " "))
    print("="*60)

    # 1. 环境自检：检查目标文件夹和编译器是否存在
    if not os.path.exists(TARGET_DIR):
        print(f"❌ 找不到目标文件夹: {TARGET_DIR}，请检查路径！")
        return

    try:
        # 尝试静默运行一下 luac，看看是否能调用成功
        subprocess.run([LUAC_EXE, "-v"], capture_output=True, check=True)
        print(f"✅ 编译器 {LUAC_EXE} 引擎预热成功！\n")
    except FileNotFoundError:
        print(f"❌ 致命错误：找不到编译器 '{LUAC_EXE}'！")
        print(f"   请确保 '{LUAC_EXE}' 与本脚本在同一目录下，或者已加入系统环境变量。")
        return
    except Exception as e:
        print(f"⚠️ 编译器预热异常，但将尝试强制执行。原因: {e}\n")

    success_count = 0
    fail_count = 0
    failed_files = []

    start_time = time.time()

    # 2. 深度遍历文件夹
    for root, dirs, files in os.walk(TARGET_DIR):
        for file in files:
            if file.lower().endswith(".lua"):
                lua_path = os.path.join(root, file)
                # 构造输出路径：把 .lua 换成 .lub
                lub_path = os.path.join(root, file[:-4] + ".lub")
                
                # 3. 构造并执行编译命令: luac.exe -o 输出.lub 输入.lua
                cmd = [LUAC_EXE, "-o", lub_path, lua_path]
                
                try:
                    # capture_output 捕获错误信息，以便在失败时排查
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        success_count += 1
                        # 为了不让屏幕滚动太快，成功信息可以简单打印
                        print(f"🟢 [成功] {lua_path}  ->  {file[:-4]}.lub")
                    else:
                        fail_count += 1
                        error_msg = result.stderr.strip()
                        failed_files.append((lua_path, error_msg))
                        print(f"🔴 [失败] {lua_path}")
                        print(f"   ↳ 错误信息: {error_msg}")
                        
                except Exception as e:
                    fail_count += 1
                    failed_files.append((lua_path, str(e)))
                    print(f"🔴 [异常] {lua_path}\n   ↳ {e}")

    end_time = time.time()

    # 4. 打印最终审计报告
    print("\n" + "="*60)
    print(" 📊 编译任务总装报告 ")
    print("="*60)
    print(f"⏱️  总耗时: {end_time - start_time:.2f} 秒")
    print(f"✅  成功编译: {success_count} 个文件")
    
    if fail_count == 0:
        print(f"🎉  完美收官！所有的 Lua 文件都已化身为强健的 Lub 字节码，准备注入 GRF！")
    else:
        print(f"❌  编译失败: {fail_count} 个文件")
        print("\n⚠️ 以下文件因为语法错误或编码问题未能编译，请手动检查：")
        for f, err in failed_files:
            print(f"   - {f}")
            # Lua 编译器的报错通常会指出具体的行数，这非常有助于排错
            print(f"     [报错点]: {err}")
    print("="*60)

if __name__ == "__main__":
    compile_all_lua()