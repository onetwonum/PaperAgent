@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM =============================================
REM PaperAgent 论文分析一键式流程脚本 (Windows版)
REM 用途：自动处理从PDF到分析报告的全部流程
REM =============================================

REM 默认设置
set WAIT_TIME=180
set PDF_PATH=
set SHOW_HELP=0

REM 处理参数
:parse_args
if "%~1"=="" goto :check_args
if /i "%~1"=="-h" set SHOW_HELP=1 & goto :show_help
if /i "%~1"=="--help" set SHOW_HELP=1 & goto :show_help
if /i "%~1"=="-w" set WAIT_TIME=%~2 & shift & shift & goto :parse_args
if /i "%~1"=="--wait" set WAIT_TIME=%~2 & shift & shift & goto :parse_args
set PDF_PATH=%~1
shift
goto :parse_args

:check_args
if %SHOW_HELP%==1 goto :show_help
if "%PDF_PATH%"=="" (
    echo 错误: 请提供PDF文件路径!
    goto :show_help
)

REM 检查文件是否存在
if not exist "%PDF_PATH%" (
    echo 错误: PDF文件不存在: %PDF_PATH%
    exit /b 1
)

REM 获取脚本目录和项目根目录
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
for %%I in ("%SCRIPT_DIR%\..") do set PROJECT_ROOT=%%~fI

REM 提取论文名称
for %%I in ("%PDF_PATH%") do set PAPER_NAME=%%~nI

REM 清理论文名称（Windows批处理中替换字符较为复杂）
REM 这里我们只替换几个常见的特殊字符
set PAPER_NAME=%PAPER_NAME: =_%
set PAPER_NAME=%PAPER_NAME:.=_%
set PAPER_NAME=%PAPER_NAME:-=_%
set PAPER_NAME=%PAPER_NAME:(=_%
set PAPER_NAME=%PAPER_NAME:)=_%
set PAPER_NAME=%PAPER_NAME:,=_%
set PAPER_NAME=%PAPER_NAME:@=_%
set PAPER_NAME=%PAPER_NAME:&=_%

echo =====================================================
echo PaperAgent 论文分析流程
echo =====================================================
echo PDF文件: %PDF_PATH%
echo 论文名称: %PAPER_NAME%
echo 等待时间: %WAIT_TIME% 秒
echo =====================================================

REM 第1阶段: magic-pdf 预处理
echo.
echo === 第1阶段: 使用magic-pdf处理PDF文件 ===
echo.

REM 修复: 正确设置输出目录
set OUTPUT_DIR=%SCRIPT_DIR%\pdf_preprocess\output
echo 输出目录: %OUTPUT_DIR%
echo 执行命令: magic-pdf -p "%PDF_PATH%" -o "%OUTPUT_DIR%" -m auto

REM 执行magic-pdf (添加引号确保路径正确处理)
magic-pdf -p "%PDF_PATH%" -o "%OUTPUT_DIR%" -m auto

if %ERRORLEVEL% NEQ 0 (
    echo 错误: magic-pdf处理失败!
    exit /b 1
)

echo.
echo magic-pdf处理启动成功，等待处理完成...

REM 等待处理完成，显示进度
for /l %%i in (1,1,%WAIT_TIME%) do (
    REM 每10秒更新一次进度
    set /a "mod=%%i %% 10"
    if !mod! equ 0 (
        set /a "percent=%%i * 100 / %WAIT_TIME%"
        echo 处理进度: !percent!%% (%%i/%WAIT_TIME% 秒)
    )
    timeout /t 1 /nobreak >nul
)

echo.
echo magic-pdf处理等待完成!

REM 第2阶段: 配置并运行main.py分析
echo.
echo === 第2阶段: 执行论文分析流程 ===
echo.

REM 创建临时main.py文件
set TEMP_MAIN=%SCRIPT_DIR%\temp_main.py
copy "%SCRIPT_DIR%\main.py" "%TEMP_MAIN%" >nul

REM 修改配置参数 (Windows中使用临时文件方式)
powershell -Command "(Get-Content '%TEMP_MAIN%') -replace 'PAPER_NAME = \"example\"', 'PAPER_NAME = \"%PAPER_NAME%\"' | Set-Content '%TEMP_MAIN%'"
powershell -Command "(Get-Content '%TEMP_MAIN%') -replace 'RUN_ALL_STEPS = False', 'RUN_ALL_STEPS = True' | Set-Content '%TEMP_MAIN%'"

REM 运行分析
echo 正在运行论文分析流程，这可能需要一段时间...
pushd "%PROJECT_ROOT%"
python "%TEMP_MAIN%"
popd

REM 检查分析结果
set REPORT_PATH=%SCRIPT_DIR%\output\%PAPER_NAME%\Final_Report.md
if exist "%REPORT_PATH%" (
    echo.
    echo ✅ 分析成功完成!
    echo 最终报告已生成: %REPORT_PATH%
) else (
    echo.
    echo ❌ 分析过程中可能出现问题，未找到最终报告。
    echo 请检查上述输出以获取更多信息。
)

REM 清理临时文件
if exist "%TEMP_MAIN%" del /q "%TEMP_MAIN%"

echo.
echo =====================================================
echo 分析流程结束
echo =====================================================
goto :eof

:show_help
echo 用法: run_paper_analysis.bat [选项] <PDF文件路径>
echo.
echo 选项:
echo   -h, --help        显示此帮助信息
echo   -w, --wait TIME   设置magic-pdf处理等待时间，单位秒（默认180秒）
echo.
echo 示例:
echo   run_paper_analysis.bat "path\to\my paper.pdf"
echo   run_paper_analysis.bat -w 300 "path\to\complex paper.pdf"
exit /b 1 