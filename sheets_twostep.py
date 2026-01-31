"""
Google Sheets Agent - Two-Step 架構（最可靠的動態 Skills 實作）

架構：
步驟 1：Agent 分析使用者請求，決定需要哪個 Skill
步驟 2：載入該 Skill 的完整內容與工具，建立專門的 Agent 來執行

優點：
- ✅ Agent 自己決定使用哪個 Skill
- ✅ 真正的按需載入（節省 tokens）
- ✅ 實作簡單，邏輯清晰
- ✅ 即使是小模型也能正確執行
"""

import asyncio
import os
import sys
import io
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from utils import SkillLoader

# UTF-8 編碼
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


async def main():
    print("=" * 70)
    print("Google Sheets Agent - Two-Step 架構")
    print("=" * 70)
    
    # 環境設定
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./credentials.json"
    
    # 1. 初始化
    skill_loader = SkillLoader()
    llm = ChatOllama(model="llama3.2:3b", temperature=0)
    
    # 2. 探索所有 Skills
    print("\n📚 探索可用的 Skills...")
    skill_names = skill_loader.discover()
    skills_info = []
    
    for name in skill_names:
        metadata = skill_loader.get_metadata(name)
        if metadata:
            skills_info.append(metadata)
            desc = metadata.get('description', '無描述')
            print(f"  - {name}: {desc}")
    
    # 3. 建立 metadata 清單（用於步驟 1）
    skills_list = "\n".join([
        f"- {s.get('name', 'unknown')}: {s.get('description', '無描述')}"
        for s in skills_info
    ])
    
    # ========== 步驟 1：規劃 Agent（決定使用哪個 Skill）==========
    
    planner_prompt = f"""
        你是一個智慧助理，負責分析使用者請求並選擇合適的 Skill。

        可用的 Skills：
        {skills_list}

        你的任務：
        1. 閱讀使用者的請求
        2. 判斷需要哪個 Skill（如果不需要任何 Skill，回答 "none"）
        3. 只回答 Skill 的名稱，不要多說

        示例：
        使用者："在 Google Sheets 的 A1 寫入 Hello"
        你："google-sheets"

        使用者："今天天氣如何？"
        你："none"

        使用者："列出試算表中的所有工作表"
        你："google-sheets"

        重要：只回答 Skill 名稱或 "none"，不要解釋。
        """
    
    # ========== 測試 ==========
    
    spreadsheet_id = "1dh0chvqXjBMliJm3T7KC2JxHdwOKV4AT89xLlIJSE7o"
    
    print("\n" + "=" * 70)
    print("測試：Two-Step 工作流程")
    print("=" * 70)
    
    # 測試查詢
    query = f"在試算表 {spreadsheet_id} 的 C1 寫入 'Two-Step Works!'"
    
    print(f"\n使用者請求: {query}")
    print("\n" + "-" * 70)
    
    # ========== 步驟 1：規劃 ==========
    
    print("\n【步驟 1：規劃】Agent 決定需要哪個 Skill...")
    
    planner = create_agent(llm, [], system_prompt=planner_prompt)
    
    planning_result = await planner.ainvoke(
        {"messages": [("user", query)]},
        config={"recursion_limit": 3}
    )
    
    needed_skill = planning_result['messages'][-1].content.strip()
    
    print(f"🎯 Agent 決定: {needed_skill}")
    
    if needed_skill == "none" or not needed_skill:
        print("ℹ️  不需要載入任何 Skill，直接回答使用者")
        return
    
    if needed_skill not in [s['name'] for s in skills_info]:
        print(f"❌ Skill '{needed_skill}' 不存在")
        return
    
    # ========== 步驟 2：載入 Skill 並執行 ==========
    
    print(f"\n【步驟 2：執行】載入 '{needed_skill}' Skill...")
    
    # 載入 Skill 的完整內容與工具
    skill_content = skill_loader.load(needed_skill, verbose=False)
    skill_tools = skill_loader.load_tools(needed_skill, verbose=True)
    
    print(f"✅ 已載入 {len(skill_tools)} 個工具: {', '.join([t.name for t in skill_tools])}")
    
    # 動態建立執行 Agent 的 prompt
    # 根據實際載入的 Skill 工具來生成（使用精簡版本避免 context 過長）
    tool_descriptions = []
    for tool in skill_tools:
        # 只取 description 的第一行
        desc = tool.description.split('\n')[0].strip() if tool.description else '工具函數'
        tool_descriptions.append(f"- {tool.name}: {desc}")
    
    tool_list = "\n".join(tool_descriptions)
    
    # 取得 Skill 的角色說明
    skill_metadata = skills_info[[s['name'] for s in skills_info].index(needed_skill)]
    skill_desc = skill_metadata.get('description', '專業助理')
    
    executor_prompt = f"""
        你是專業助理，專精於：{skill_desc}

        工作流程：
        1. 理解使用者要求
        2. 選擇並呼叫適當的工具
        3. 根據工具回傳的結果回答使用者
        4. 完成後立即停止

        可用工具：
        {tool_list}

        重要：
        - 必須真正呼叫工具，不要假裝
        - 根據真實結果回答
        - 完成後停止
        """
    
    # 建立執行 Agent
    print("\n🤖 建立執行 Agent...")
    executor = create_agent(llm, skill_tools, system_prompt=executor_prompt)
    
    # 執行任務
    print("\n🚀 執行任務...\n")
    
    execution_result = await executor.ainvoke(
        {"messages": [("user", query)]},
        config={"recursion_limit": 10}  # 增加限制
    )
    
    # ========== 顯示結果 ==========
    
    print("\n🔍 執行過程:")
    for i, msg in enumerate(execution_result['messages'], 1):
        msg_type = msg.__class__.__name__
        content = str(msg.content)
        
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"  步驟 {i}: 呼叫工具 {tc['name']}")
                args_str = str(tc['args'])
                if len(args_str) > 100:
                    args_str = args_str[:100] + "..."
                print(f"        參數: {args_str}")
        elif msg_type == 'ToolMessage':
            preview = content[:150]
            if len(content) > 150:
                preview += "..."
            print(f"  步驟 {i}: 工具回傳: {preview}")
        else:
            preview = content[:100]
            if len(content) > 100:
                preview += "..."
            print(f"  步驟 {i}: [{msg_type}] {preview}")
    
    print(f"\n" + "=" * 70)
    print(f"🤖 最終回答: {execution_result['messages'][-1].content}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
