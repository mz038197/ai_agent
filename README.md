# AI Agent with MCP (Model Context Protocol)

基于 LangChain + Ollama + MCP 的 AI Agent 示例项目。

## ✨ 新功能：Skill 支持（符合 Anthropic 官方標準）

本專案支援類似 Anthropic Claude 的 Skill 系統，現已重構為完全符合官方標準！

**特點：**
- 📁 自動發現和加載 skills
- 📖 將 skill 內容注入到 system prompt
- 🔧 **直接從 skill 加載 Python 工具函數**
- 🚫 **不需要啟動 MCP Server**
- 🎯 工具代碼和指導文檔在一起
- ⚡ 更簡單、更直接、更易維護
- ✅ **完全符合 Anthropic 官方 Skills 標準**

## 安装依赖

```bash
pip install -r requirements.txt
```

确保你已经安装：
- Python 3.9+
- Ollama（并下载模型：`ollama pull llama3.1`）

## 快速测试

### 1. 测试本地 MCP Server

首先测试基础的 MCP 连接和工具调用：

```bash
python test_main.py
```

这会：
- 启动一个本地的测试 MCP server（test_server.py）
- 载入数学计算和问候工具
- 测试 agent 能否正确调用这些工具

### 2. 使用 Google Sheets（推荐 - 直接加载工具）

**新方式：直接从 Skill 加载工具，不需要 MCP Server！**

1. **准备 Google 凭证：**
   - 前往 [Google Cloud Console](https://console.cloud.google.com/)
   - 创建服务账号并下载 `credentials.json`
   - 启用 Google Sheets API 和 Google Drive API
   - 将 `credentials.json` 放到项目根目录
   - 在 Google Sheets 中，将试算表分享给服务账号的邮箱

2. **安装依赖：**
   ```bash
   pip install gspread google-auth pyyaml
   ```

3. **运行直接加载版本（推荐）：**
   ```bash
   python sheets_direct.py
   ```
   
   **优势：**
   - ✅ 不需要启动 MCP Server
   - ✅ 工具定义在 `skills/google-sheets/tools.py`
   - ✅ 更简单、更直接
   - ✅ 易于调试和修改

4. **或运行 MCP Server 版本：**
   ```bash
   python sheets_main.py
   ```
   
   注意：记得修改代码中的 `spreadsheet_id`！

### 3. 使用官方 Google Drive MCP Server（备选）

如果你想使用 npm 包：

1. **安装 Node.js 和 npx：**
   ```bash
   node --version  # 确认已安装
   ```

2. **运行主程序：**
   ```bash
   python main.py
   ```
   
   注意：官方的 `@modelcontextprotocol/server-gdrive` 已被标记为 deprecated

## 📂 项目结构

```
ai_agent/
├── skills/                      # Skills 目录（新增）
│   └── google-sheets/
│       ├── SKILL.md            # Skill 指南（包含 YAML metadata）
│       ├── tools.py            # 工具函数实现（新增）
│       └── __init__.py         # 包初始化
├── utils/                       # 工具模块（新增）
│   ├── __init__.py
│   └── skill_loader.py         # Skill 加载工具（支持加载工具函数）
├── test_main.py                 # 本地测试示例（推荐先运行）
├── test_server.py               # 简单的 MCP 测试服务器
├── test_skills.py               # Skills 系统测试
├── test_skill_tools.py          # 工具加载功能测试（新增）
├── sheets_direct.py             # 直接加载工具版本（推荐，新增）
├── sheets_main.py               # MCP Server 版本（支持 skill）
├── sheets_main_v2.py            # MCP Server 版本 v2（使用 utils）
├── sheets_server.py             # 自定义 Google Sheets MCP 服务器
├── main.py                      # 使用官方 gdrive server（已 deprecated）
├── requirements.txt             # Python 依赖
├── credentials.json             # Google 凭证（需自行创建）
└── README.md                    # 项目文档
```

## 🎯 使用 Skills

### 什么是 Skill？

Skill 是存储在 `./skills/` 目录下的 SKILL.md 文件，用于：
- 📖 提供工具使用指南
- ✅ 定义最佳实践
- 📝 规范回答格式
- 🎓 教导 Agent 专业知识

### 創建新的 Skill（符合官方標準）

1. 在 `skills/` 目錄下創建新資料夾：
   ```bash
   mkdir skills/my-skill
   ```

2. 創建 `scripts/tools.py` 文件（工具函數實現）：
   ```python
   def my_tool(param1: str, param2: int) -> str:
       """
       工具的描述
       
       Args:
           param1: 參數1說明
           param2: 參數2說明
       
       Returns:
           結果說明
       """
       # 實現代碼
       return f"處理結果: {param1}, {param2}"
   
   # 導出工具列表（推薦）
   __all__ = ['my_tool']
   ```

3. 創建 `SKILL.md` 文件（符合 Anthropic 官方標準）：
   ```markdown
   ---
   name: my-skill
   description: 這個 skill 的簡短描述，說明何時使用它
   ---
   
   # My Skill
   
   ## 工具位置
   
   本 Skill 的工具函數位於 `scripts/tools.py`，包含：
   - `my_tool(param1, param2)` - 工具的說明
   
   ## 使用指南
   
   1. 第一步：...
   2. 第二步：...
   
   ## 最佳實踐
   
   - ✅ 推薦做法
   - ❌ 避免做法
   ```

**重要說明：**
- ✅ YAML frontmatter 只需要 `name` 和 `description`
- ✅ 工具文件按約定放在 `scripts/tools.py`（自動發現）
- ✅ 使用 `__all__` 列表導出工具（自動載入）
- ✅ 無需在 YAML 中定義 `tools_file` 或 `tools`

### 在代码中使用 Skill

**方法 1: 直接加载工具（推荐）**
```python
from utils import SkillLoader
from langchain.agents import create_agent

loader = SkillLoader()

# 1. 加载工具函数
tools = loader.load_tools("google-sheets")

# 2. 加载指导内容
skill_content = loader.load("google-sheets")

# 3. 创建 agent
system_prompt = f"你是助手。\n\n{skill_content}"
agent = create_agent(llm, tools, system_prompt=system_prompt)

# 不需要 MCP Server！
```

**方法 2: 加载多个 Skills 的工具**
```python
from utils import SkillLoader

loader = SkillLoader()

# 加载所有 skills 的工具
all_tools = loader.load_all_tools()

# 或指定特定 skills
tools = loader.load_all_tools(["google-sheets", "web-search"])
```

**方法 3: 獲取 Skill 元信息**
```python
from utils import SkillLoader

loader = SkillLoader()

# 獲取 metadata（如果有 YAML frontmatter）
metadata = loader.get_metadata("google-sheets")
# {'name': 'google-sheets', 'description': '...'}

# 發現所有 skills
skills = loader.discover()

# 獲取 skill 信息
info = loader.get_info("google-sheets")
```

## 📚 重構文檔

專案已重構為完全符合 Anthropic 官方標準，詳見：
- `REFACTORING_TO_OFFICIAL_STANDARD.md` - 重構詳細說明
- `DYNAMIC_SKILLS_ARCHITECTURE.md` - 動態 Skills 架構設計

**主要改進：**
- ✅ 符合官方 Skills 標準
- ✅ 約定優於配置（自動發現工具文件）
- ✅ 向後兼容（仍支援自定義擴展）
- ✅ 更簡潔的 YAML frontmatter

## 工作原理

1. **MCP Server**：提供工具（函数）供 AI 调用
2. **MultiServerMCPClient**：连接一个或多个 MCP server
3. **LangChain Agent**：使用 Ollama 模型理解用户意图并调用工具
4. **执行流程**：用户提问 → Agent 分析 → 调用工具 → 返回结果

## 故障排查

### 错误：`Connection closed`
- 检查 MCP server 是否正常启动
- 对于 Google Workspace，确认 `credentials.json` 存在
- 先运行 `test_main.py` 测试基础功能

### 错误：`Cannot import name 'AgentExecutor'`
- 确保已安装最新版本：`pip install -U langchain langchain-mcp-adapters`

### Ollama 连接失败
- 确认 Ollama 正在运行：`ollama serve`
- 确认模型已下载：`ollama pull llama3.1`

## 参考资源

- [LangChain MCP 文档](https://docs.langchain.com/oss/python/langchain/mcp)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [FastMCP 库](https://github.com/jlowin/fastmcp)
