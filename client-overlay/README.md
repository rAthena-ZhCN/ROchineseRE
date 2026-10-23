# client-overlay（客户端中文覆盖包）

覆盖到客户端根目录即可，包含：

- `SystemEN/`：物品、技能、任务、成就、地图、提示等中文 lua/lub
- `data/`
  - `msgstringtable.csv/.txt`：界面文本
  - `mapnametable.txt`、`questid2display.txt`、`book/`
  - `luafiles514/lua files/`：各功能模块与 `datainfo/pcjobname`（GBK 中文）
  - `texture/.../esc_*.bmp`：ESC 菜单按钮中文图片
- `Skin/*/esc_*.bmp`：各皮肤的中文 ESC 按钮

## 前置条件（重要）

1. 客户端需启用 WARP0716 的 `Custom*Lub` 系列补丁；
2. **`CustomCodePage` 必须设为 936（GBK）**；
   设 65001 会让中文变方框，不设则职业名会显示成 `3oDAOβ`；
3. `clientinfo.xml`：`<langtype>3</langtype>`、`<servicetype>china</servicetype>`。

推荐 WARP 配置：`WARP0716/profiles/zhcn_codepage936.yml`

## 用法

1. 备份客户端；
2. 双击 `一键覆盖.bat`，把客户端根目录拖进去；
3. 重启客户端。

也可以手动把 `SystemEN`、`data`、`Skin` 复制到客户端根目录合并。

## 说明

- 本包只覆盖翻译文件，不包含客户端本体、GRF、exe；
- 职业名使用 GBK `pcjobname.lub`，必须配合 codepage 936；
- 设置界面的 `gamesettings.lub` 已翻译为 GBK 中文。