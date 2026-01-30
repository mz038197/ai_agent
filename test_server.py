"""简单的 MCP 测试服务器"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("TestServer")

@mcp.tool()
def add(a: int, b: int) -> int:
    """两个数字相加"""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """两个数字相乘"""
    return a * b

@mcp.tool()
def greet(name: str) -> str:
    """问候用户"""
    return f"你好，{name}！"

if __name__ == "__main__":
    mcp.run(transport="stdio")
