import os
import base64
from openai import OpenAI
import config

# --- Helper Functions ---

def encode_image_to_base64(image_path):
    """将图片文件编码为Base64字符串。"""
    if not os.path.exists(image_path):
        print(f"错误: 找不到测试图片文件: {image_path}")
        # 尝试创建一个虚拟的图片文件以继续
        try:
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            from PIL import Image
            img = Image.new('RGB', (60, 30), color = 'red')
            img.save(image_path)
            print("已创建一个临时的红色图片文件用于测试。")
        except ImportError:
            print("Pillow 未安装, 无法创建临时图片。请手动创建或提供图片。")
            return None
        except Exception as e:
            print(f"创建临时图片时出错: {e}")
            return None


    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"编码图片时发生错误: {e}")
        return None

# --- Test Functions ---

def test_language_model():
    """
    通过发送简单请求来测试语言模型API。
    """
    print("--- 1. 开始测试语言模型API ---")

    # 检查API密钥和基础URL
    if not config.LLM_API_KEY or "YOUR_" in config.LLM_API_KEY:
        print("错误: LLM_API_KEY 未在 .env 文件中找到或设置。")
        print("请根据 .env.example 创建 .env 文件并添加您的 API 密钥。")
        return False

    if not config.LLM_BASE_URL:
        print("错误: LLM_BASE_URL 未在 .env 文件中找到或设置。")
        print("请在 .env 文件中设置 LLM_BASE_URL。")
        return False

    print(f"使用模型: {config.LLM_MODEL_NAME}")
    print(f"使用URL: {config.LLM_BASE_URL}")

    # 初始化客户端
    try:
        client = OpenAI(
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL,
        )
    except Exception as e:
        print(f"初始化OpenAI客户端时出错: {e}")
        return False

    # 发送测试请求
    try:
        print("正在向语言模型发送请求...")
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "用中文说 'Hello, World!'",
                }
            ],
            model=config.LLM_MODEL_NAME,
        )
        print("请求成功!")
        print("模型响应:")
        print(chat_completion.choices[0].message.content)
        print("--- 语言模型API测试通过 ---")
        return True
    except Exception as e:
        print(f"发送请求时发生错误: {e}")
        print("--- 语言模型API测试失败 ---")
        return False


def test_vision_model():
    """
    通过发送一张本地图片来测试视觉模型API。
    """
    print("--- 2. 开始测试视觉模型API ---")

    # 检查API密钥和基础URL
    if not config.VISION_API_KEY or "YOUR_" in config.VISION_API_KEY:
        print("错误: VISION_API_KEY 未在 .env 文件中配置。")
        return False
    if not config.VISION_BASE_URL:
        print("错误: VISION_BASE_URL 未在 .env 文件中配置。")
        return False

    print(f"使用模型: {config.VISION_MODEL_NAME}")
    print(f"使用URL: {config.VISION_BASE_URL}")

    # 准备图片
    image_path = os.path.join('assets','Figure_1.jpg')
    print(f"准备图片: {image_path}")
    
    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        print("--- 视觉模型API测试失败 ---")
        return False

    # 初始化客户端并发送请求
    try:
        client = OpenAI(
            api_key=config.VISION_API_KEY,
            base_url=config.VISION_BASE_URL,
        )

        print("正在向视觉模型发送请求 (使用流式模式)...")
        completion = client.chat.completions.create(
            model=config.VISION_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "你是一个有用的助手。"}]
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
                        {"type": "text", "text": "这张图片里有什么？请用中文回答。"},
                    ],
                }
            ],
            max_tokens=1024,
            stream=True,
        )
        
        print("--- 请求成功！正在接收响应... ---")
        print("模型响应: ", end="")
        
        full_response = ""
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        
        print("\n--- 响应接收完毕 ---")
        print("--- 视觉模型API测试通过 ---")
        return True

    except Exception as e:
        print(f"\n--- 请求失败 ---")
        print(f"调用API时发生严重错误: {e}")
        print("--- 视觉模型API测试失败 ---")
        return False

if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    print("="*50)
    print("      开始进行API连通性测试")
    print("="*50)
    
    llm_ok = test_language_model()
    
    print("\n" + "-"*50 + "\n")
    
    vision_ok = test_vision_model()
    
    print("\n" + "="*50)
    print("        API连通性测试总结")
    print("="*50)
    print(f"语言模型 (LLM) API: {'✅  通讯正常' if llm_ok else '❌ 通讯失败'}")
    print(f"视觉模型 (Vision) API: {'✅  通讯正常' if vision_ok else '❌ 通讯失败'}")
    print("="*50)

    if not llm_ok or not vision_ok:
        print("\n提示: 请检查您的 .env 文件中的 API Key 和 Base URL 配置是否正确。")
        print("另外，请确保您的网络可以访问到对应的API服务，以及测试图片文件存在。") 