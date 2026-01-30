---
name: google-sheets
description: 操作 Google Sheets 的专业技能
keywords: [sheets, 表格, spreadsheet, excel, 试算表, 单元格]
categories: [data, productivity]
tools_file: scripts/tools.py
tools:
  - read_cell
  - write_cell
  - read_range
  - list_sheets
trigger_patterns:
  - "表格"
  - "sheets"
  - "试算表"
  - "单元格"
  - "spreadsheet"
version: 1.0
---

# Google Sheets Skill

## 描述
此 skill 提供操作 Google Sheets 的专业能力，帮助你高效、准确地完成试算表操作。

## 可用工具

### 1. read_cell
读取指定单元格的值
- **参数**：
  - `spreadsheet_id`: 试算表 ID（从网址中获取）
  - `cell`: 单元格位置（如 "A1", "B2"）
  - `sheet_name`: 工作表名称（默认 "工作表1"）
- **示例**：读取试算表的 A1 单元格

### 2. write_cell
写入值到指定单元格
- **参数**：
  - `spreadsheet_id`: 试算表 ID
  - `cell`: 单元格位置
  - `value`: 要写入的值
  - `sheet_name`: 工作表名称（默认 "工作表1"）
- **示例**：在 A1 写入 "Hello"

### 3. read_range
读取指定范围的值
- **参数**：
  - `spreadsheet_id`: 试算表 ID
  - `range_name`: 范围（如 "A1:B10"）
  - `sheet_name`: 工作表名称
- **示例**：读取 A1 到 B10 的所有数据

### 4. list_sheets
列出试算表中的所有工作表
- **参数**：
  - `spreadsheet_id`: 试算表 ID
- **示例**：列出所有工作表名称

## 最佳实践

### 1. 单元格引用格式
- ✅ 使用 A1 notation：`"A1"`, `"B2"`, `"AA10"`
- ✅ 范围使用冒号：`"A1:B10"`, `"C1:C100"`
- ❌ 避免使用 R1C1 格式

### 2. 试算表 ID 格式
- 试算表 ID 是一长串字符，从网址中获取：
  ```
  https://docs.google.com/spreadsheets/d/【这里是ID】/edit
  ```
- 示例：`1dh0chvqXjBMliJm3T7KC2JxHdwOKV4AT89xLlIJSE7o`

### 3. 工作表名称
- 默认为 "工作表1"（中文）或 "Sheet1"（英文）
- 如果用户指定了工作表名称，务必使用正确的名称

### 4. 错误处理
- 如果操作失败，工具会返回错误信息
- 常见错误：
  - 试算表 ID 无效
  - 没有权限访问
  - 工作表名称不存在
  - 单元格格式错误

## 工作流程建议

### 场景 1：写入数据
```
用户: "在 A1 写入 Hello"
步骤:
1. 确认有 spreadsheet_id
2. 使用 write_cell(spreadsheet_id, "A1", "Hello")
3. 回报写入结果
```

### 场景 2：读取数据
```
用户: "读取 A1 的数据"
步骤:
1. 确认有 spreadsheet_id
2. 使用 read_cell(spreadsheet_id, "A1")
3. 返回读取的值
```

### 场景 3：批量操作
```
用户: "读取 A1 到 B10 的所有数据"
步骤:
1. 确认有 spreadsheet_id
2. 使用 read_range(spreadsheet_id, "A1:B10")
3. 格式化并返回数据
```

## 回答格式

### 成功时
- 明确说明完成的操作
- 显示相关的数据结果
- 示例："✅ 成功在 A1 单元格写入 'Hello from MCP!'"

### 失败时
- 说明失败原因
- 提供解决建议
- 示例："❌ 写入失败：试算表 ID 无效。请检查网址中的 ID 部分。"

## 注意事项

1. **权限检查**：确保服务账号有试算表的访问权限
2. **ID 验证**：试算表 ID 应该是一长串字符（约 40+ 字符）
3. **工作表名称**：如果不确定，使用 list_sheets 先查看所有工作表
4. **数据类型**：写入的值会自动转换为字符串
5. **性能考虑**：大量数据操作时，优先使用 read_range 而不是多次 read_cell
