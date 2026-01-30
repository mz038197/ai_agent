# AI Agent with MCP (Model Context Protocol)

基于 LangChain + Ollama + MCP 的 AI Agent 示例项目。

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

### 2. 使用 Google Sheets（推荐）

如果你想操作 Google Sheets：

1. **准备 Google 凭证：**
   - 前往 [Google Cloud Console](https://console.cloud.google.com/)
   - 创建服务账号并下载 `credentials.json`
   - 启用 Google Sheets API 和 Google Drive API
   - 将 `credentials.json` 放到项目根目录
   - 在 Google Sheets 中，将试算表分享给服务账号的邮箱

2. **安装依赖：**
   ```bash
   pip install gspread google-auth
   ```

3. **运行 Google Sheets 程序：**
   ```bash
   python sheets_main.py
   ```
   
   注意：记得修改 `sheets_main.py` 中的 `spreadsheet_id`！

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

## 项目结构

```
ai_agent/
├── test_main.py         # 本地测试示例（推荐先运行）
├── test_server.py       # 简单的 MCP 测试服务器
├── sheets_main.py       # Google Sheets 示例（推荐）
├── sheets_server.py     # 自定义 Google Sheets MCP 服务器
├── main.py              # 使用官方 gdrive server（已 deprecated）
├── requirements.txt     # Python 依赖
├── credentials.json     # Google 凭证（需自行创建）
└── README.md            # 项目文档
```

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
