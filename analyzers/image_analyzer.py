import os
import json
import base64
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

def encode_image_to_base64(image_path):
    """将图片文件编码为Base64字符串。"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"错误: 找不到图片文件: {image_path}")
        return None
    except Exception as e:
        print(f"编码图片时发生错误: {e}")
        return None

def get_all_images_from_data(structured_data):
    """从结构化数据中递归提取所有图片的信息。"""
    images = []
    
    def recurse_sections(sections):
        for section in sections:
            if section.get('images'):
                images.extend(section['images'])
            if section.get('subsections'):
                recurse_sections(section['subsections'])

    if structured_data and structured_data.get('sections'):
        recurse_sections(structured_data['sections'])
    return images

def analyze_single_image(image_info, image_dir, llm_client):
    """使用视觉模型分析单张图片。"""
    image_path = os.path.join(image_dir, image_info['new_path'])
    
    print(f"--- 正在分析图片: {image_path} ---")
    
    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return f"无法加载图片: {image_path}"

    prompt = prompts.ANALYZE_FIGURE_PROMPT.format(figure_caption=image_info.get('caption', '无图注'))

    try:
        completion = llm_client.chat.completions.create(
            model=config.VISION_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are a helpful assistant."}]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            max_tokens=1024,
            stream=True
        )
        
        full_response = ""
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
        return full_response

    except Exception as e:
        print(f"调用视觉模型API时发生错误: {e}")
        return f"分析图片时出错: {e}"

def analyze_paper_images(paper_name):
    """
    为一篇论文生成完整的图片分析报告。
    """
    print(f"--- 开始为论文 '{paper_name}' 生成图片分析报告 ---")
    output_dir = os.path.join('output', paper_name)
    structured_data_path = os.path.join(output_dir, 'structured_data.json')
    report_path = os.path.join(output_dir, 'image_analysis.md')
    image_dir = os.path.join(output_dir) # 图片的相对路径从这里开始

    # 1. 加载数据
    structured_data = load_structured_data(structured_data_path)
    if not structured_data:
        print("分析中止，因为无法加载结构化数据。")
        return

    all_images = get_all_images_from_data(structured_data)
    if not all_images:
        print("论文中未找到图片，无需生成报告。")
        return

    # 2. 初始化LLM客户端
    if not config.VISION_API_KEY or "YOUR_" in config.VISION_API_KEY:
        print("错误: VISION_API_KEY 未在 .env 文件中配置。")
        return
        
    client = OpenAI(
        api_key=config.VISION_API_KEY,
        base_url=config.VISION_BASE_URL,
    )

    # 3. 分析所有图片并生成报告内容
    report_content = f"# 论文《{structured_data.get('paper_title', '未知标题')}》图表分析报告\n\n"
    
    total_images = len(all_images)
    print(f"--- 发现 {total_images} 张图片，开始逐一分析 ---")

    for i, image_info in enumerate(all_images):
        print(f"--- 正在处理图片 {i+1}/{total_images} ---")
        analysis_text = analyze_single_image(image_info, image_dir, client)
        
        report_content += f"## {image_info.get('id', '未命名图表')}\n\n"
        report_content += f"**原始图注:** {image_info.get('caption', '无')}\n\n"
        report_content += f"![{image_info.get('id')}]({image_info.get('new_path', '')})\n\n"
        report_content += f"### **模型分析结果:**\n\n"
        report_content += f"{analysis_text}\n\n"
        report_content += "---\n\n"

    # 4. 保存报告
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"--- 图片分析报告已生成: {report_path} ---")
    except IOError as e:
        print(f"错误: 无法写入报告文件: {e}") 