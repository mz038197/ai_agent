"""简单的 Google Sheets MCP 服务器"""
from mcp.server.fastmcp import FastMCP
import json
import os
from typing import Optional

# 注意：这需要安装 gspread 和 google-auth
# pip install gspread google-auth

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

mcp = FastMCP("GoogleSheets")

def get_sheets_client():
    """获取 Google Sheets 客户端"""
    if not GSPREAD_AVAILABLE:
        raise ImportError("请先安装: pip install gspread google-auth")
    
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "./credentials.json")
    
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"找不到凭证文件: {creds_path}")
    
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    credentials = Credentials.from_service_account_file(creds_path, scopes=scope)
    return gspread.authorize(credentials)

@mcp.tool()
def read_cell(spreadsheet_id: str, cell: str, sheet_name: str = "工作表1") -> str:
    """
    读取 Google Sheets 中指定单元格的值
    
    参数:
        spreadsheet_id: 试算表 ID（从网址中获取）
        cell: 单元格位置，例如 "A1"
        sheet_name: 工作表名称，默认为 "工作表1"
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        value = worksheet.acell(cell).value
        return f"单元格 {cell} 的值: {value}"
    except Exception as e:
        return f"读取失败: {str(e)}"

@mcp.tool()
def write_cell(spreadsheet_id: str, cell: str, value: str, sheet_name: str = "工作表1") -> str:
    """
    写入值到 Google Sheets 的指定单元格
    
    参数:
        spreadsheet_id: 试算表 ID（从网址中获取）
        cell: 单元格位置，例如 "A1"
        value: 要写入的值
        sheet_name: 工作表名称，默认为 "工作表1"
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        worksheet.update_acell(cell, value)
        return f"成功写入 '{value}' 到单元格 {cell}"
    except Exception as e:
        return f"写入失败: {str(e)}"

@mcp.tool()
def read_range(spreadsheet_id: str, range_name: str, sheet_name: str = "工作表1") -> str:
    """
    读取 Google Sheets 中指定范围的值
    
    参数:
        spreadsheet_id: 试算表 ID
        range_name: 范围，例如 "A1:B10"
        sheet_name: 工作表名称
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        values = worksheet.get(range_name)
        return f"范围 {range_name} 的值:\n{json.dumps(values, ensure_ascii=False, indent=2)}"
    except Exception as e:
        return f"读取失败: {str(e)}"

@mcp.tool()
def list_sheets(spreadsheet_id: str) -> str:
    """
    列出试算表中的所有工作表
    
    参数:
        spreadsheet_id: 试算表 ID
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        sheets = [sheet.title for sheet in spreadsheet.worksheets()]
        return f"工作表列表: {', '.join(sheets)}"
    except Exception as e:
        return f"列出失败: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
