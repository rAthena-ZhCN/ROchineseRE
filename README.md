# RoChineseRE（rAthena 中文客户端汉化工程）

基于 [ROenglishRE](https://github.com/llchrisll/ROenglishRE) 的三语合并工程：
以 **英文 lua 为骨架**，把 **国服（cn）/ 台服（tw）** 官方文本按 key 合并进去，再用 `luac` 编译成客户端可读的 `.lub`。

目标是配合 **rAthenaZhCN** 服务端和 **2025-07-16 Ragexe** 客户端，维护一套可持续更新的中文客户端翻译。

## 一、目录说明

```
RoChineseRE/
├── SystemEN/
│   ├── en_SystemEN/        英文骨架（来自 ROenglishRE）
│   ├── cn_SystemEN/        国服中文源
│   ├── tw_SystemEN/        台服中文源
│   ├── systemEN/           合并后的成品（lua + lub）
│   ├── OngoingQuests/      任务追踪专用合并目录
│   └── 合并*.py            各模块合并脚本
├── data/
│   ├── luafiles514/
│   │   ├── en_lua files/   英文骨架（19 个模块）
│   │   ├── cn_lua files/   国服源
│   │   ├── tw_lua files/   台服源
│   │   ├── lua files/      合并后的成品
│   │   └── *.py            合并/编译脚本
│   ├── msgstringtable.csv/ 界面文本（成品，含 msgstringtable.txt）
│   ├── mapnametable.txt/   地图名
│   ├── questid2display.txt/任务名
│   └── book/               书籍文本
├── Lua编译与Lub反编译/      luac / luadec 工具
└── UnLuaC工具/              unluac 工具
```

> 注：`msgstringtable.csv/`、`mapnametable.txt/`、`questid2display.txt/` 是**同名文件夹**，里面放实际文件，是沿用早期脚本的路径习惯。

## 二、当前状态（2026-10-23）

| 项目 | 状态 |
|---|---|
| EN 骨架快照 | ROenglishRE **2026-03-27**（上游最新 **2026-10-07**，待同步） |
| `SystemEN` 成品 | itemInfo、achievements、mapInfo、OngoingQuests、RecommendedQuests、Towninfo、spopup、tipbox |
| `data/luafiles514` 成品 | 6 个模块 + 从旧客户端补入的 13 个模块与 `datainfo` |
| 文本 | msgstringtable.csv/.txt、mapnametable.txt、questid2display.txt、书籍 |
| ESC 按钮图片 | 基础皮肤 + 3 个 `Skin` 皮肤，共 87 张 BMP |

### 客户端覆盖包（推荐使用）

仓库根目录的 `client-overlay/` 是可直接覆盖到客户端的中文包：

```
client-overlay/
├── SystemEN/
├── data/
│   ├── msgstringtable.csv/.txt
│   ├── mapnametable.txt
│   ├── questid2display.txt
│   ├── book/
│   ├── luafiles514/lua files/
│   └── texture/…/esc_*.bmp
├── Skin/*/esc_*.bmp
├── 一键覆盖.bat
└── README.md
```

把 `client-overlay` 里的内容覆盖到客户端根目录，或双击 `一键覆盖.bat` 选择客户端目录，然后重启客户端。

## 三、目标客户端与服务端

- 客户端：**2025-07-16 Ragexe（build 175220998）**
- 服务端：[rAthenaZhCN](https://github.com/rAthena-ZhCN/rAthenaZhCN)
- WARP 补丁：需要启用 **Use SystemEN** 类补丁，让客户端从 `SystemEN` 读取翻译
- **CustomCodePage 必须设为 936（GBK）**，否则职业名会按 CP1252 显示成 `3oDAOβ`
- `clientinfo.xml`：`<langtype>3</langtype>`、`<servicetype>china</servicetype>`
- 客户端本体、`data.grf`、exe 等**不进入本仓库**

## 四、构建流程

1. 用 `en_*` 作骨架，按 key 把 `cn_*` / `tw_*` 覆盖进去（缺的条目再机翻/人工补）；
2. 用 `luac5.1` 编译成 `.lub`；
3. 把成品放到客户端的 `SystemEN/` 和 `data/` 对应路径；
4. 测试：登录 → 建角色 → 进图 → 技能右键 → 物品说明 → 任务 → 地图名 → NPC 对话。

> 建议后续把成品打包成独立的 `translation.grf`，放在 `DATA.INI` 优先位置，避免客户端更新覆盖散文件。

## 五、与 ROenglishRE 同步

上游仓库：<https://github.com/llchrisll/ROenglishRE>

本地骨架停留在 2026-03-27，上游此后还有：

- 2026-04-18 / 04-24 / 05-12 更新
- 2026-07-08 更新
- 2026-08-05 更新
- 2026-09-23 更新
- 2026-10-07 更新（PrivateAirplane 20260520.lub、QuestEraseList.lua、itemInfo 微调、skilldescript 微调）

同步时建议只替换 `en_*` 骨架，然后重新跑合并脚本，检查新增/变更 key。

## 六、许可与致谢

- 英文骨架：[llchrisll/ROenglishRE](https://github.com/llchrisll/ROenglishRE)，遵循其项目说明；
- 中文文本来源：国服 / 台服官方客户端；
- 《仙境传说》客户端文本与资源版权归 Gravity 及各地区运营商所有，本仓库仅用于私服汉化研究，不包含客户端本体或 GRF；
- 本仓库中的脚本与合并成果可自由用于非商业用途。
