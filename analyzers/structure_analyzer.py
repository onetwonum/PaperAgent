import os
import json
import re
from openai import OpenAI
import config
from prompts import prompts

def load_structured_data(json_path):
    """从文件中加载结构化的论文数据。"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到结构化数据文件: {json_path}")
        return None
    except json.JSONDecodeError:
        print(f"错误: 解析JSON文件失败: {json_path}")
        return None

def format_toc_for_prompt(sections, indent=0):
    """将层级目录格式化为简单的缩进文本，以便LLM理解。"""
    toc_str = ""
    for section in sections:
        toc_str += "  " * indent + f"- {section['title']}\n"
        if section.get('subsections'):
            toc_str += format_toc_for_prompt(section['subsections'], indent + 1)
    return toc_str

def get_abstract(preamble):
    """从preamble中提取摘要部分。"""
    # 尝试找到 "Abstract" 及其后的内容
    match = re.search(r'#\s*Abstract\s*\n([\s\S]*)', preamble, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "摘要未找到。"

def create_section_mapping(structured_data, llm_client):
    """
    使用LLM将论文目录映射到标准分析结构。
    """
    paper_title = structured_data.get('paper_title', '未知标题')
    abstract = get_abstract(structured_data.get('preamble', ''))
    toc_string = format_toc_for_prompt(structured_data.get('sections', []))
    
    # 使用从prompts.py导入的模板
    prompt = prompts.MAPPING_SECTIONS_PROMPT.format(
        paper_title=paper_title,
        abstract=abstract,
        toc_string=toc_string
    )

    print("--- 正在调用LLM进行目录映射... ---")
    try:
        response = llm_client.chat.completions.create(
            model=config.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是一位顶级的科研助理，擅长快速分析计算机科学领域的学术论文结构。请严格按照要求输出JSON。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        mapping_json_str = response.choices[0].message.content
        print("--- LLM响应成功 ---")
        return json.loads(mapping_json_str)
    except Exception as e:
        print(f"调用LLM API时发生错误: {e}")
        return None

def analyze_paper_structure(paper_name):
    """
    分析单篇论文的主流程。
    """
    print(f"--- 开始分析论文结构: {paper_name} ---")
    # 路径现在指向根目录下的output文件夹
    output_dir = os.path.join('output', paper_name)
    structured_data_path = os.path.join(output_dir, 'structured_data.json')
    mapping_output_path = os.path.join(output_dir, 'section_mapping.json')

    # 1. 加载结构化数据
    print("1. 加载结构化JSON数据...")
    structured_data = load_structured_data(structured_data_path)
    if not structured_data:
        return

    # 2. 初始化LLM客户端
    if not config.LLM_API_KEY or "YOUR_" in config.LLM_API_KEY:
        print("错误: LLM_API_KEY 未在 .env 文件中配置。")
        return
    
    client = OpenAI(
        api_key=config.LLM_API_KEY,
        base_url=config.LLM_BASE_URL,
    )
    
    # 3. 创建章节映射
    print("2. 创建章节与标准结构的映射...")
    section_mapping = create_section_mapping(structured_data, client)

    # 4. 保存映射文件
    if section_mapping:
        print(f"3. 保存映射关系到 {mapping_output_path}...")
        try:
            with open(mapping_output_path, 'w', encoding='utf-8') as f:
                json.dump(section_mapping, f, indent=4, ensure_ascii=False)
            print("--- 结构分析完成 ---")
        except IOError as e:
            print(f"错误: 无法写入映射文件: {e}")
    else:
        print("未能生成章节映射，分析中止。")