import chainlit as cl
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
import base64


def encode_image_to_base64(image_path):
    """將圖片編碼為 base64 格式"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


@cl.on_chat_start
async def start():
    """初始化聊天會話"""
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
    
    # 將模型存儲在用戶會話中
    cl.user_session.set("chat", chat)
    cl.user_session.set("model", MODEL)
    
    # 歡迎訊息
    await cl.Message(
        content=f"👋 歡迎使用 AI 助手！\n\n📦 當前模型: **{MODEL}**\n\n💬 您可以：\n- 輸入文字進行對話\n- 📎 點擊輸入框旁的按鈕上傳圖片\n- 🖱️ 或直接拖拉圖片到聊天區域",
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """處理用戶訊息"""
    # 獲取聊天模型
    chat = cl.user_session.get("chat")
    
    # 檢查是否有圖片附件
    print(f"收到訊息，elements 數量: {len(message.elements)}")
    if message.elements:
        for elem in message.elements:
            print(f"元素類型: {elem.mime if hasattr(elem, 'mime') else 'unknown'}")
    
    images = [file for file in message.elements if "image" in file.mime]
    
    try:
        if images:
            # 處理圖片訊息
            image_file = images[0]  # 取第一張圖片
            
            # 創建圖片元素以在界面中顯示
            image_element = cl.Image(
                name="uploaded_image",
                path=image_file.path
            )
            
            # 顯示處理中的訊息（附帶圖片）
            msg = cl.Message(
                content="🔍 正在分析圖片...",
                elements=[image_element]
            )
            await msg.send()
            
            # 讀取並編碼圖片
            image_data = encode_image_to_base64(image_file.path)
            
            # 創建包含圖片的訊息
            user_message = HumanMessage(
                content=[
                    {"type": "text", "text": message.content or "請描述這張圖片"},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{image_data}"
                    }
                ]
            )
            
            # 獲取模型回應
            response = await cl.make_async(chat.invoke)([user_message])
            
            # 更新訊息內容（保留圖片顯示）
            msg.content = response.content
            msg.elements = [image_element]
            await msg.update()
            
        else:
            # 處理純文字訊息
            msg = cl.Message(content="")
            await msg.send()
            
            # 創建文字訊息
            user_message = HumanMessage(content=message.content)
            
            # 獲取模型回應
            response = await cl.make_async(chat.invoke)([user_message])
            
            # 更新訊息內容
            msg.content = response.content
            await msg.update()
            
    except Exception as e:
        await cl.Message(
            content=f"❌ 發生錯誤: {str(e)}\n\n請確保 Ollama 服務正在運行且模型已下載。"
        ).send()


@cl.on_settings_update
async def setup_agent(settings):
    """處理設置更新"""
    print("設置已更新:", settings)
