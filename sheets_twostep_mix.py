"""
Google Sheets Agent - Two-Step 混合架構
步驟 1：使用 LCEL Chain（更現代）
步驟 2：使用 create_agent（更簡單）
"""

import asyncio
import os
import sys
import io
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from utils import SkillLoader

# UTF-8 編碼
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


async def main():
    print("=" * 70)
    print("Google Sheets Agent - Two-Step 混合架構")
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
    
    # 3. 建立 metadata 清單
    skills_list = "\n".join([
        f"- {s.get('name', 'unknown')}: {s.get('description', '無描述')}"
        for s in skills_info
    ])
    
    # ========== 步驟 1：規劃（使用 LCEL）==========
    
    print("\n" + "=" * 70)
    print("步驟 1：建立 Planner（LCEL 版本）")
    print("=" * 70)
    
    # 原版（create_agent）的 prompt 內容
    planner_system_prompt = f"""你是一個智慧助理，負責分析使用者請求並選擇合適的 Skill。

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

重要：只回答 Skill 名稱或 "none"，不要解釋。"""
    
    # === LCEL 寫法開始 ===
    
    # 1. 建立 ChatPromptTemplate（取代 system_prompt 參數）
    planner_prompt_template = ChatPromptTemplate.from_messages([
        ("system", planner_system_prompt),  # system 訊息
        ("user", "{query}")                  # user 訊息，{query} 是變數
    ])
    
    print("✅ 建立 ChatPromptTemplate")
    print(f"   - system message: {len(planner_system_prompt)} 字元")
    print(f"   - user message 變數: query")
    
    # 2. 建立 LCEL Chain（使用 | 運算符串接）
    planner_chain = (
        planner_prompt_template    # 步驟 1: 格式化 prompt
        | llm                       # 步驟 2: 調用 LLM
        | StrOutputParser()         # 步驟 3: 將回應轉成字串
    )
    
    print("✅ 建立 LCEL Chain")
    print("   流程: ChatPromptTemplate → LLM → StrOutputParser")
    
    # 說明：這個 Chain 等同於原版的：
    # planner = create_agent(llm, [], system_prompt=planner_prompt)
    
    # === LCEL 寫法結束 ===
    
    # ========== 測試 ==========
    
    spreadsheet_id = "1dh0chvqXjBMliJm3T7KC2JxHdwOKV4AT89xLlIJSE7o"
    
    print("\n" + "=" * 70)
    print("測試：Two-Step 工作流程")
    print("=" * 70)
    
    query = f"在試算表 {spreadsheet_id} 的 C1 寫入 'Two-Step Works!'"
    
    print(f"\n使用者請求: {query}")
    print("\n" + "-" * 70)
    
    # ========== 執行步驟 1：規劃 ==========
    
    print("\n【步驟 1：規劃】使用 LCEL Chain 決定需要哪個 Skill...")
    
    # === LCEL 調用方式 ===
    
    # 原版調用方式：
    # planning_result = await planner.ainvoke(
    #     {"messages": [("user", query)]},
    #     config={"recursion_limit": 3}
    # )
    # needed_skill = planning_result['messages'][-1].content.strip()
    
    # LCEL 調用方式（更簡潔）：
    needed_skill = await planner_chain.ainvoke({"query": query})
    
    # 說明差異：
    # 1. 輸入格式：{"query": query} 而不是 {"messages": [("user", query)]}
    # 2. 輸出格式：直接得到字串，而不是 messages 列表
    # 3. 不需要從 result['messages'][-1].content 提取
    # 4. StrOutputParser 已經自動 strip() 了
    
    needed_skill = needed_skill.strip()  # 額外清理（保險起見）
    
    print(f"🎯 Chain 決定: {needed_skill}")
    print(f"   （原版需要: planning_result['messages'][-1].content.strip()）")
    print(f"   （LCEL 直接返回字串）")
    
    # === LCEL 調用結束 ===
    
    if needed_skill == "none" or not needed_skill:
        print("ℹ️  不需要載入任何 Skill，直接回答使用者")
        return
    
    if needed_skill not in [s['name'] for s in skills_info]:
        print(f"❌ Skill '{needed_skill}' 不存在")
        return
    
    # ========== 步驟 2：載入 Skill 並執行（保留 create_agent）==========
    
    print(f"\n" + "=" * 70)
    print(f"步驟 2：執行（保留 create_agent 版本）")
    print("=" * 70)
    
    print(f"\n【步驟 2：執行】載入 '{needed_skill}' Skill...")
    
    # 載入 Skill 的完整內容與工具
    skill_content = skill_loader.load(needed_skill, verbose=False)
    skill_tools = skill_loader.load_tools(needed_skill, verbose=True)
    
    print(f"✅ 已載入 {len(skill_tools)} 個工具: {', '.join([t.name for t in skill_tools])}")
    
    # 動態建立執行 Agent 的 prompt
    tool_descriptions = []
    for tool in skill_tools:
        desc = tool.description.split('\n')[0].strip() if tool.description else '工具函數'
        tool_descriptions.append(f"- {tool.name}: {desc}")
    
    tool_list = "\n".join(tool_descriptions)
    
    # 取得 Skill 的角色說明
    skill_metadata = skills_info[[s['name'] for s in skills_info].index(needed_skill)]
    skill_desc = skill_metadata.get('description', '專業助理')
    
    executor_prompt = f"""你是專業助理，專精於：{skill_desc}

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
- 完成後停止"""
    
    # === 這裡保留原版的 create_agent ===
    
    print("\n🤖 建立執行 Agent（使用 create_agent）...")
    print("   為什麼保留 create_agent？")
    print("   - 自動處理工具調用循環")
    print("   - 自動管理 tool_calls 和 tool_results")
    print("   - 程式碼更簡潔")
    
    executor = create_agent(llm, skill_tools, system_prompt=executor_prompt)
    
    # === 原版調用方式不變 ===
    
    print("\n🚀 執行任務...\n")
    
    execution_result = await executor.ainvoke(
        {"messages": [("user", query)]},
        config={"recursion_limit": 10}
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
    
    # ========== 總結對比 ==========
    
    print("\n" + "=" * 70)
    print("總結：混合架構的優勢")
    print("=" * 70)
    print("""
步驟 1（Planner）使用 LCEL：
  ✅ 更簡潔的代碼
  ✅ 直接返回字串結果
  ✅ 更好的可組合性
  ✅ 支援串流（如需要）
  
步驟 2（Executor）使用 create_agent：
  ✅ 自動處理工具調用
  ✅ 不需要手動管理工具循環
  ✅ 程式碼更簡單
  ✅ 更穩定可靠

這是「最佳實踐」的混合方案！
""")


if __name__ == "__main__":
    asyncio.run(main())