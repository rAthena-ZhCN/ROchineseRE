@echo off
echo ===============================================================================
echo = Lub 反编译脚本由 EXP 编写，欢迎使用...                                  =
echo ===============================================================================
if not exist Output (
	mkdir Output
)
set LubCount=0
for %%i in (*.lub) do (
	set /a LubCount+=1
)
if %LubCount% equ 0 (
	echo = 程序并未发现 SpyBin 的同级目录下存在 lub 文件需要反编译...                =
)
for %%i in (*.lub) do (
	echo = 正在反编译 %%i 到 Output\%%~ni.lub
	SpyBin\luadec5.1.exe %%i > Output\%%~ni.lub
	del %%i
)
echo ===============================================================================del %%i
echo = 反编译过程已经执行完毕，再次感谢您的使用！                                    =
echo ===============================================================================
pause