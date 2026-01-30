"""测试 MCP 连接的简单示例"""
import asyncio
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

async def main():
    # 1. 初始化 Ollama
    llm = ChatOllama(model="llama3.2:3b", temperature=0)

    # 2. 建立 MCP Client，连接本地测试服务器
    client = MultiServerMCPClient({
        "test_server": {
            "transport": "stdio",
            "command": "python",
            "args": ["test_server.py"],
        }
    })

    # 3. 载入 MCP 工具
    print("正在载入 MCP 工具...")
    tools = await client.get_tools()
    print(f"成功载入 {len(tools)} 个工具:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")

    # 4. 建立 Agent
    system_prompt = "你是一个数学助手。你可以执行加法、乘法和问候操作。"
    agent = create_agent(llm, tools, system_prompt=system_prompt)

    # 5. 测试执行
    print("\n测试 1: 数学计算")
    query = "计算 (3 + 5) × 12 等于多少？"
    result = await agent.ainvoke({"messages": [("user", query)]})
    print(f"问题: {query}")
    print(f"回答: {result['messages'][-1].content}\n")

    print("测试 2: 问候")
    query = "跟 Alice 打个招呼"
    result = await agent.ainvoke({"messages": [("user", query)]})
    print(f"问题: {query}")
    print(f"回答: {result['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(main())
