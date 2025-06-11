import os
import re
import json
import shutil
from PyPDF2 import PdfReader

def get_toc_from_pdf(pdf_path):
    """
    从PDF文件中提取目录（Table of Contents）。
    返回一个扁平的列表，其中每个条目包含标题、页码和缩进级别。
    """
    try:
        reader = PdfReader(pdf_path)
        outlines = reader.outline
        if not outlines:
            print(f"警告: PDF '{pdf_path}' 没有可提取的目录(outline)。")
            return []
        
        return get_toc_recursive(reader, outlines)
    except FileNotFoundError:
        print(f"错误: PDF文件未找到于 '{pdf_path}'")
        return []
    except Exception as e:
        print(f"处理PDF时发生错误: {e}")
        return []

def get_toc_recursive(reader, outlines, indent=0):
    """
    通过递归遍历PDF的outline来提取目录。
    """
    toc = []
    for item in outlines:
        if isinstance(item, list):
            toc.extend(get_toc_recursive(reader, item, indent + 1))
        else:
            try:
                page_num = reader.get_page_number(item.page) + 1
                toc.append({'title': item.title, 'page': page_num, 'indent': indent})
            except Exception as e:
                print(f"因错误跳过一个目录项 '{item.title}': {e}")
                continue
    return toc

def build_toc_hierarchy(flat_toc):
    """
    将扁平的TOC列表转换为嵌套的层级结构。
    """
    if not flat_toc:
        return []
    
    hierarchical_toc = []
    parent_stack = []  # 存放 (节点, 缩进级别) 的栈

    for item in flat_toc:
        node = {
            'title': item['title'],
            'page': item['page'],
            'level': item['indent'] + 1,
            'content': '',
            'images': [],
            'tables': [],
            'subsections': []
        }
        
        # 弹出栈直到找到当前节点的父节点
        while parent_stack and parent_stack[-1][1] >= item['indent']:
            parent_stack.pop()
            
        if not parent_stack:
            hierarchical_toc.append(node)
        else:
            parent_node = parent_stack[-1][0]
            parent_node['subsections'].append(node)
            
        parent_stack.append((node, item['indent']))
        
    return hierarchical_toc

def parse_md_content(md_path):
    """
    解析Markdown文件，将其分割成带有标题、级别和内容的章节列表。
    """
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: Markdown文件未找到于 '{md_path}'")
        return None, []

    # 按标题分割全文
    # 使用正则表达式查找所有以'#'开头的行
    # (?=...) 是一个正向前瞻，它匹配但不消耗字符，所以分隔符会保留在结果中
    parts = re.split(r'(?=\n#+\s)', '\n' + content)
    
    sections = []
    preamble = ""
    
    if parts:
        # 第一部分通常是摘要前的任何内容（标题、作者等）
        preamble = parts[0].strip()
        
        for part in parts[1:]:
            part = part.strip()
            if not part:
                continue
            
            try:
                header_match = re.match(r'^(#+)\s+(.*)', part)
                if not header_match:
                    continue

                level = len(header_match.group(1))
                title = header_match.group(2).split('\n')[0].strip()
                
                sections.append({
                    'title': title,
                    'level': level,
                    'raw_content': part
                })
            except IndexError:
                print(f"警告: 无法解析Markdown部分: '{part[:50]}...'")

    return preamble, sections

def clean_title(title):
    """
    清理标题以便于匹配：移除数字编号、转小写、移除标点符号。
    例如："2.1. Overview" -> "overview"
    """
    # 移除前面的数字和点
    normalized = re.sub(r'^\d+([.\d\s]+)?', '', title).strip()
    # 移除大部分标点符号，保留空格
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return normalized.lower()

def populate_content_and_assets(toc_nodes, md_sections, md_path, dest_image_dir, used_indices):
    """
    递归地为层级目录填充内容和处理图片/表格。
    图片将被从源目录复制并重命名到目标目录。
    """
    source_md_dir = os.path.dirname(md_path)
    for node in toc_nodes:
        cleaned_node_title = clean_title(node['title'])
        
        for i, section in enumerate(md_sections):
            if i in used_indices:
                continue

            if cleaned_node_title == clean_title(section['title']):
                content = section['raw_content']
                images_found = []
                pattern = re.compile(r'!\[.*?\]\((.*?)\)\s*\n(Figure|Table)\s*([\d\.]+):\s*(.*)')
                
                for match in pattern.finditer(content):
                    original_path_from_md = match.group(1)
                    asset_type = match.group(2)
                    asset_id_num = match.group(3).replace('.', '_')
                    caption = f"{asset_type} {match.group(3)}: {match.group(4).strip()}"
                    
                    _, extension = os.path.splitext(original_path_from_md)
                    new_filename = f"{asset_type}_{asset_id_num}{extension}"
                    new_path_relative = os.path.join('images', new_filename)
                    
                    source_image_path = os.path.join(source_md_dir, original_path_from_md)
                    dest_image_path = os.path.join(dest_image_dir, new_filename)

                    try:
                        if os.path.exists(source_image_path):
                            os.makedirs(dest_image_dir, exist_ok=True)
                            shutil.copy2(source_image_path, dest_image_path) # 使用copy2保留元数据
                        else:
                            print(f"警告: 找不到源图片文件: {source_image_path}")

                    except OSError as e:
                        print(f"错误: 复制文件 '{source_image_path}' 失败: {e}")

                    content = content.replace(original_path_from_md, new_path_relative)
                    
                    images_found.append({
                        'id': f"{asset_type} {match.group(3)}",
                        'new_path': new_path_relative,
                        'original_path': original_path_from_md,
                        'caption': caption
                    })
                
                node['content'] = content
                node['images'] = images_found
                used_indices.add(i)
                break
        
        if node['subsections']:
            populate_content_and_assets(node['subsections'], md_sections, md_path, dest_image_dir, used_indices)

def process_paper(paper_name):
    """
    主处理函数，协调整个流程。
    读取pdf_preprocess/output中的原始产物，
    将处理后的结果存放到顶层的output/中。
    """
    print(f"--- 开始处理论文: {paper_name} ---")

    # 所有路径都应从项目根目录（'paperagent'）开始构建
    
    # 源文件路径
    source_pdf_path = os.path.join('pdf_preprocess', 'pdf', f'{paper_name}.pdf')
    source_output_dir = os.path.join('pdf_preprocess', 'output', paper_name, 'auto')
    source_md_path = os.path.join(source_output_dir, f'{paper_name}.md')

    # 目标路径
    dest_paper_dir = os.path.join('output', paper_name)
    dest_image_dir = os.path.join(dest_paper_dir, 'images')
    dest_json_path = os.path.join(dest_paper_dir, 'structured_data.json')

    os.makedirs(dest_paper_dir, exist_ok=True)
    
    print("1. 从PDF提取目录...")
    flat_toc = get_toc_from_pdf(source_pdf_path)
    if not flat_toc:
        return
        
    print("2. 构建层级目录结构...")
    structured_toc = build_toc_hierarchy(flat_toc)

    print("3. 解析Markdown文件...")
    preamble, md_sections = parse_md_content(source_md_path)
    if not md_sections:
        return

    print("4. 匹配目录、填充内容并复制/重命名图片...")
    used_indices = set()
    populate_content_and_assets(structured_toc, md_sections, source_md_path, dest_image_dir, used_indices)

    final_data = {
        'paper_title': preamble.split('\n')[0].replace('#', '').strip(),
        'preamble': preamble,
        'sections': structured_toc
    }
    
    print(f"5. 保存结构化数据到 {dest_json_path}...")
    try:
        with open(dest_json_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
        print("--- 处理完成 ---")
    except IOError as e:
        print(f"错误: 无法写入JSON文件: {e}")

if __name__ == '__main__':
    # 调整这里的路径，使其在直接运行时也能找到example.pdf
    # 假设脚本在 paperagent/pdf_preprocess/ 目录下运行，需要向上回溯一级
    os.chdir('..') # 返回到 paperagent/ 根目录
    PAPER_TO_PROCESS = 'example'
    process_paper(PAPER_TO_PROCESS) 