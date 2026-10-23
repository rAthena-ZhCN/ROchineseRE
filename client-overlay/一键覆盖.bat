@echo off
chcp 936 >nul
setlocal
set "SRC=%~dp0"
set "TARGET=%~1"
if "%TARGET%"=="" (
  echo 请把客户端根目录拖到本 BAT 上，或直接输入路径。
  set /p TARGET=客户端根目录: 
)
if not exist "%TARGET%\data.grf" (
  echo [警告] 该目录下没有 data.grf，可能不是客户端根目录。
  pause
  exit /b 1
)
echo 正在覆盖 SystemEN...
robocopy "%SRC%SystemEN" "%TARGET%\SystemEN" /E /NFL /NDL /NJH /NJS >nul
echo 正在覆盖 data...
robocopy "%SRC%data" "%TARGET%\data" /E /NFL /NDL /NJH /NJS >nul
if exist "%SRC%Skin" (
  echo 正在覆盖 Skin...
  robocopy "%SRC%Skin" "%TARGET%\Skin" /E /NFL /NDL /NJH /NJS >nul
)
echo.
echo 完成，请重启客户端。
pause