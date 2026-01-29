"""
Chainlit UI 層
負責處理用戶界面交互，將業務邏輯委托給服務層
遵守單一職責原則 (Single Responsibility Principle)
"""
import chainlit as cl
from services import LLMService, ImageService


# 配置參數
CONFIG = {
    "MODEL": "gemma3:4b",
    "BASE_URL": "http://localhost:11434",
    "TEMPERATURE": 0.7
}


@cl.on_chat_start
async def start():
    """初始化聊天會話"""
    # 初始化服務層
    llm_service = LLMService(
        model=CONFIG["MODEL"],
        base_url=CONFIG["BASE_URL"],
        temperature=CONFIG["TEMPERATURE"]
    )
    
    # 將服務存儲在用戶會話中
    cl.user_session.set("llm_service", llm_service)
    
    # 獲取模型信息
    model_info = llm_service.get_model_info()
    
    # 歡迎訊息
    await cl.Message(
        content=f"👋 歡迎使用 AI 助手！\n\n"
                f"📦 當前模型: **{model_info['model']}**\n\n"
                f"💬 您可以：\n"
                f"- 輸入文字進行對話\n"
                f"- 📎 點擊輸入框旁的按鈕上傳圖片\n"
                f"- 🖱️ 或直接拖拉圖片到聊天區域",
    ).send()


@cl.on_message
async def handle_message(message: cl.Message):
    """
    處理用戶訊息（統一處理文字和圖片）
    UI層只負責接收輸入、顯示輸出，業務邏輯委托給服務層
    """
    # 獲取服務層實例
    llm_service = cl.user_session.get("llm_service")
    
    # 檢查是否有圖片附件
    images = [file for file in message.elements if "image" in file.mime]
    
    try:
        # 顯示處理中狀態
        status_text = "🔍 正在分析圖片..." if images else ""
        msg = cl.Message(content=status_text)
        await msg.send()
        
        # 準備參數
        user_text = message.content or ("請描述這張圖片" if images else "")
        image_url = None
        
        # 如果有圖片，轉換為 data URL
        if images:
            image_url = ImageService.create_image_data_url(images[0].path)
        
        # 統一調用 send_message（內部會自動判斷是否為多模態）
        response_text = await cl.make_async(llm_service.send_message)(
            content=user_text,
            image_url=image_url
        )
        
        # 更新 UI
        msg.content = response_text
        await msg.update()
            
    except Exception as e:
        await cl.Message(
            content=f"❌ 發生錯誤: {str(e)}\n\n請確保 Ollama 服務正在運行且模型已下載。"
        ).send()


@cl.on_settings_update
async def setup_agent(settings):
    """處理設置更新"""
    print("設置已更新:", settings)
