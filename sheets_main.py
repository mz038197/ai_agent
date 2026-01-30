"""使用自定义 Google Sheets MCP Server 的示例"""
import asyncio
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

async def main():
    # 1. 初始化 Ollama
    llm = ChatOllama(model="llama3.2:3b", temperature=0)

    # 2. 建立 MCP Client，连接自定义的 Google Sheets server
    client = MultiServerMCPClient({
        "google_sheets": {
            "transport": "stdio",
            "command": "python",
            "args": ["sheets_server.py"],
            "env": {
                "GOOGLE_APPLICATION_CREDENTIALS": "./credentials.json"
            }
        }
    })

    # 3. 载入 MCP 工具
    print("正在载入 Google Sheets 工具...")
    try:
        tools = await client.get_tools()
        print(f"成功载入 {len(tools)} 个工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
    except Exception as e:
        print(f"载入工具失败: {e}")
        print("\n请确保:")
        print("1. 已安装: pip install gspread google-auth")
        print("2. credentials.json 文件存在")
        print("3. 服务账号有 Google Sheets 权限")
        return

    # 4. 建立 Agent
    system_prompt = "你是一个 Google Sheets 助手。你可以读取和写入 Google Sheets 的数据。"
    agent = create_agent(llm, tools, system_prompt=system_prompt)

    # 5. 测试操作
    # 注意：请将下面的 spreadsheet_id 替换为你自己的试算表 ID
    spreadsheet_id = "1dh0chvqXjBMliJm3T7KC2JxHdwOKV4AT89xLlIJSE7o"
    
    print(f"\n测试 Google Sheets 操作 (试算表 ID: {spreadsheet_id})")
    print("=" * 60)
    
    # 测试 1: 写入数据
    print("\n测试 1: 写入数据到 A1")
    query = f"请在试算表 {spreadsheet_id} 的 A1 单元格写入 'Hello from MCP!'"
    result = await agent.ainvoke({"messages": [("user", query)]})
    print(f"回答: {result['messages'][-1].content}")
    
    # 测试 2: 读取数据
    print("\n测试 2: 读取 A1 的数据")
    query = f"读取试算表 {spreadsheet_id} 的 A1 单元格"
    result = await agent.ainvoke({"messages": [("user", query)]})
    print(f"回答: {result['messages'][-1].content}")
    
    # 测试 3: 列出所有工作表
    print("\n测试 3: 列出所有工作表")
    query = f"列出试算表 {spreadsheet_id} 中的所有工作表"
    result = await agent.ainvoke({"messages": [("user", query)]})
    print(f"回答: {result['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(main())
