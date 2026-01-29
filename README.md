# AI Agent with Chainlit UI

基於 Ollama、LangChain 和 Chainlit 構建的 AI 對話助手，支援文字對話和圖片分析。

## 功能特色

- 💬 **智能對話**: 使用 Gemma 3 模型進行自然語言對話
- 🖼️ **圖片理解**: 支援上傳圖片並進行分析
- 📚 **RAG 知識庫**: 上傳文檔（PDF/TXT/Markdown）建立私有知識庫
- 🤖 **Agent 模式**: LLM 自主調用工具（知識庫檢索 + 網路搜尋）
- 🎨 **現代化 UI**: 類似 ChatGPT 的使用體驗
- 🚀 **本地運行**: 完全在本地運行，保護隱私

## 安裝步驟

### 1. 安裝 Ollama

前往 [Ollama 官網](https://ollama.ai/) 下載並安裝 Ollama。

### 2. 下載模型

基礎對話模型：
```bash
ollama pull gemma3:4b
```

如果要使用 **Agent 模式**，需要額外下載支持工具調用的模型：
```bash
ollama pull qwen2.5:7b        # 推薦，中文支持好
# 或
ollama pull llama3.1:8b       # 也不錯
```

嵌入模型（用於 RAG）：
```bash
ollama pull nomic-embed-text
```

### 3. 啟動 Ollama 服務

```bash
ollama serve
```

### 4. 安裝 Python 依賴

```bash
pip install -r requirements.txt
```

## 使用方法

### 方式一：使用 Chainlit UI（推薦）

啟動 Web UI：

```bash
chainlit run app.py -w
```

然後在瀏覽器中打開 `http://localhost:8000`

**功能說明：**
- 💭 輸入文字進行對話
- 📎 點擊輸入框旁的按鈕上傳圖片或文檔
- 🖼️ 支援拖放圖片到聊天區域
- 📄 支援上傳 PDF、TXT、Markdown 文件建立知識庫

**模式切換：**
- `/chat` - 純聊天模式（不使用知識庫）
- `/rag` - 知識庫模式（強制檢索文檔）
- `/auto` - 自動模式（智能判斷，預設）
- `/agent` - Agent 模式（LLM 自主調用工具）⭐ NEW

**其他命令：**
- `/stats` - 查看系統狀態
- `/clear` - 清空知識庫

### 方式二：使用命令列（舊版）

```bash
python main.py
```

**使用說明：**
- 輸入文字進行對話
- 輸入 `image:圖片路徑 問題` 來分析圖片
  - 例如: `image:photo.jpg 這張圖片裡有什麼？`

## 專案結構

```
ai_agent/
├── app.py                        # Chainlit UI 應用（UI 層）
├── services/                     # 業務邏輯層
│   ├── __init__.py          
│   ├── llm_service.py           # LLM 服務
│   ├── image_service.py         # 圖片處理服務
│   ├── document_service.py      # 文檔處理服務
│   ├── vector_store_service.py  # 向量存儲服務（Chroma）
│   ├── rag_service.py           # RAG 服務
│   └── agent_service.py         # Agent 服務 ⭐ NEW
├── chroma_db/                   # 向量數據庫存儲目錄
├── test_agent.py                # Agent 測試腳本
├── main.py                      # 命令列版本
├── requirements.txt             # Python 依賴
├── chainlit.md                  # Chainlit 歡迎頁面
├── .chainlit/                   # Chainlit 配置目錄
│   └── config.toml
├── ARCHITECTURE.md              # 架構設計文檔
├── AGENT_GUIDE.md               # Agent 使用指南 ⭐ NEW
├── RAG_SETUP.md                 # RAG 設置指南
└── README.md                    # 說明文件
```

### 架構特點

本專案遵守 **SOLID 原則**，採用分層架構：

- **UI 層** (`app.py`): 負責用戶界面交互
- **服務層** (`services/`): 封裝業務邏輯
  - `LLMService`: 處理模型調用
  - `ImageService`: 處理圖片編碼
  - `DocumentService`: 處理文檔加載和分割
  - `VectorStoreService`: 處理向量存儲（Chroma）
  - `RAGService`: 處理檢索增強生成
  - `AgentService`: 處理 Agent 工具調用 ⭐ NEW

詳細說明：
- 架構設計：[ARCHITECTURE.md](ARCHITECTURE.md)
- Agent 使用：[AGENT_GUIDE.md](AGENT_GUIDE.md) ⭐
- RAG 設置：[RAG_SETUP.md](RAG_SETUP.md)

## 技術棧

- **LLM**: Ollama (Gemma 3 / Qwen 2.5 / Llama 3.1)
- **框架**: LangChain
- **UI**: Chainlit
- **向量數據庫**: ChromaDB
- **嵌入模型**: nomic-embed-text
- **搜尋工具**: DuckDuckGo
- **語言**: Python 3.8+

## Agent 模式 🆕

Agent 模式是本項目的亮點功能，讓 LLM 能夠自主決定何時使用工具：

### 可用工具
1. **知識庫檢索** - 檢索已上傳的文檔
2. **網路搜尋** - DuckDuckGo 搜尋最新信息

### 使用方法
1. 確保已下載支持工具調用的模型：
   ```bash
   ollama pull qwen2.5:7b
   ```

2. 啟動應用並切換到 Agent 模式：
   ```
   /agent
   ```

3. 測試 Agent 功能：
   ```bash
   python test_agent.py
   ```

### 示例查詢
```
RAG 在 LangChain 的做法是什麼？最新的版本有什麼更新？
```

Agent 會自動：
1. 使用知識庫檢索查找 RAG 資料
2. 使用網路搜尋查找最新更新
3. 綜合兩個來源生成回答

詳細說明請參考 [AGENT_GUIDE.md](AGENT_GUIDE.md)

## 常見問題

### 1. 無法連接到 Ollama

確保 Ollama 服務正在運行：
```bash
ollama serve
```

### 2. 圖片分析失敗

確認模型支援多模態功能。如果 `gemma3:4b` 不支援，可以使用：
```bash
ollama pull llava
```
然後在 `app.py` 中將 `MODEL` 改為 `"llava"`。

### 3. 依賴安裝失敗

嘗試升級 pip：
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 授權

MIT License
