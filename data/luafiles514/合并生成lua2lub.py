# -*- coding: utf-8 -*-
import os
import re
import subprocess
import zhconv
from openai import OpenAI

# ================= 1. 全局与 API 配置区 =================
# 阿里云百炼 (Qwen) API 配置
API_KEY = "sk-f0c5fb9fd3e644f3b84ec74f5a3fb5e2" 
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen3.5-plus" # 推荐 qwen-plus，性价比极高，逻辑能力强

EN_DIR = "en_lua files"
CN_DIR = "cn_lua files"
TW_DIR = "tw_lua files"
OUT_DIR = "lua files"
LOG_FILE = "agent_pipeline.log"

LUAC_PATH = "luac5.1.exe"

PATH_MAPPING_CN = {"korea": "china", "_kr": "_ch", "korean": "chinese"}
PATH_MAPPING_TW = {"korea": "taiwan", "_kr": "_tw", "korean": "taiwanese"}

# 初始化千问客户端
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
# =======================================================

def read_lua_text(filepath):
    if not os.path.exists(filepath): return ""
    for enc in ['utf-8', 'utf-8-sig', 'gbk', 'big5']:
        try:
            with open(filepath, 'r', encoding=enc) as f: return f.read()
        except: continue
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: return f.read()

def compile_to_lub(lua_content, out_filepath):
    temp_lua = out_filepath.replace('.lub', '.temp.lua')
    if not temp_lua.endswith('.lua'): temp_lua += '.lua'
    os.makedirs(os.path.dirname(out_filepath), exist_ok=True)
    with open(temp_lua, 'w', encoding='gbk', errors='ignore') as f: f.write(lua_content)
    if out_filepath.endswith('.lua'):
        os.replace(temp_lua, out_filepath)
        return True
    cmd = [LUAC_PATH, '-o', out_filepath, temp_lua]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if os.path.exists(temp_lua): os.remove(temp_lua)
    return result.returncode == 0

def map_path(rel_path, mapping_dict):
    mapped = rel_path
    for kr_str, local_str in mapping_dict.items():
        mapped = re.sub(re.escape(kr_str), local_str, mapped, flags=re.IGNORECASE)
    return mapped

def get_file_sample(text, max_lines=150):
    """提取文件的前 N 行作为样本发送给大模型，节省 Token 并加快速度"""
    if not text: return ""
    lines = text.splitlines()
    return "\n".join(lines[:max_lines])

def request_merge_strategy_from_llm(filename, en_sample, cn_sample, tw_sample):
    """向千问请求专属的 Python 合并代码"""
    system_prompt = """
    你是一个资深的 RO 仙境传说客户端本地化工程师和 Python 专家。
    你的任务是：根据提供的 EN, CN, TW 三个 Lua 文件的样本，编写一个 Python 函数来将中文翻译完美合并到英文骨架中。
    
    规则与痛点：
    1. 函数签名必须是：`def custom_merge(en_text, cn_text, tw_text):`
    2. 函数必须返回合并后的完整字符串 `merged_text`。
    3. 警惕韩文乱码：CN 或 TW 中可能夹杂 EUC-KR 解码错误的乱码（如"酒抛唱蒋靛S"）。你必须在生成的代码里写逻辑，利用 `re.search(r'[\u4e00-\u9fa5]', text)` 确保只提取真正的中文，忽略乱码。
    4. 保护代码骨架：不要破坏 Lua 的 Table 结构、键名（如 `["Bs_Item_M_S_26"]`）或内部变量名（如 `"EFST_MOVE_AGIT"`）。
    5. 你可以且应该在生成的代码中 `import re` 和 `import zhconv`。
    
    返回格式：
    只返回 Python 代码，必须用 ```python 和 ``` 包裹。不要有任何多余的解释！
    """
    
    user_prompt = f"""
    文件目标: {filename}
    
    === EN 样本 ===
    {en_sample}
    
    === CN 样本 ===
    {cn_sample}
    
    === TW 样本 ===
    {tw_sample}
    
    请输出定制的 `custom_merge` 函数代码。
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1 # 保持极低温度，确保代码逻辑严谨
        )
        content = response.choices[0].message.content
        
        # 使用正则提取包裹在 ```python ``` 中的代码
        match = re.search(r'```python(.*?)```', content, re.DOTALL)
        if match:
            return match.group(1).strip()
        else:
            return content.strip() # 兼容大模型忘记写 Markdown 标记的情况
    except Exception as e:
        print(f"\n[API 请求失败]: {e}")
        return None

def agentic_merge(en_text, cn_text, tw_text, filename):
    """智能体核心：获取策略 -> 动态编译 -> 执行合并"""
    if not cn_text and not tw_text:
        return en_text # 没中文资源，直接返回英文
        
    en_sample = get_file_sample(en_text)
    cn_sample = get_file_sample(cn_text)
    tw_sample = get_file_sample(tw_text)
    
    print(" [🧠 思考合并策略...]", end="", flush=True)
    strategy_code = request_merge_strategy_from_llm(filename, en_sample, cn_sample, tw_sample)
    
    if not strategy_code:
        raise Exception("大模型未能返回有效的合并策略代码")
        
    # 构建安全的执行命名空间
    exec_namespace = {
        're': re,
        'zhconv': zhconv
    }
    
    try:
        # 动态执行 LLM 写的代码，将函数加载到内存中
        exec(strategy_code, globals(), exec_namespace)
        custom_merge_func = exec_namespace.get('custom_merge')
        
        if not custom_merge_func:
            raise Exception("生成的代码中未找到 custom_merge 函数")
            
        print(" [⚙️ 执行动态注入...]", end="", flush=True)
        # 实际调用 LLM 写的函数来处理整个文件
        merged_text = custom_merge_func(en_text, cn_text, tw_text)
        return merged_text
        
    except Exception as e:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n[{filename}] 动态执行失败:\n{e}\n生成的代码:\n{strategy_code}\n")
        raise e

def run_agentic_pipeline():
    print("="*70)
    print(" 🧠 RO 本地化智能体中枢 (Agentic Pipeline) 启动 ".center(66, " "))
    print("="*70)
    
    total, success, failed = 0, 0, 0
    
    for root, dirs, files in os.walk(EN_DIR):
        for file in files:
            if not (file.endswith('.lua') or file.endswith('.lub')): continue
            
            total += 1
            rel_path = os.path.relpath(os.path.join(root, file), EN_DIR)
            en_filepath = os.path.join(EN_DIR, rel_path)
            out_filepath = os.path.join(OUT_DIR, rel_path)
            
            cn_rel_path = map_path(rel_path, PATH_MAPPING_CN).replace('.lub', '.lua')
            tw_rel_path = map_path(rel_path, PATH_MAPPING_TW).replace('.lub', '.lua')
            
            en_text = read_lua_text(en_filepath)
            cn_text = read_lua_text(os.path.join(CN_DIR, cn_rel_path))
            tw_text = read_lua_text(os.path.join(TW_DIR, tw_rel_path))
            
            print(f"\n🔄 处理: {rel_path}", end="")
            
            try:
                merged_text = agentic_merge(en_text, cn_text, tw_text, rel_path)
                
                if compile_to_lub(merged_text, out_filepath):
                    print(" [✅ 编译成功]")
                    success += 1
                else:
                    print(" [❌ 编译失败]")
                    failed += 1
            except Exception as e:
                print(f" [⚠️ 智能体作业崩溃，回退保留英文原版] (详见日志)")
                compile_to_lub(en_text, out_filepath) # 失败则回退，保证客户端完整
                failed += 1

    print("\n" + "="*70)
    print(f"🎉 智能体作业完成！")
    print(f"总计处理: {total} 个 | 成功合并: {success} 个 | 失败回退: {failed} 个")
    print("="*70)

if __name__ == "__main__":
    run_agentic_pipeline()