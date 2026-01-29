"""
Chainlit UI 層
負責處理用戶界面交互，將業務邏輯委托給服務層
遵守單一職責原則 (Single Responsibility Principle)
"""
import chainlit as cl
from services import (
    LLMService, 
    ImageService,
    DocumentService,
    VectorStoreService,
    RAGService
)


# 配置參數
CONFIG = {
    "MODEL": "gemma3:4b",
    "BASE_URL": "http://localhost:11434",
    "TEMPERATURE": 0.7,
    "EMBEDDING_MODEL": "nomic-embed-text",
    "CHROMA_DB_PATH": "./chroma_db",
    "SYSTEM_PROMPT": """你是一個專業、友善的 AI 助手，具備以下特點：
- 使用繁體中文回答
- 提供準確、清晰、有幫助的回答
- 當處理文檔相關問題時，嚴格基於提供的上下文回答
- 如果不確定或信息不足，會明確說明
- 以專業但親切的語氣與用戶交流"""
}


@cl.on_chat_start
async def start():
    """初始化聊天會話"""
    # 初始化 LLM 服務
    llm_service = LLMService(
        model=CONFIG["MODEL"],
        base_url=CONFIG["BASE_URL"],
        temperature=CONFIG["TEMPERATURE"],
        system_prompt=CONFIG["SYSTEM_PROMPT"]
    )
    
    # 初始化 RAG 相關服務
    doc_service = DocumentService(chunk_size=1000, chunk_overlap=200)
    vector_service = VectorStoreService(
        persist_directory=CONFIG["CHROMA_DB_PATH"],
        embedding_model=CONFIG["EMBEDDING_MODEL"],
        base_url=CONFIG["BASE_URL"]
    )
    rag_service = RAGService(
        document_service=doc_service,
        vector_store_service=vector_service,
        llm_service=llm_service,
        default_k=4
    )
    
    # 將服務存儲在用戶會話中
    cl.user_session.set("llm_service", llm_service)
    cl.user_session.set("rag_service", rag_service)
    
    # 獲取模型和知識庫信息
    model_info = llm_service.get_model_info()
    kb_stats = rag_service.get_knowledge_base_stats()
    
    # 歡迎訊息
    await cl.Message(
        content=f"👋 歡迎使用 AI 助手！\n\n"
                f"📦 **當前模型:** {model_info['model']}\n"
                f"📚 **知識庫:** {kb_stats['total_chunks']} 個文檔塊\n\n"
                f"💬 **您可以：**\n"
                f"- 💭 輸入文字進行對話（自動使用知識庫）\n"
                f"- 📄 上傳文件（PDF/TXT/Markdown）建立知識庫\n"
                f"- 🖼️ 上傳圖片進行視覺分析\n"
                f"- 📊 輸入 `/stats` 查看知識庫統計\n"
                f"- 🗑️ 輸入 `/clear` 清空知識庫",
    ).send()


@cl.on_message
async def handle_message(message: cl.Message):
    """
    處理用戶訊息（統一處理文字、圖片和文檔）
    UI層只負責接收輸入、顯示輸出，業務邏輯委托給服務層
    """
    # 獲取服務層實例
    llm_service = cl.user_session.get("llm_service")
    rag_service = cl.user_session.get("rag_service")
    
    # 檢查命令
    if message.content:
        content_lower = message.content.lower().strip()
        
        # 統計命令
        if content_lower == "/stats":
            stats = rag_service.get_knowledge_base_stats()
            await cl.Message(
                content=f"📊 **知識庫統計**\n\n"
                        f"- 文檔塊總數：{stats['total_chunks']}\n"
                        f"- 集合名稱：{stats['collection_name']}\n"
                        f"- 嵌入模型：{stats['embedding_model']}\n"
                        f"- 支援格式：{', '.join(stats['supported_formats'])}"
            ).send()
            return
        
        # 清空命令
        if content_lower == "/clear":
            await cl.AskActionMessage(
                content="確定要清空整個知識庫嗎？此操作無法撤銷。",
                actions=[
                    cl.Action(name="confirm", payload={"action": "confirm"}, label="✅ 確定清空"),
                    cl.Action(name="cancel", payload={"action": "cancel"}, label="❌ 取消"),
                ],
            ).send()
            return
    
    # 分類附件
    images = [file for file in message.elements if "image" in file.mime]
    documents = [file for file in message.elements 
                 if file.mime in ["application/pdf", "text/plain", "text/markdown"]
                 or file.name.endswith(('.pdf', '.txt', '.md', '.markdown'))]
    
    try:
        # 處理文檔上傳
        if documents:
            await _handle_document_upload(message, documents, rag_service)
        
        # 處理圖片
        elif images:
            await _handle_image_message(message, images[0], llm_service)
        
        # 處理純文字（使用 RAG）
        else:
            await _handle_text_with_rag(message, rag_service)
            
    except Exception as e:
        await cl.Message(
            content=f"❌ 發生錯誤: {str(e)}\n\n請確保 Ollama 服務正在運行且模型已下載。"
        ).send()


async def _handle_document_upload(
    message: cl.Message,
    documents: list,
    rag_service: RAGService
):
    """處理文檔上傳"""
    msg = cl.Message(content="📄 正在處理文件...")
    await msg.send()
    
    results = []
    for doc_file in documents:
        try:
            result = await cl.make_async(rag_service.ingest_file)(doc_file.path)
            results.append(f"✅ **{doc_file.name}**\n   - 已添加 {result['chunks_count']} 個文檔塊")
        except Exception as e:
            results.append(f"❌ **{doc_file.name}**\n   - 錯誤：{str(e)}")
    
    # 獲取更新後的統計
    stats = rag_service.get_knowledge_base_stats()
    
    msg.content = "📚 **文檔處理完成**\n\n" + "\n\n".join(results)
    msg.content += f"\n\n📊 知識庫現有 **{stats['total_chunks']}** 個文檔塊"
    
    if message.content:
        msg.content += f"\n\n💬 現在回答您的問題..."
        await msg.update()
        
        # 使用上傳的文檔回答問題
        response = await cl.make_async(rag_service.query_with_context)(
            message.content,
            k=4
        )
        
        msg.content += f"\n\n{response}"
    
    await msg.update()


async def _handle_text_with_rag(message: cl.Message, rag_service: RAGService):
    """使用 RAG 處理純文字訊息"""
    msg = cl.Message(content="")
    await msg.send()
    
    # 使用 RAG 查詢（會自動檢索知識庫）
    response = await cl.make_async(rag_service.query_with_context)(
        message.content,
        k=4,
        use_mmr=False,
        include_sources=True
    )
    
    msg.content = response
    await msg.update()


async def _handle_image_message(
    message: cl.Message,
    image_file,
    llm_service: LLMService
):
    """處理圖片訊息"""
    msg = cl.Message(content="🔍 正在分析圖片...")
    await msg.send()
    
    # 轉換圖片為 data URL
    image_url = ImageService.create_image_data_url(image_file.path)
    user_text = message.content or "請描述這張圖片"
    
    # 調用 LLM（圖片不使用 RAG）
    response = await cl.make_async(llm_service.send_message)(
        content=user_text,
        image_url=image_url
    )
    
    msg.content = response
    await msg.update()


@cl.action_callback("confirm")
async def on_action(action: cl.Action):
    """處理清空知識庫確認"""
    rag_service = cl.user_session.get("rag_service")
    await cl.make_async(rag_service.clear_knowledge_base)()
    await cl.Message(content="✅ 知識庫已清空").send()


@cl.action_callback("cancel")
async def on_cancel(action: cl.Action):
    """處理取消操作"""
    await cl.Message(content="❌ 已取消操作").send()


@cl.on_settings_update
async def setup_agent(settings):
    """處理設置更新"""
    print("設置已更新:", settings)
