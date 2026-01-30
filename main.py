import asyncio
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

async def main():
    # 1. 初始化 Ollama (確保你已經 ollama pull llama3.1 或 qwen2.5)
    llm = ChatOllama(model="qwen3:8b", temperature=0.7)

    # 2. 建立 MCP Client，定義 Server 的啟動參數
    # 使用官方的 Google Drive MCP server
    client = MultiServerMCPClient({
        "google_drive": {
            "transport": "stdio",  # 使用 stdio 傳輸
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-gdrive"],
            "env": {
                "GOOGLE_APPLICATION_CREDENTIALS": "./credentials.json"  # 你的憑證路徑
            }
        }
    })

    # 3. 載入 MCP 工具
    tools = await client.get_tools()

    # 4. 建立 Agent (使用 langchain.agents.create_agent)
    system_prompt = "你是一個 Google Workspace 助手。你可以根據用戶要求讀寫 Google Sheets。"
    agent = create_agent(llm, tools, system_prompt=system_prompt)

    # 5. 測試更改試算表
    # 註：你需要提供一個你有權限的 Spreadsheet ID (從網址中獲取)
    sheet_id = "1dh0chvqXjBMliJm3T7KC2JxHdwOKV4AT89xLlIJSE7o"
    query = f"請在試算表 {sheet_id} 的 A1 儲存格中填入 '透過 Ollama 和 MCP 寫入成功'"
    
    # 執行 agent
    result = await agent.ainvoke({"messages": [("user", query)]})
    print(result)

if __name__ == "__main__":
    asyncio.run(main())