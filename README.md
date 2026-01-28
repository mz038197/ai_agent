# AI Agent with Chainlit UI

基於 Ollama、LangChain 和 Chainlit 構建的 AI 對話助手，支援文字對話和圖片分析。

## 功能特色

- 💬 **智能對話**: 使用 Gemma 3 模型進行自然語言對話
- 🖼️ **圖片理解**: 支援上傳圖片並進行分析
- 🎨 **現代化 UI**: 類似 ChatGPT 的使用體驗
- 🚀 **本地運行**: 完全在本地運行，保護隱私

## 安裝步驟

### 1. 安裝 Ollama

前往 [Ollama 官網](https://ollama.ai/) 下載並安裝 Ollama。

### 2. 下載模型

```bash
ollama pull gemma3:4b
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
- 輸入文字進行對話
- 點擊輸入框旁的 📎 按鈕上傳圖片
- 支援拖放圖片到聊天區域

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
├── app.py                    # Chainlit UI 應用（UI 層）
├── services/                 # 業務邏輯層
│   ├── __init__.py          
│   ├── llm_service.py       # LLM 服務
│   └── image_service.py     # 圖片處理服務
├── main.py                  # 命令列版本
├── requirements.txt         # Python 依賴
├── chainlit.md              # Chainlit 歡迎頁面
├── .chainlit/               # Chainlit 配置目錄
│   └── config.toml
├── ARCHITECTURE.md          # 架構設計文檔
└── README.md                # 說明文件
```

### 架構特點

本專案遵守 **SOLID 原則**，採用分層架構：

- **UI 層** (`app.py`): 負責用戶界面交互
- **服務層** (`services/`): 封裝業務邏輯
  - `LLMService`: 處理模型調用
  - `ImageService`: 處理圖片編碼

詳細架構說明請參考 [ARCHITECTURE.md](ARCHITECTURE.md)

## 技術棧

- **LLM**: Ollama (Gemma 3)
- **框架**: LangChain
- **UI**: Chainlit
- **語言**: Python 3.8+

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
