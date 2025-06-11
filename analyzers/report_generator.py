import os
import json

def generate_final_report(paper_name):
    """
    整合所有分析结果，生成一份完整的、结构化的Markdown研究报告。
    """
    print(f"--- 开始为论文 '{paper_name}' 生成最终的整合报告 ---")

    # 1. 定义所有需要读取的文件的路径
    output_dir = os.path.join('output', paper_name)
    paper_title_path = os.path.join(output_dir, 'structured_data.json') # 从这里获取论文标题
    mapping_path = os.path.join(output_dir, 'section_mapping.json')
    content_analysis_path = os.path.join(output_dir, 'content_analysis.json')
    image_report_path = os.path.join(output_dir, 'image_analysis.md')
    insights_path = os.path.join(output_dir, 'insights.md')
    final_report_path = os.path.join(output_dir, 'Final_Report.md')
    
    # 2. 加载所有数据
    print("--- 正在加载所有分析产物... ---")
    try:
        with open(paper_title_path, 'r', encoding='utf-8') as f:
            paper_title = json.load(f).get('paper_title', '未知标题')
        with open(mapping_path, 'r', encoding='utf-8') as f:
            section_mapping = json.load(f)
        with open(content_analysis_path, 'r', encoding='utf-8') as f:
            content_analysis = json.load(f)
        with open(image_report_path, 'r', encoding='utf-8') as f:
            image_analysis = f.read()
        with open(insights_path, 'r', encoding='utf-8') as f:
            insights_analysis = f.read()
    except FileNotFoundError as e:
        print(f"错误: 缺少必要的分析文件 {e.filename}，无法生成最终报告。")
        return
    except Exception as e:
        print(f"加载文件时发生未知错误: {e}")
        return

    # 3. 开始构建最终报告的Markdown字符串
    print("--- 正在拼接最终报告... ---")
    report_parts = []

    # --- 报告头部 ---
    report_parts.append(f"# 论文分析报告：{paper_title}\n\n")

    # --- 报告主体：按章节顺序整合 ---
    report_parts.append("\n## 章节深度分析\n\n")
    for section_name in section_mapping.keys():
        if section_name in content_analysis:
            report_parts.append(f"### {section_name}\n\n")
            analysis_details = content_analysis[section_name]
            for point, detail in analysis_details.items():
                report_parts.append(f"- **{point}:** {detail}\n")
            report_parts.append("\n")
    report_parts.append("\n---\n\n")

    report_parts.append("## 全局洞察：核心观点总结\n\n")
    report_parts.append(insights_analysis)
    report_parts.append("\n---\n\n")

    # --- 报告附录：图表分析 ---
    # 从原始图片分析报告中移除主标题，避免重复
    image_analysis_body = image_analysis.split('\n', 1)[-1].strip()
    report_parts.append("## 附录：重点图表分析详情\n\n")
    report_parts.append(image_analysis_body)

    # 4. 合并并写入文件
    final_report_content = "".join(report_parts)
    try:
        with open(final_report_path, 'w', encoding='utf-8') as f:
            f.write(final_report_content)
        print(f"--- 最终报告已成功生成: {final_report_path} ---")
    except IOError as e:
        print(f"错误: 无法写入最终报告文件: {e}") 