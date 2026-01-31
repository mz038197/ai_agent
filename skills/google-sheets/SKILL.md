---
name: google-sheets
description: 操作 Google Sheets 試算表的讀取和寫入功能。使用此技能來讀取單元格、寫入數據、批量處理範圍數據，或列出工作表。當用戶提到 sheets、試算表、spreadsheet、單元格、或需要操作 Google Sheets 時使用。
---

# Google Sheets 操作

## 工具位置

本 Skill 的工具函數位於 `scripts/tools.py`，包含以下函數：

- `read_cell(spreadsheet_id, cell, sheet_name)` - 讀取單元格
- `write_cell(spreadsheet_id, cell, value, sheet_name)` - 寫入單元格
- `read_range(spreadsheet_id, range_name, sheet_name)` - 讀取範圍
- `list_sheets(spreadsheet_id)` - 列出所有工作表

這些函數會自動載入為可用工具，無需手動導入。

## 快速開始

**可用工具（已自動載入）：**

| 工具 | 用途 | 範例 |
|------|------|------|
| `read_cell` | 讀取單元格 | read_cell(id, "A1") |
| `write_cell` | 寫入單元格 | write_cell(id, "A1", "Hello") |
| `read_range` | 讀取範圍 | read_range(id, "A1:B10") |
| `list_sheets` | 列出工作表 | list_sheets(id) |

## 取得 Spreadsheet ID

從 Google Sheets 網址中提取 ID：
```
https://docs.google.com/spreadsheets/d/【這裡是ID】/edit
                                      ↑
                                約 40+ 字符的長字串
```

## 操作流程

### 1. 確認 Spreadsheet ID

**沒有 ID？** → 請用戶提供 Google Sheets 網址或 ID

**有 ID？** → 繼續下一步

### 2. 選擇操作類型

| 用戶需求 | 使用工具 | 範例 |
|---------|---------|------|
| 讀取單個值 | `read_cell` | 讀取 A1 的值 |
| 寫入單個值 | `write_cell` | 在 B2 寫入 "測試" |
| 讀取多個值 | `read_range` | 讀取 A1:C10 的所有數據 |
| 查看所有工作表 | `list_sheets` | 列出所有工作表名稱 |

### 3. 執行並回報

**成功時**：
```
✅ 成功在 A1 單元格寫入 'Hello'
```

**失敗時**：
```
❌ 操作失敗：[錯誤原因]
建議：[解決方案]
```

## 單元格格式規範

使用 A1 notation（不使用 R1C1 格式）：

| 格式類型 | 正確示例 | 錯誤示例 |
|---------|---------|---------|
| 單元格 | `A1`, `B2`, `AA10` | `R1C1`, `1,1` |
| 範圍 | `A1:B10`, `C1:C100` | `A1-B10`, `A1..B10` |

## 工作表名稱

- 默認：`"工作表1"` (中文) 或 `"Sheet1"` (英文)
- 不確定名稱時，先使用 `list_sheets` 查看
- 有多個工作表時，明確指定 `sheet_name` 參數

## 常見錯誤處理

| 錯誤類型 | 可能原因 | 解決方案 |
|---------|---------|---------|
| ID 無效 | Spreadsheet ID 格式錯誤 | 檢查網址中的 ID 部分 |
| 權限不足 | 服務帳號無訪問權限 | 將試算表分享給服務帳號 |
| 工作表不存在 | 工作表名稱錯誤 | 使用 `list_sheets` 查看正確名稱 |
| 單元格格式錯誤 | 使用了非 A1 notation | 改用 A1 格式（如 "A1"） |

## 性能優化

大量數據操作時：

- ✅ **推薦**：使用 `read_range` 一次讀取範圍
- ❌ **避免**：多次調用 `read_cell` 讀取相鄰單元格

範例：
```bash
# 推薦：一次讀取 10 個單元格
read_range <id> A1:A10

# 避免：調用 10 次
read_cell <id> A1
read_cell <id> A2
...
```
