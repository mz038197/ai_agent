"""
Google Sheets 工具函数

这些函数会被自动转换为 LangChain Tools。
"""

import os
from typing import Optional
import gspread
from google.oauth2.service_account import Credentials


def _get_sheets_client():
    """获取 Google Sheets 客户端（内部函数）"""
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "./credentials.json")
    
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"找不到凭证文件: {creds_path}")
    
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    credentials = Credentials.from_service_account_file(creds_path, scopes=scope)
    return gspread.authorize(credentials)


def read_cell(spreadsheet_id: str, cell: str, sheet_name: str = "工作表1") -> str:
    """
    读取 Google Sheets 中指定单元格的值
    
    Args:
        spreadsheet_id: 试算表 ID（从网址中获取）
        cell: 单元格位置，例如 "A1"
        sheet_name: 工作表名称，默认为 "工作表1"
    
    Returns:
        单元格的值或错误信息
    """
    try:
        client = _get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # 尝试获取指定的工作表，如果不存在就使用第一个工作表
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except Exception:
            # 如果找不到指定的工作表，使用第一个工作表
            worksheet = spreadsheet.get_worksheet(0)
            actual_sheet = worksheet.title
            value = worksheet.acell(cell).value
            return f"✅ 单元格 {cell} 的值: {value}（工作表：{actual_sheet}，原指定的 '{sheet_name}' 不存在）"
        
        value = worksheet.acell(cell).value
        return f"✅ 单元格 {cell} 的值: {value}"
    except Exception as e:
        return f"❌ 读取失败: {str(e)}"


def write_cell(spreadsheet_id: str, cell: str, value: str, sheet_name: str = "工作表1") -> str:
    """
    写入值到 Google Sheets 的指定单元格
    
    Args:
        spreadsheet_id: 试算表 ID（从网址中获取）
        cell: 单元格位置，例如 "A1"
        value: 要写入的值
        sheet_name: 工作表名称，默认为 "工作表1"
    
    Returns:
        操作结果信息
    """
    try:
        client = _get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # 尝试获取指定的工作表，如果不存在就使用第一个工作表
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except Exception:
            # 如果找不到指定的工作表，使用第一个工作表
            worksheet = spreadsheet.get_worksheet(0)
            actual_sheet = worksheet.title
            worksheet.update_acell(cell, value)
            return f"✅ 成功写入 '{value}' 到单元格 {cell}（工作表：{actual_sheet}，原指定的 '{sheet_name}' 不存在）"
        
        worksheet.update_acell(cell, value)
        return f"✅ 成功写入 '{value}' 到单元格 {cell}"
    except Exception as e:
        return f"❌ 写入失败: {str(e)}"


def read_range(spreadsheet_id: str, range_name: str, sheet_name: str = "工作表1") -> str:
    """
    读取 Google Sheets 中指定范围的值
    
    Args:
        spreadsheet_id: 试算表 ID
        range_name: 范围，例如 "A1:B10"
        sheet_name: 工作表名称
    
    Returns:
        范围内的所有值（JSON 格式）
    """
    try:
        import json
        client = _get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # 尝试获取指定的工作表，如果不存在就使用第一个工作表
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except Exception:
            # 如果找不到指定的工作表，使用第一个工作表
            worksheet = spreadsheet.get_worksheet(0)
            actual_sheet = worksheet.title
            values = worksheet.get(range_name)
            return f"✅ 范围 {range_name} 的值:\n{json.dumps(values, ensure_ascii=False, indent=2)}\n（工作表：{actual_sheet}，原指定的 '{sheet_name}' 不存在）"
        
        values = worksheet.get(range_name)
        return f"✅ 范围 {range_name} 的值:\n{json.dumps(values, ensure_ascii=False, indent=2)}"
    except Exception as e:
        return f"❌ 读取失败: {str(e)}"


def list_sheets(spreadsheet_id: str) -> str:
    """
    列出试算表中的所有工作表
    
    Args:
        spreadsheet_id: 试算表 ID
    
    Returns:
        所有工作表名称列表
    """
    try:
        client = _get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        sheets = [sheet.title for sheet in spreadsheet.worksheets()]
        return f"✅ 工作表列表: {', '.join(sheets)}"
    except Exception as e:
        return f"❌ 列出失败: {str(e)}"


# 定义导出的工具列表（可选，但推荐）
__all__ = ['read_cell', 'write_cell', 'read_range', 'list_sheets']
