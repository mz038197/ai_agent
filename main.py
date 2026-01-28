import base64
import os
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage


def encode_image_to_base64(image_path):
    """將圖片編碼為 base64 格式"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def create_image_message(prompt, image_path):
    """創建包含圖片和文字的訊息"""
    image_data = encode_image_to_base64(image_path)
    
    return HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{image_data}"
            }
        ]
    )


def main():
    # 配置參數
    BASE_URL = "http://localhost:11434"
    MODEL = "gemma3:4b"  # 多模態模型（支援文字和圖片）
    TEMPERATURE = 0.7
    
    # 初始化多模態模型
    chat = ChatOllama(
        model=MODEL,
        base_url=BASE_URL,
        temperature=TEMPERATURE,
    )
    
    print("✅ 成功連接到 Ollama LLM!")
    print(f"📦 使用模型: {MODEL}")
    print("=" * 50)
    print("\n使用說明:")
    print("- 輸入文字進行對話")
    print("- 輸入 'image:圖片路徑 問題' 來分析圖片")
    print("  例如: image:photo.jpg 這張圖片裡有什麼？")
    print("- 輸入 'quit' 或 'exit' 退出")
    print("=" * 50)
    
    try:
        while True:
            user_input = input("\n你: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("拜拜！下次再見!")
                break
            
            if not user_input:
                continue
            
            # 檢查是否是圖片分析請求
            if user_input.startswith("image:"):
                try:
                    # 解析命令: image:路徑 問題
                    parts = user_input[6:].strip().split(maxsplit=1)
                    
                    if len(parts) < 2:
                        print("❌ 格式錯誤！請使用: image:圖片路徑 問題")
                        continue
                    
                    image_path = parts[0]
                    prompt = parts[1]
                    
                    # 檢查檔案是否存在
                    if not os.path.exists(image_path):
                        print(f"❌ 找不到圖片: {image_path}")
                        continue
                    
                    print(f"📷 正在分析圖片: {image_path}")
                    print(f"❓ 問題: {prompt}")
                    print("⏳ 處理中...")
                    
                    # 使用多模態模型處理圖片
                    message = create_image_message(prompt, image_path)
                    response = chat.invoke([message])
                    
                    print(f"\n模型: {response.content}")
                    
                except FileNotFoundError:
                    print(f"❌ 找不到圖片: {image_path}")
                except Exception as e:
                    print(f"❌ 錯誤: {str(e)}")
                    print(f"\n提示: 請確保模型支援多模態功能")
                    print(f"可嘗試其他視覺模型: ollama pull llava")
            else:
                # 普通文字對話
                message = HumanMessage(content=user_input)
                response = chat.invoke([message])
                print(f"\n模型: {response.content}")
            
    except KeyboardInterrupt:
        print("\n\n程式已中斷")
    except Exception as e:
        print(f"❌ 錯誤: {str(e)}")
        print("\n請確保:")
        print("1. Ollama 已安裝並運行 (ollama serve)")
        print(f"2. 已下載模型 (ollama pull {MODEL})")
        print(f"3. Ollama 服務運行在 {BASE_URL}")
        print(f"4. 模型支援多模態功能（文字+圖片）")


if __name__ == "__main__":
    main()
