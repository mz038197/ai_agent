# RAG 功能使用指南

## 📋 功能概述

您的 AI 助手現在支援 **RAG（檢索增強生成）** 功能，可以：

1. ✅ 上傳並處理 PDF、TXT、Markdown 文檔
2. ✅ 自動將文檔向量化存儲到 Chroma DB
3. ✅ 基於知識庫回答問題（長期記憶）
4. ✅ 同時保留對話歷史（短期記憶）

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 下載嵌入模型

RAG 功能需要嵌入模型來向量化文檔：

```bash
# 下載 Ollama 的嵌入模型（推薦）
ollama pull nomic-embed-text
```

### 3. 啟動應用

```bash
chainlit run app.py
```

## 💡 使用方式

### 📄 上傳文檔建立知識庫

1. 點擊輸入框旁的 **📎 附件按鈕**
2. 選擇文件（支援 `.pdf`、`.txt`、`.md`、`.markdown`）
3. 可選：輸入問題，AI 會在處理完文檔後立即回答
4. 等待處理完成

**支援的文件格式：**
- PDF 文件 (`.pdf`)
- 純文字文件 (`.txt`)
- Markdown 文件 (`.md`, `.markdown`)

### 💬 提問（自動使用知識庫）

直接輸入問題，AI 會：
1. 自動從知識庫檢索相關內容
2. 基於檢索到的內容回答
3. 在回答末尾附上資料來源

**範例：**
```
用戶：這份文件的主要內容是什麼？
AI：[基於知識庫的回答]

📚 資料來源：
  - document.pdf
```

### 🖼️ 圖片分析（不使用知識庫）

上傳圖片時，會使用視覺模型直接分析，不會查詢知識庫。

### 📊 查看知識庫統計

輸入命令：
```
/stats
```

會顯示：
- 文檔塊總數
- 集合名稱
- 嵌入模型
- 支援的文件格式

### 🗑️ 清空知識庫

輸入命令：
```
/clear
```

系統會要求確認，確認後會清空所有文檔。

## ⚙️ 配置說明

在 `app.py` 中可以調整配置：

```python
CONFIG = {
    "MODEL": "gemma3:4b",              # LLM 模型
    "BASE_URL": "http://localhost:11434",
    "TEMPERATURE": 0.7,
    "EMBEDDING_MODEL": "nomic-embed-text",  # 嵌入模型
    "CHROMA_DB_PATH": "./chroma_db"         # 數據庫路徑
}
```

### 調整文檔分割參數

在 `services/document_service.py` 中：

```python
doc_service = DocumentService(
    chunk_size=1000,      # 每個塊的大小
    chunk_overlap=200     # 塊之間的重疊
)
```

### 調整檢索數量

在查詢時指定 `k` 參數：

```python
rag_service.query_with_context(
    query="問題",
    k=4  # 檢索 4 個最相關的文檔塊（預設值）
)
```

## 🏗️ 架構說明

```
services/
├── llm_service.py          # LLM 對話服務（含短期記憶）
├── document_service.py     # 文檔加載與分割
├── vector_store_service.py # Chroma DB 向量存儲
└── rag_service.py          # RAG 整合服務（長期記憶）

chroma_db/                  # 向量數據庫（自動創建）
```

### 數據流程

```
文檔上傳 → 加載 → 分割 → 向量化 → 存儲到 Chroma DB
                                           ↓
用戶提問 → 向量化問題 → 檢索相似文檔 → 構建提示詞 → LLM 生成回答
```

## 🔍 進階功能

### 使用 MMR 檢索（避免重複）

```python
rag_service.query_with_context(
    query="問題",
    use_mmr=True  # 使用最大邊際相關性
)
```

### 帶分數檢索（過濾不相關結果）

```python
rag_service.query_with_score(
    query="問題",
    score_threshold=1.5  # 只保留分數 ≤ 1.5 的結果
)
```

### 元數據過濾

```python
vector_service.search_by_metadata(
    query="問題",
    metadata_filter={"source": "specific.pdf"}
)
```

## 🐛 常見問題

### 1. 找不到嵌入模型

**錯誤：** `Model not found: nomic-embed-text`

**解決：**
```bash
ollama pull nomic-embed-text
```

### 2. 文檔處理失敗

**可能原因：**
- PDF 文件損壞或加密
- 文件編碼問題（TXT）
- 缺少依賴包

**解決：**
```bash
pip install pypdf unstructured
```

### 3. 查詢沒有使用知識庫

**檢查：**
1. 確認文檔已成功上傳（使用 `/stats` 查看）
2. 確認問題與文檔內容相關
3. 嘗試增加檢索數量 `k`

### 4. 記憶體不足

**原因：** 文檔過多或過大

**解決：**
- 減少 `chunk_size`
- 定期清理不需要的文檔
- 使用元數據過濾只查詢特定文檔

## 📚 最佳實踐

### 文檔準備

1. **清理文檔：** 移除無關內容（頁首頁尾、目錄等）
2. **結構化：** 使用標題、段落分隔
3. **合理大小：** 單個文檔建議 < 10MB

### 提問技巧

1. **具體明確：** "第三章講了什麼？" 比 "講了什麼？" 更好
2. **相關性：** 確保問題與上傳的文檔相關
3. **多角度：** 如果第一次回答不理想，換個方式問

### 性能優化

1. **合適的 chunk_size：** 
   - 技術文檔：500-800 字符
   - 長篇文章：1000-1500 字符
   
2. **合適的 k 值：**
   - 簡單問題：k=2-3
   - 複雜問題：k=4-6
   
3. **定期清理：** 移除過時或不再需要的文檔

## 🎯 使用場景

### 1. 技術文檔助手
上傳產品手冊、API 文檔，快速查找解決方案

### 2. 學習助手
上傳課程講義、教材，輔助學習和複習

### 3. 研究助理
上傳論文、研究報告，快速提取關鍵信息

### 4. 企業知識庫
建立內部文檔庫，提高團隊效率

## 📈 後續改進方向

- [ ] 支援更多文件格式（Word、Excel）
- [ ] 多知識庫管理（按主題分類）
- [ ] 文檔版本控制
- [ ] 引用追溯（精確到段落）
- [ ] 批量文檔上傳
- [ ] 知識圖譜可視化

---

有任何問題或建議，歡迎反饋！🎉
