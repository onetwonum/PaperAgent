import os
import json
import re
from openai import OpenAI
import config
from prompts import prompts

# 定义一个可选的、推荐的分析框架。这不再是强制性的，而是作为指导。
DEFAULT_ANALYSIS_SCHEMA = {
    "研究背景": ["研究问题", "研究难点", "相关工作"]
}

def load_json(file_path, file_description):
    """通用JSON加载函数，文件不存在时返回空字典而不是None。"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {} # 如果文件不存在，返回空字典以便追加
    except json.JSONDecodeError:
        print(f"错误: 解析{file_description}文件失败: {file_path}。将创建一个新文件。")
        return {}
    except Exception as e:
        print(f"加载{file_description}文件时发生未知错误: {e}")
        return {}

def get_section_content(section_titles, all_sections_data):
    """
    根据标题列表，从结构化数据中递归地提取并合并所有相关章节的原文和图片ID。
    这个版本支持深入子章节进行查找。
    """
    content = ""
    figure_ids = []
    
    # 将所有目标标题转换为小写并去除首尾空格，便于匹配
    target_titles_set = {t.strip().lower() for t in section_titles}

    def recurse_extract(sections):
        """递归函数，用于遍历所有章节和子章节。"""
        nonlocal content
        for section in sections:
            # 检查当前章节（或子章节）的标题是否在我们的目标列表中
            current_title_normalized = section.get('title', '').strip().lower()
            
            # 使用更宽容的 `in` 匹配，检查目标标题集合中是否有任何一个标题是当前章节标题的子串
            # 或当前章节标题是目标标题的子串。这提供了双向的灵活性。
            should_extract = False
            for target_title in target_titles_set:
                if target_title in current_title_normalized or current_title_normalized in target_title:
                    should_extract = True
                    break

            if should_extract:
                # 提取文本
                content += section.get('content', '') + "\n\n"
                # 提取图片ID
                if section.get('images'):
                    for img in section['images']:
                        figure_ids.append(img.get('id'))
            
            # 无论当前章节是否匹配，都必须继续深入其子章节
            if 'subsections' in section and section['subsections']:
                recurse_extract(section['subsections'])

    # 从顶层章节开始递归
    recurse_extract(all_sections_data)
    
    return content.strip(), list(set(figure_ids)) # 对图片ID去重

def get_figure_analysis_from_report(figure_ids, report_path):
    """从完整的图片分析报告中，根据图片ID提取相关的分析内容。"""
    if not figure_ids:
        return "本部分不包含图表。"
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            full_report = f.read()
        
        relevant_analyses = []
        for fig_id in figure_ids:
            match = re.search(rf"## {re.escape(fig_id)}\n(.*?)\n---", full_report, re.DOTALL | re.IGNORECASE)
            if match:
                relevant_analyses.append(match.group(1).strip())
        
        return "\n\n".join(relevant_analyses) if relevant_analyses else "未能从报告中找到指定图表的分析。"
    except FileNotFoundError:
        return f"警告: 找不到图片分析报告: {report_path}"
    except Exception as e:
        return f"读取图片分析报告时出错: {e}"

def llm_call(client, prompt, response_format={"type": "json_object"}):
    """封装LLM调用。"""
    try:
        response = client.chat.completions.create(
            model=config.LLM_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format=response_format
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"LLM调用失败: {e}")
        return None

def analyze_single_section_dynamically(section_name, section_content, figures_analysis, client, log_path):
    """动态两步式分析单个部分，包含图文信息，并记录IO。"""
    
    def log_interaction(step_name, prompt, response):
        """将单次LLM交互写入日志文件的辅助函数。"""
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"--- START: {step_name} for '{section_name}' ---\n")
            f.write("--- PROMPT SENT TO LLM: ---\n")
            f.write(prompt)
            f.write("\n\n--- RESPONSE FROM LLM: ---\n")
            # 确保即使响应不是合法的JSON也能被记录
            if isinstance(response, dict) or isinstance(response, list):
                f.write(json.dumps(response, indent=2, ensure_ascii=False))
            elif response:
                f.write(str(response))
            else:
                f.write("NO RESPONSE OR ERROR")
            f.write(f"\n--- END: {step_name} for '{section_name}' ---\n\n\n")

    analysis_points = DEFAULT_ANALYSIS_SCHEMA.get(section_name)

    # 智能分流：如果存在预设框架，则跳过第一步
    if analysis_points:
        print(f"--- 检测到 '{section_name}' 的预设分析框架，跳过动态生成步骤。 ---")
    else:
        # --- 步骤1：生成分析框架 ---
        print(f"--- 步骤1: 为 '{section_name}' 生成动态分析框架... ---")
        
        prompt_step1 = prompts.SMART_ANALYZE_SECTION_PROMPT.format(
            section_name=section_name,
            related_figures_analysis=figures_analysis,
            section_content=section_content
        )
        framework_response = llm_call(client, prompt_step1)
        log_interaction("Step 1: Generate Framework", prompt_step1, framework_response) # 记录交互

        if not framework_response or "analysis_points" not in framework_response or not framework_response["analysis_points"]:
            print(f"警告: 未能为 '{section_name}' 生成有效的分析框架。跳过此部分。")
            return None
        
        analysis_points = framework_response["analysis_points"]

    print(f"--- '{section_name}' 的分析要点: {analysis_points} ---")

    # --- 步骤2：进行深入分析 ---
    print(f"--- 步骤2: 为 '{section_name}' 进行深入内容分析... ---")
    prompt_step2 = prompts.DEEP_ANALYZE_PROMPT.format(
        section_name=section_name,
        analysis_points_str="\n".join([f"- {p}" for p in analysis_points]),
        related_figures_analysis=figures_analysis,
        section_content=section_content
    )
    deep_analysis_response = llm_call(client, prompt_step2)
    log_interaction("Step 2: Deep Analysis", prompt_step2, deep_analysis_response) # 记录交互

    if not deep_analysis_response or "analysis_details" not in deep_analysis_response:
        print(f"警告: 未能对 '{section_name}' 进行深入分析。")
        return None

    print(f"--- '{section_name}' 分析完成 ---")
    return {section_name: deep_analysis_response["analysis_details"]}
    
def analyze_paper_content(paper_name):
    """对论文进行分块内容分析的主流程，并实现分步保存。"""
    print(f"--- 开始对论文 '{paper_name}' 进行智能图文内容分析 (支持断点续传) ---")
    output_dir = os.path.join('output', paper_name)
    mapping_path = os.path.join(output_dir, 'section_mapping.json')
    data_path = os.path.join(output_dir, 'structured_data.json')
    image_report_path = os.path.join(output_dir, 'image_analysis.md')
    result_path = os.path.join(output_dir, 'content_analysis.json')
    log_path = os.path.join(output_dir, 'llm_io_log.txt')

    # 在分析开始时清空旧的日志文件，以便于本次运行的调试
    if os.path.exists(log_path):
        os.remove(log_path)
        print(f"--- 已清空旧的日志文件: {log_path} ---")

    # 1. 加载所需文件
    section_mapping = load_json(mapping_path, "章节映射")
    structured_data = load_json(data_path, "结构化数据")
    if not section_mapping or not structured_data:
        print("错误：无法加载章节映射或结构化数据，分析中止。")
        return

    # 尝试加载已有的分析结果，实现断点续传
    full_analysis = load_json(result_path, "内容分析结果")

    # 2. 初始化客户端
    client = OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)

    # 3. 逐部分进行分析
    all_sections_data = structured_data.get('sections', [])
    for section_name, section_titles in section_mapping.items():
        # 如果已有分析结果，则跳过
        if section_name in full_analysis:
            print(f"--- 已检测到 '{section_name}' 的分析结果，跳过 ---")
            continue

        if not section_titles:
            continue
        
        section_content, figure_ids = get_section_content(section_titles, all_sections_data)
        if not section_content:
            continue

        figures_analysis = get_figure_analysis_from_report(figure_ids, image_report_path)
            
        analysis_result = analyze_single_section_dynamically(section_name, section_content, figures_analysis, client, log_path)
        
        if analysis_result:
            full_analysis.update(analysis_result)
            # 每完成一部分，就立即保存一次
            print(f"--- 已完成 '{section_name}' 的分析，立即保存进度... ---")
            try:
                with open(result_path, 'w', encoding='utf-8') as f:
                    json.dump(full_analysis, f, indent=4, ensure_ascii=False)
            except IOError as e:
                print(f"错误: 无法写入分析文件: {e}")

    print("--- 智能图文内容分析全部完成！ ---") 