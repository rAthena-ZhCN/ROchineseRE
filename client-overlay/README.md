# client-overlay（客户端中文覆盖包）

把本文件夹里的内容覆盖到客户端根目录即可，包含：

- `SystemEN/`：物品、技能、任务、成就、地图、提示等中文 lua/lub
- `data/`：
  - `msgstringtable.csv/.txt`：界面文本
  - `mapnametable.txt`、`questid2display.txt`、`book/`
  - `luafiles514/lua files/`：各功能模块与 `datainfo/pcjobname` 等
  - `texture/.../esc_*.bmp`：ESC 菜单按钮中文图片
- `Skin/*/esc_*.bmp`：各皮肤的中文 ESC 按钮

## 用法

1. 建议先备份客户端；
2. 双击 `一键覆盖.bat`，把客户端根目录拖进去（或输入路径）；
3. 重启客户端。

也可以手动把 `SystemEN`、`data`、`Skin` 三个文件夹复制到客户端根目录并合并。

## 说明

- 客户端需启用 **Use SystemEN** 相关补丁（WARP0716 的 `Custom*Lub` 系列）；
- `langtype` 用 **3**（GB2312）；
- 本包只覆盖翻译文件，不包含客户端本体、GRF、exe。