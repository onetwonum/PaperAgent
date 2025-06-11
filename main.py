import os
import sys
import argparse

from analyzers.structure_analyzer import analyze_paper_structure
from analyzers.image_analyzer import analyze_paper_images
from analyzers.content_analyzer import analyze_paper_content
from analyzers.insight_analyzer import analyze_paper_insight
from analyzers.report_generator import generate_final_report
from pdf_preprocess.main_parser import process_paper

def main():
    """
    项目的主入口。
    支持两种运行模式：
    1. 分步模式 - 取消注释您需要执行的步骤
    2. 全流程模式 - 设置 RUN_ALL_STEPS = True
    """
    # =========================== 配置区 ===========================
    # 在这里设置您要处理的论文名称（不含.pdf后缀）
    # 注意：这应与 magic-pdf 处理后的输出目录名称相同
    PAPER_NAME = "1"
    
    # 设置为 True 可一键执行从预处理到生成最终报告的全部步骤
    RUN_ALL_STEPS = True
    
    # =========================== 执行区 ===========================
    if RUN_ALL_STEPS:
        print("=== 开始执行全流程分析 ===")
        # 第1步：预处理PDF文件
        process_paper(PAPER_NAME)
        # 第2步：结构分析与映射
        analyze_paper_structure(PAPER_NAME)
        # 第3步：图片提取与分析
        analyze_paper_images(PAPER_NAME)
        # 第4步：章节内容深度分析
        analyze_paper_content(PAPER_NAME)
        # 第5步：全局洞察分析
        analyze_paper_insight(PAPER_NAME)
        # 第6步：生成最终报告
        generate_final_report(PAPER_NAME)
        print("=== 全流程分析完成！最终报告已生成 ===")
    else:
        # 分步执行模式：取消注释您想要执行的步骤
        
        # --- 第1步：预处理PDF ---
        # 将PDF文件解析为结构化数据，提取图片、文本和章节关系
        # process_paper(PAPER_NAME)
        
        # --- 第2步：结构分析与映射 ---
        # 分析论文结构并创建章节映射关系
        # analyze_paper_structure(PAPER_NAME)
        
        # --- 第3步：图片提取与分析 ---
        # 分析论文中的图片，生成解释和洞察
        # analyze_paper_images(PAPER_NAME)
        
        # --- 第4步：章节内容深度分析 ---
        # 对每个章节的内容进行深入分析和摘要
        # analyze_paper_content(PAPER_NAME)
        
        # --- 第5步：全局洞察分析 ---
        # 生成论文的优点、不足与关键问题分析
        # analyze_paper_insight(PAPER_NAME)
        
        # --- 第6步：生成最终报告 ---
        # 整合所有分析结果，生成最终的综合报告
        generate_final_report(PAPER_NAME)


if __name__ == '__main__':
    main() 