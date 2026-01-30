"""
Google Sheets Agent - Two-Step 架构（最可靠的动态 Skills 实现）

架构：
步骤 1：Agent 分析用户请求，决定需要哪个 Skill
步骤 2：加载该 Skill 的完整内容和工具，创建专门的 Agent 来执行

优点：
- ✅ Agent 自己决定使用哪个 Skill
- ✅ 真正的按需加载（节省 tokens）
- ✅ 实现简单，逻辑清晰
- ✅ 即使是小模型也能正确执行
"""

import asyncio
import os
import sys
import io
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from utils import SkillLoader

# UTF-8 编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


async def main():
    print("=" * 70)
    print("Google Sheets Agent - Two-Step 架构")
    print("=" * 70)
    
    # 环境设置
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./credentials.json"
    
    # 1. 初始化
    skill_loader = SkillLoader()
    llm = ChatOllama(model="llama3.2:3b", temperature=0)
    
    # 2. 发现所有 Skills
    print("\n📚 发现可用的 Skills...")
    skill_names = skill_loader.discover()
    skills_info = []
    
    for name in skill_names:
        metadata = skill_loader.get_metadata(name)
        if metadata:
            skills_info.append(metadata)
            desc = metadata.get('description', '无描述')
            print(f"  - {name}: {desc}")
    
    # 3. 构建元数据列表（用于步骤 1）
    skills_list = "\n".join([
        f"- {s.get('name', 'unknown')}: {s.get('description', '无描述')}"
        for s in skills_info
    ])
    
    # ========== 步骤 1：规划 Agent（决定使用哪个 Skill）==========
    
    planner_prompt = f"""你是一个智能助手，负责分析用户请求并选择合适的 Skill。

可用的 Skills：
{skills_list}

你的任务：
1. 阅读用户的请求
2. 判断需要哪个 Skill（如果不需要任何 Skill，回答"none"）
3. 只回答 Skill 的名称，不要多说

示例：
用户："在 Google Sheets 的 A1 写入 Hello"
你："google-sheets"

用户："今天天气如何？"
你："none"

用户："列出试算表中的所有工作表"
你："google-sheets"

重要：只回答 Skill 名称或"none"，不要解释。
"""
    
    # ========== 测试 ==========
    
    spreadsheet_id = "1dh0chvqXjBMliJm3T7KC2JxHdwOKV4AT89xLlIJSE7o"
    
    print("\n" + "=" * 70)
    print("测试：Two-Step 工作流程")
    print("=" * 70)
    
    # 测试查询
    query = f"在试算表 {spreadsheet_id} 的 C1 写入 'Two-Step Works!'"
    
    print(f"\n用户请求: {query}")
    print("\n" + "-" * 70)
    
    # ========== 步骤 1：规划 ==========
    
    print("\n【步骤 1：规划】Agent 决定需要哪个 Skill...")
    
    planner = create_agent(llm, [], system_prompt=planner_prompt)
    
    planning_result = await planner.ainvoke(
        {"messages": [("user", query)]},
        config={"recursion_limit": 3}
    )
    
    needed_skill = planning_result['messages'][-1].content.strip()
    
    print(f"🎯 Agent 决定: {needed_skill}")
    
    if needed_skill == "none" or not needed_skill:
        print("ℹ️  不需要加载任何 Skill，直接回答用户")
        return
    
    if needed_skill not in [s['name'] for s in skills_info]:
        print(f"❌ Skill '{needed_skill}' 不存在")
        return
    
    # ========== 步骤 2：加载 Skill 并执行 ==========
    
    print(f"\n【步骤 2：执行】加载 '{needed_skill}' Skill...")
    
    # 加载 Skill 的完整内容和工具
    skill_content = skill_loader.load(needed_skill, verbose=False)
    skill_tools = skill_loader.load_tools(needed_skill, verbose=True)
    
    print(f"✅ 已加载 {len(skill_tools)} 个工具: {', '.join([t.name for t in skill_tools])}")
    
    # 构建执行 Agent 的 prompt（简化版本）
    # 注意：不包含完整 SKILL.md，避免太长导致循环
    executor_prompt = """你是 Google Sheets 助手。

工作流程：
1. 理解用户要求
2. 调用对应的工具一次
3. 根据工具返回的结果回答用户
4. 立即停止

可用工具：
- read_cell: 读取单个单元格
- write_cell: 写入单个单元格
- read_range: 读取范围
- list_sheets: 列出所有工作表

示例：
用户："在 A1 写入 Hello"
你：调用 write_cell(...) → 获得结果 → "✅ 已写入"

重要：
- 必须真正调用工具，不要假装
- 只调用一次工具
- 根据真实结果回答
- 完成后停止
"""
    
    # 创建执行 Agent
    print(f"\n🤖 创建执行 Agent...")
    executor = create_agent(llm, skill_tools, system_prompt=executor_prompt)
    
    # 执行任务
    print(f"\n🚀 执行任务...\n")
    
    execution_result = await executor.ainvoke(
        {"messages": [("user", query)]},
        config={"recursion_limit": 10}  # 增加限制
    )
    
    # ========== 显示结果 ==========
    
    print("\n🔍 执行过程:")
    for i, msg in enumerate(execution_result['messages'], 1):
        msg_type = msg.__class__.__name__
        content = str(msg.content)
        
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"  步骤 {i}: 调用工具 {tc['name']}")
                args_str = str(tc['args'])
                if len(args_str) > 100:
                    args_str = args_str[:100] + "..."
                print(f"        参数: {args_str}")
        elif msg_type == 'ToolMessage':
            preview = content[:150]
            if len(content) > 150:
                preview += "..."
            print(f"  步骤 {i}: 工具返回: {preview}")
        else:
            preview = content[:100]
            if len(content) > 100:
                preview += "..."
            print(f"  步骤 {i}: [{msg_type}] {preview}")
    
    print(f"\n" + "=" * 70)
    print(f"🤖 最终回答: {execution_result['messages'][-1].content}")
    print("=" * 70)
    
    print("\n✅ Two-Step 架构的优势:")
    print("  1. Agent 自己决定需要哪个 Skill（步骤 1）")
    print("  2. 只加载需要的 Skill（节省 tokens）")
    print("  3. 执行逻辑简单清晰（步骤 2）")
    print("  4. 即使小模型也能正确执行")
    print("  5. 完全符合 Anthropic 官方架构")


if __name__ == "__main__":
    asyncio.run(main())
