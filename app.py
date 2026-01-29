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
    RAGService,
    AgentService
)


# 配置參數
CONFIG = {
    "MODEL": "gemma3:4b",
    "AGENT_MODEL": "qwen2.5:7b",  # Agent 專用模型（需支持工具調用）
    "BASE_URL": "http://localhost:11434",
    "TEMPERATURE": 0.7,
    "AGENT_TEMPERATURE": 0,  # Agent 建議用較低溫度
    "EMBEDDING_MODEL": "nomic-embed-text",
    "CHROMA_DB_PATH": "./chroma_db",
    "ENABLE_WEB_SEARCH": True,  # 是否啟用網路搜尋
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
    
    # 初始化 Agent 服務（新增）
    try:
        agent_service = AgentService(
            vector_store_service=vector_service,
            model=CONFIG["AGENT_MODEL"],
            base_url=CONFIG["BASE_URL"],
            temperature=CONFIG["AGENT_TEMPERATURE"],
            enable_web_search=CONFIG["ENABLE_WEB_SEARCH"],
            verbose=False  # 在生產環境設為 False
        )
        cl.user_session.set("agent_service", agent_service)
        agent_available = True
    except Exception as e:
        print(f"⚠️ Agent 服務初始化失敗: {e}")
        agent_available = False
    
    # 將服務存儲在用戶會話中
    cl.user_session.set("llm_service", llm_service)
    cl.user_session.set("rag_service", rag_service)
    cl.user_session.set("agent_available", agent_available)
    
    # 設置默認模式為 auto（自動判斷）
    cl.user_session.set("mode", "auto")
    
    # 獲取模型和知識庫信息
    model_info = llm_service.get_model_info()
    kb_stats = rag_service.get_knowledge_base_stats()
    
    # 歡迎訊息
    agent_status = "✅ 已啟用" if agent_available else "❌ 未啟用"
    agent_info = ""
    if agent_available:
        agent_service = cl.user_session.get("agent_service")
        tools = agent_service.list_tools()
        tool_names = ", ".join([t["name"] for t in tools])
        agent_info = f"\n🛠️ **可用工具:** {tool_names}\n"
    
    await cl.Message(
        content=f"👋 歡迎使用 AI 助手！\n\n"
                f"📦 **當前模型:** {model_info['model']}\n"
                f"📚 **知識庫:** {kb_stats['total_chunks']} 個文檔塊\n"
                f"🤖 **當前模式:** 自動模式 (auto)\n"
                f"🤖 **Agent 模式:** {agent_status}{agent_info}\n"
                f"💬 **您可以：**\n"
                f"- 💭 輸入文字進行對話\n"
                f"- 📄 上傳文件（PDF/TXT/Markdown）建立知識庫\n"
                f"- 🖼️ 上傳圖片進行視覺分析\n\n"
                f"⚙️ **模式切換：**\n"
                f"- `/auto` - 自動判斷是否使用知識庫（預設）\n"
                f"- `/chat` - 純聊天模式（不使用知識庫）\n"
                f"- `/rag` - 知識庫模式（強制檢索文檔）\n"
                + (f"- `/agent` - Agent 模式（LLM 自主調用工具）\n" if agent_available else "")
                + f"\n📋 **其他命令：**\n"
                f"- `/stats` - 查看知識庫統計\n"
                f"- `/clear` - 清空知識庫",
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
        
        # 模式切換命令
        if content_lower == "/chat":
            cl.user_session.set("mode", "chat")
            await cl.Message(
                content="💬 **已切換到聊天模式**\n\n"
                        "- 不會檢索知識庫\n"
                        "- 純粹與 AI 對話\n"
                        "- 適合閒聊、常識問題"
            ).send()
            return
        
        if content_lower == "/rag":
            cl.user_session.set("mode", "rag")
            await cl.Message(
                content="📚 **已切換到知識庫模式**\n\n"
                        "- 強制檢索知識庫\n"
                        "- 基於文檔內容回答\n"
                        "- 適合查詢已上傳的文檔"
            ).send()
            return
        
        if content_lower == "/auto":
            cl.user_session.set("mode", "auto")
            await cl.Message(
                content="🤖 **已切換到自動模式**\n\n"
                        "- 智能判斷是否需要知識庫\n"
                        "- 根據問題相關性自動選擇\n"
                        "- 適合混合使用場景（預設）"
            ).send()
            return
        
        if content_lower == "/agent":
            agent_available = cl.user_session.get("agent_available", False)
            if not agent_available:
                await cl.Message(
                    content="❌ **Agent 模式不可用**\n\n"
                            "可能原因：\n"
                            "- Agent 模型未下載（需要 qwen2.5:7b 或其他支持工具調用的模型）\n"
                            "- 網路搜尋工具初始化失敗\n\n"
                            "請確保已下載支持工具調用的模型：\n"
                            "`ollama pull qwen2.5:7b`"
                ).send()
                return
            
            cl.user_session.set("mode", "agent")
            agent_service = cl.user_session.get("agent_service")
            tools = agent_service.list_tools()
            tools_info = "\n".join([f"  • **{t['name']}**: {t['description']}" for t in tools])
            
            await cl.Message(
                content=f"🤖 **已切換到 Agent 模式**\n\n"
                        f"- LLM 自主決定何時使用工具\n"
                        f"- 支援知識庫檢索 + 網路搜尋\n"
                        f"- 適合複雜查詢和多步推理\n\n"
                        f"**可用工具：**\n{tools_info}"
            ).send()
            return
        
        # 統計命令
        if content_lower == "/stats":
            current_mode = cl.user_session.get("mode", "auto")
            mode_emoji = {"chat": "💬", "rag": "📚", "auto": "🤖", "agent": "🤖"}
            mode_name = {"chat": "聊天模式", "rag": "知識庫模式", "auto": "自動模式", "agent": "Agent 模式"}
            
            stats = rag_service.get_knowledge_base_stats()
            
            stats_content = (
                f"📊 **系統狀態**\n\n"
                f"🤖 **當前模式:** {mode_emoji.get(current_mode, '🤖')} {mode_name.get(current_mode, '自動模式')}\n\n"
                f"📚 **知識庫統計：**\n"
                f"- 文檔塊總數：{stats['total_chunks']}\n"
                f"- 集合名稱：{stats['collection_name']}\n"
                f"- 嵌入模型：{stats['embedding_model']}\n"
                f"- 支援格式：{', '.join(stats['supported_formats'])}"
            )
            
            # 如果是 Agent 模式，顯示 Agent 信息
            if current_mode == "agent":
                agent_service = cl.user_session.get("agent_service")
                if agent_service:
                    agent_info = agent_service.get_agent_info()
                    stats_content += (
                        f"\n\n🤖 **Agent 配置：**\n"
                        f"- 模型：{agent_info['model']}\n"
                        f"- 溫度：{agent_info['temperature']}\n"
                        f"- 工具：{', '.join(agent_info['tools'])}"
                    )
            
            await cl.Message(content=stats_content).send()
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
        
        # 處理純文字（根據模式選擇處理方式）
        else:
            await _handle_text_with_rag(message, rag_service, llm_service)
            
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


async def _handle_text_with_rag(
    message: cl.Message, 
    rag_service: RAGService,
    llm_service: LLMService
):
    """根據當前模式處理純文字訊息"""
    msg = cl.Message(content="")
    await msg.send()
    
    # 獲取當前模式
    mode = cl.user_session.get("mode", "auto")
    
    # 根據模式選擇處理方式
    if mode == "chat":
        # 純聊天模式 - 不檢索知識庫
        response = await cl.make_async(llm_service.send_message)(message.content)
    
    elif mode == "rag":
        # 知識庫模式 - 強制使用 RAG
        response = await cl.make_async(rag_service.query_with_context)(
            message.content,
            k=4,
            use_mmr=False,
            include_sources=True
        )
    
    elif mode == "agent":
        # Agent 模式 - LLM 自主調用工具
        agent_service = cl.user_session.get("agent_service")
        if agent_service:
            msg.content = "🤖 Agent 正在思考並決定使用哪些工具..."
            await msg.update()
            
            result = await cl.make_async(agent_service.query)(message.content)
            
            if result["success"]:
                response = result["answer"]
                
                # 顯示使用的工具（可選）
                if result.get("intermediate_steps"):
                    steps_info = "\n\n---\n*使用的工具: "
                    tools_used = set()
                    for step in result["intermediate_steps"]:
                        if hasattr(step[0], 'tool'):
                            tools_used.add(step[0].tool)
                    if tools_used:
                        response += steps_info + ", ".join(tools_used) + "*"
            else:
                response = result["answer"]
        else:
            response = "❌ Agent 服務不可用"
    
    else:  # auto 模式
        # 自動判斷模式 - 使用智能查詢
        response = await cl.make_async(rag_service.query_with_auto_mode)(
            message.content,
            k=4,
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
