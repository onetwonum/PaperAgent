import os
import json
from openai import OpenAI
from . import content_analyzer # 复用内容分析器中的函数
import config
from prompts import prompts

def analyze_paper_insight(paper_name):
    """
    对整篇论文进行最终的、全局性的分析，提炼优点、不足和深刻问题。
    """
    print(f"--- 开始为论文 '{paper_name}' 生成最终的全局分析报告 ---")
    
    # 定义路径
    output_dir = os.path.join('output', paper_name)
    content_analysis_path = os.path.join(output_dir, 'content_analysis.json')
    image_report_path = os.path.join(output_dir, 'image_analysis.md')
    structured_data_path = os.path.join(output_dir, 'structured_data.json')
    mapping_path = os.path.join(output_dir, 'section_mapping.json')
    result_path = os.path.join(output_dir, 'insights.json')

    # 1. 加载所有需要的数据
    print("--- 正在加载所有分析结果和原始数据... ---")
    content_analysis = content_analyzer.load_json(content_analysis_path, "内容分析")
    if not content_analysis:
        print(f"错误: 无法加载内容分析文件: {content_analysis_path}，无法继续。")
        return

    try:
        with open(image_report_path, 'r', encoding='utf-8') as f:
            image_analysis = f.read()
    except FileNotFoundError:
        print(f"警告: 找不到图片分析报告: {image_report_path}。分析将继续，但缺少图片信息。")
        image_analysis = "无图片分析报告。"

    structured_data = content_analyzer.load_json(structured_data_path, "结构化数据")
    section_mapping = content_analyzer.load_json(mapping_path, "章节映射")
    if not structured_data or not section_mapping:
        print("错误: 无法加载结构化数据或章节映射，无法提取引言和结论。")
        return

    # 2. 提取引言和结论的原文
    print("--- 正在提取引言和结论的原文... ---")
    all_sections_data = structured_data.get('sections', [])
    
    intro_titles = section_mapping.get("研究背景", [])
    conclusion_titles = section_mapping.get("总体结论", [])

    introduction_text, _ = content_analyzer.get_section_content(intro_titles, all_sections_data)
    conclusion_text, _ = content_analyzer.get_section_content(conclusion_titles, all_sections_data)

    if not introduction_text:
        print("警告: 未能提取到引言部分的原文。")
    if not conclusion_text:
        print("警告: 未能提取到结论部分的原文。")

    # 3. 准备Prompt
    all_summaries_str = json.dumps(content_analysis, indent=2, ensure_ascii=False)

    prompt = prompts.GENERATE_FINAL_INSIGHTS_PROMPT.format(
        all_summaries=all_summaries_str,
        all_figures_analysis=image_analysis,
        introduction_text=introduction_text or "未能提取到引言。",
        conclusion_text=conclusion_text or "未能提取到结论。"
    )

    # 4. 调用LLM
    print("--- 正在调用大模型进行最终分析，请稍候... ---")
    client = OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)
    
    try:
        response = client.chat.completions.create(
            model=config.LLM_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            # 注意：这个Prompt的输出是Markdown，所以不使用json_object模式
        )
        final_insights_content = response.choices[0].message.content
    except Exception as e:
        print(f"LLM调用失败: {e}")
        return

    # 5. 保存结果
    print(f"--- 正在保存最终分析报告... ---")
    # 直接保存Markdown文本
    try:
        with open(result_path.replace('.json', '.md'), 'w', encoding='utf-8') as f:
            f.write(final_insights_content)
        print(f"--- 全局分析报告已生成: {result_path.replace('.json', '.md')} ---")
    except IOError as e:
        print(f"错误: 无法写入最终分析报告: {e}") 