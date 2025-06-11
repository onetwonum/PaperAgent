#!/bin/bash

# =============================================
# PaperAgent 论文分析一键式流程脚本
# 用途：自动处理从PDF到分析报告的全部流程
# =============================================

# 显示帮助信息
show_help() {
    echo "用法: bash run_paper_analysis.sh [选项] <PDF文件路径>"
    echo ""
    echo "选项:"
    echo "  -h, --help        显示此帮助信息"
    echo "  -w, --wait TIME   设置magic-pdf处理等待时间，单位秒（默认180秒）"
    echo ""
    echo "示例:"
    echo "  bash run_paper_analysis.sh \"path/to/my paper.pdf\""
    echo "  bash run_paper_analysis.sh -w 300 \"path/to/complex paper.pdf\""
    exit 1
}

# 处理参数
PDF_PATH=""
WAIT_TIME=180

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -w|--wait)
            WAIT_TIME="$2"
            shift # 移过参数名
            shift # 移过参数值
            ;;
        *)
            PDF_PATH="$1"
            shift
            ;;
    esac
done

# 检查是否提供了PDF路径
if [ -z "$PDF_PATH" ]; then
    echo "错误: 请提供PDF文件路径!"
    show_help
fi

# 检查文件是否存在
if [ ! -f "$PDF_PATH" ]; then
    echo "错误: PDF文件不存在: $PDF_PATH"
    exit 1
fi

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PAPER_NAME=$(basename "$PDF_PATH" .pdf)

# 清理论文名称（替换不合法字符为下划线）
PAPER_NAME=$(echo "$PAPER_NAME" | sed 's/[^a-zA-Z0-9_]/_/g')

echo "====================================================="
echo "PaperAgent 论文分析流程"
echo "====================================================="
echo "PDF文件: $PDF_PATH"
echo "论文名称: $PAPER_NAME"
echo "等待时间: $WAIT_TIME 秒"
echo "====================================================="

# 第1阶段: magic-pdf 预处理
echo ""
echo "=== 第1阶段: 使用magic-pdf处理PDF文件 ==="
echo ""

OUTPUT_DIR="$SCRIPT_DIR/pdf_preprocess/output"
MAGIC_PDF_CMD="magic-pdf -p \"$PDF_PATH\" -o \"$OUTPUT_DIR\" -m auto"

echo "执行命令: $MAGIC_PDF_CMD"
eval $MAGIC_PDF_CMD

if [ $? -ne 0 ]; then
    echo "错误: magic-pdf处理失败!"
    exit 1
fi

echo ""
echo "magic-pdf处理启动成功，等待处理完成..."

# 等待处理完成，显示进度条
for ((i=1; i<=$WAIT_TIME; i++)); do
    # 每10秒更新一次进度
    if [ $((i % 10)) -eq 0 ] || [ $i -eq $WAIT_TIME ]; then
        percent=$(echo "scale=1; $i * 100 / $WAIT_TIME" | bc)
        echo -ne "处理进度: $percent% ($i/$WAIT_TIME 秒)\r"
    fi
    sleep 1
done

echo ""
echo "magic-pdf处理等待完成!"

# 第2阶段: 配置并运行main.py分析
echo ""
echo "=== 第2阶段: 执行论文分析流程 ==="
echo ""

# 创建临时main.py文件
TEMP_MAIN="$SCRIPT_DIR/temp_main.py"
cp "$SCRIPT_DIR/main.py" "$TEMP_MAIN"

# 修改配置参数
if [[ "$OSTYPE" == "darwin"* ]]; then  # macOS
    sed -i "" "s/PAPER_NAME = \"example\"/PAPER_NAME = \"$PAPER_NAME\"/" "$TEMP_MAIN"
    sed -i "" "s/RUN_ALL_STEPS = False/RUN_ALL_STEPS = True/" "$TEMP_MAIN"
else  # Linux and others
    sed -i "s/PAPER_NAME = \"example\"/PAPER_NAME = \"$PAPER_NAME\"/" "$TEMP_MAIN"
    sed -i "s/RUN_ALL_STEPS = False/RUN_ALL_STEPS = True/" "$TEMP_MAIN"
fi

# 运行分析
echo "正在运行论文分析流程，这可能需要一段时间..."
(cd "$PROJECT_ROOT" && python "$TEMP_MAIN")

# 检查分析结果
REPORT_PATH="$SCRIPT_DIR/output/$PAPER_NAME/Final_Report.md"
if [ -f "$REPORT_PATH" ]; then
    echo ""
    echo "✅ 分析成功完成!"
    echo "最终报告已生成: $REPORT_PATH"
else
    echo ""
    echo "❌ 分析过程中可能出现问题，未找到最终报告。"
    echo "请检查上述输出以获取更多信息。"
fi

# 清理临时文件
rm -f "$TEMP_MAIN"

echo ""
echo "====================================================="
echo "分析流程结束"
echo "=====================================================" 