# 架構設計文檔

## 概述

本專案遵守 SOLID 原則進行重構，將 UI 層與業務邏輯層分離，提高代碼的可維護性和可擴展性。

## 目錄結構

```
ai_agent/
├── app.py                      # Chainlit UI 層
├── services/                   # 業務邏輯層
│   ├── __init__.py            
│   ├── llm_service.py         # LLM 服務
│   └── image_service.py       # 圖片處理服務
├── main.py                    # 命令列版本（保留）
├── requirements.txt           
└── README.md                  
```

## SOLID 原則應用

### 1. 單一職責原則 (Single Responsibility Principle - SRP)

每個類/模組只有一個改變的理由：

- **`app.py`**: 只負責 UI 交互（Chainlit 事件處理、消息顯示）
- **`LLMService`**: 只負責與 LLM 模型交互
- **`ImageService`**: 只負責圖片處理邏輯

### 2. 開放封閉原則 (Open/Closed Principle - OCP)

對擴展開放，對修改封閉：

- 新增其他 LLM 提供者（如 OpenAI）時，只需實現新的服務類
- 不需要修改現有的 UI 代碼

### 3. 里氏替換原則 (Liskov Substitution Principle - LSP)

服務層可以被替換而不影響 UI 層：

- 可以輕鬆切換不同的 LLM 實現
- UI 層不需要知道具體實現細節

### 4. 接口隔離原則 (Interface Segregation Principle - ISP)

客戶端不應該依賴它不使用的接口：

- `LLMService` 提供清晰的方法接口
- UI 層只調用需要的方法

### 5. 依賴反轉原則 (Dependency Inversion Principle - DIP)

高層模組不應該依賴低層模組，兩者都應該依賴抽象：

- UI 層依賴服務層的抽象接口
- 服務層可以獨立測試和替換

## 架構層次

```
┌─────────────────────────────────────┐
│         UI 層 (app.py)              │
│  - Chainlit 事件處理                │
│  - 用戶輸入接收                     │
│  - 回應顯示                         │
└─────────────┬───────────────────────┘
              │ 依賴
              ↓
┌─────────────────────────────────────┐
│      服務層 (services/)             │
│  - LLMService: 模型調用             │
│  - ImageService: 圖片處理           │
│  - 業務邏輯封裝                     │
└─────────────┬───────────────────────┘
              │ 依賴
              ↓
┌─────────────────────────────────────┐
│      基礎設施層                     │
│  - LangChain                        │
│  - Ollama                           │
│  - Python 標準庫                    │
└─────────────────────────────────────┘
```

## 核心組件

### 1. UI 層 (`app.py`)

**職責：**
- 處理 Chainlit 事件 (`@cl.on_chat_start`, `@cl.on_message`)
- 接收用戶輸入（文字/圖片）
- 顯示處理狀態和結果
- 管理用戶會話

**特點：**
- 不包含業務邏輯
- 所有 LLM 調用都委托給服務層
- 專注於用戶體驗

### 2. LLM 服務 (`services/llm_service.py`)

**職責：**
- 初始化和配置 LLM 模型
- 處理文字輸入
- 處理多模態輸入（文字+圖片）
- 提供模型信息

**核心方法：**
```python
- __init__(model, base_url, temperature)  # 初始化
- process_text(text)                      # 處理純文字
- process_image_with_text(text, image)    # 處理圖片+文字
- get_model_info()                        # 獲取模型信息
```

### 3. 圖片服務 (`services/image_service.py`)

**職責：**
- 圖片編碼（base64）
- 創建 data URL
- 圖片格式處理

**核心方法：**
```python
- encode_to_base64(image_path)           # Base64 編碼
- create_image_data_url(image_path)      # 創建 data URL
```

## 優勢

### ✅ 可維護性
- 職責清晰，修改某一層不影響其他層
- 代碼更易讀和理解

### ✅ 可測試性
- 服務層可以獨立單元測試
- UI 層可以 mock 服務層進行測試

### ✅ 可擴展性
- 新增功能時只需擴展服務層
- 切換 UI 框架不影響業務邏輯
- 切換 LLM 提供者只需修改服務層

### ✅ 可重用性
- 服務層可以被其他 UI（如 Web API、CLI）重用
- 業務邏輯不綁定於特定 UI 框架

## 使用範例

### 啟動應用

```bash
chainlit run app.py -w
```

### 擴展新功能

**例：添加流式輸出**

1. 在 `LLMService` 添加方法：
```python
def process_text_stream(self, text: str):
    """流式處理文字"""
    return self.chat.stream([self.create_text_message(text)])
```

2. 在 UI 層使用：
```python
async def _handle_text_message_stream(message, llm_service):
    msg = cl.Message(content="")
    await msg.send()
    
    stream = llm_service.process_text_stream(message.content)
    for chunk in stream:
        msg.content += chunk.content
        await msg.update()
```

### 切換 LLM 提供者

創建新的服務類：

```python
class OpenAIService:
    def __init__(self, api_key, model):
        # OpenAI 初始化
        pass
    
    def process_text(self, text):
        # OpenAI API 調用
        pass
```

在 `app.py` 中切換：
```python
llm_service = OpenAIService(api_key="...", model="gpt-4")
```

## 最佳實踐

1. **保持 UI 層輕量**：只處理顯示邏輯
2. **服務層無狀態**：盡量設計為純函數
3. **依賴注入**：通過構造函數傳入依賴
4. **錯誤處理**：在適當的層次處理錯誤
5. **文檔化**：為公開方法添加清晰的文檔字符串

## 未來改進方向

- [ ] 添加抽象基類 (ABC) 定義服務接口
- [ ] 實現依賴注入容器
- [ ] 添加日誌系統
- [ ] 實現配置管理類
- [ ] 添加單元測試
- [ ] 添加對話歷史管理服務
- [ ] 實現插件系統
