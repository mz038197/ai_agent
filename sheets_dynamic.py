"""
Google Sheets Agent - 动态 Skills 系统（完全按照 Anthropic 官方架构）

架构（三级加载）：
1. 级别 1（始终加载）：所有 Skills 的元数据（name + description）
2. 级别 2（触发时加载）：SKILL.md 的完整指导内容
3. 级别 3（根据需要）：Skill 的工具和资源

工作流程：
用户请求 → Agent 看到元数据 → Agent 决定需要哪个 Skill → 
Agent 调用 load_skill → 获得完整指导 → Agent 使用工具
"""

import asyncio
import os
import sys
import io
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_core.tools import Tool
from utils import SkillLoader

# UTF-8 编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class DynamicSkillManager:
    """管理动态加载的 Skills"""
    
    def __init__(self, skill_loader: SkillLoader):
        self.loader = skill_loader
        self.available_skills = {}  # skill_name -> metadata
        self.loaded_skills = {}     # skill_name -> content
        self.skill_tools = {}       # skill_name -> [tools]
        
    def discover_all(self):
        """发现所有可用的 Skills（级别 1：元数据）"""
        skill_names = self.loader.discover()
        skills = []
        for name in skill_names:
            metadata = self.loader.get_metadata(name)
            if metadata:
                self.available_skills[name] = metadata
                skills.append(metadata)
        return skills
    
    def load_skill(self, skill_name: str) -> str:
        """
        加载 Skill 的完整内容和工具（级别 2 & 3）
        
        这是 Agent 可以调用的工具
        """
        # 处理可能的字典输入
        if isinstance(skill_name, dict):
            skill_name = skill_name.get('skill_name', '')
        
        skill_name = str(skill_name).strip()
        
        if skill_name not in self.available_skills:
            return f"❌ Skill '{skill_name}' 不存在。可用的 Skills: {', '.join(self.available_skills.keys())}"
        
        try:
            # 加载完整指导内容
            content = self.loader.load(skill_name, verbose=False)
            self.loaded_skills[skill_name] = content
            
            # 加载工具
            tools = self.loader.load_tools(skill_name)
            self.skill_tools[skill_name] = tools
            
            tool_names = [t.name for t in tools]
            
            return f"""✅ Skill '{skill_name}' 已加载

## 可用工具
{', '.join(tool_names)}

## 使用指导

{content}

你现在可以使用上述工具来完成任务。请严格遵守指导中的最佳实践。
"""
        except Exception as e:
            return f"❌ 加载失败: {str(e)}"
    
    def get_all_tools(self):
        """获取所有已加载的工具 + load_skill 工具"""
        from langchain_core.tools import StructuredTool
        from pydantic import BaseModel, Field
        
        # 定义 load_skill 的参数 schema
        class LoadSkillInput(BaseModel):
            skill_name: str = Field(description="要加载的 Skill 名称，例如：'google-sheets'")
        
        # 创建 load_skill 工具（使用 StructuredTool）
        load_tool = StructuredTool(
            name="load_skill",
            description="加载一个 Skill 以获取其完整指导和工具。当用户的请求需要特定领域的专业功能时调用。",
            func=self.load_skill,
            args_schema=LoadSkillInput
        )
        
        # 收集所有已加载的 skill 工具
        all_tools = [load_tool]
        for tools in self.skill_tools.values():
            all_tools.extend(tools)
        
        return all_tools
    
    def get_metadata_summary(self) -> str:
        """获取所有 Skills 的元数据摘要（用于 system prompt）"""
        if not self.available_skills:
            return "（没有可用的 Skills）"
        
        lines = []
        for name, info in self.available_skills.items():
            lines.append(f"- **{name}**: {info['description']}")
        
        return "\n".join(lines)


async def main():
    print("=" * 70)
    print("Google Sheets Agent - 动态 Skills 系统")
    print("=" * 70)
    
    # 环境设置
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./credentials.json"
    
    # 1. 创建 Skill 管理器
    skill_manager = DynamicSkillManager(SkillLoader())
    
    # 2. 发现所有 Skills（级别 1：只加载元数据）
    print("\n📚 发现可用的 Skills...")
    available_skills = skill_manager.discover_all()
    print(f"✅ 发现 {len(available_skills)} 个 Skills:")
    for skill in available_skills:
        print(f"  - {skill['name']}: {skill['description']}")
    
    # 3. 构建 system prompt（只包含元数据）
    system_prompt = f"""你是一个智能助手。

## 可用的 Skills

{skill_manager.get_metadata_summary()}

## 工作流程

**你必须严格按照以下步骤操作：**

步骤 1: 分析用户请求
步骤 2: 如果需要专业功能，调用 load_skill("<skill-name>")
步骤 3: 阅读返回的指导内容
步骤 4: **必须调用指导中提到的工具来完成实际任务**
步骤 5: 根据工具返回的结果回答用户

**示例 - 写入任务：**

用户："在 Google Sheets 的 A1 写入 Hello"

你的步骤：
1. 分析：需要 google-sheets Skill
2. 调用 load_skill("google-sheets")
3. 收到：完整指导 + 工具列表（包含 write_cell）
4. **调用 write_cell(spreadsheet_id="...", cell="A1", value="Hello")** ← 必须执行！
5. 收到：工具返回 "✅ 成功写入..."
6. 回答用户："已在 A1 写入 Hello"

**示例 - 读取任务：**

用户："读取 Google Sheets 的 A1"

你的步骤：
1. 如果之前已加载 google-sheets，跳过步骤 2-3
2. 如果未加载，调用 load_skill("google-sheets")
3. **调用 read_cell(spreadsheet_id="...", cell="A1")** ← 必须执行！
4. 收到：工具返回 "✅ 单元格 A1 的值: Hello"
5. 回答用户："A1 的值是 Hello"

**关键规则：**
- ❌ 不能假装完成任务，必须真正调用工具
- ❌ load_skill 只是加载指导，不会执行任务
- ✅ 必须在 load_skill 后再调用实际的工具（write_cell、read_cell 等）
- ✅ 只根据工具返回的真实结果回答用户
"""
    
    # 4. 初始化模型
    print("\n🤖 初始化 Ollama 模型...")
    llm = ChatOllama(
        model="llama3.1:8b",
        temperature=0,
        num_predict=300
    )
    
    # 5. 创建 Agent（初始只有 load_skill 工具）
    print("\n🎯 创建 Agent...")
    
    # 这里我们用一个技巧：预加载所有工具，但通过 prompt 引导 agent 先加载 skill
    all_tools = skill_manager.get_all_tools()
    agent = create_agent(llm, all_tools, system_prompt=system_prompt)
    
    # 6. 测试
    spreadsheet_id = "1dh0chvqXjBMliJm3T7KC2JxHdwOKV4AT89xLlIJSE7o"
    
    print("\n" + "=" * 70)
    print("开始测试")
    print("=" * 70)
    
    # 测试：Agent 应该自动决定加载 google-sheets skill
    print("\n📝 测试：写入数据（Agent 应该先加载 google-sheets）")
    print("-" * 70)
    query = f"在试算表 {spreadsheet_id} 的 B1 写入 'Dynamic Skill!'"
    
    print(f"用户请求: {query}\n")
    
    try:
        result = await agent.ainvoke(
            {"messages": [("user", query)]},
            config={"recursion_limit": 15}  # 需要更多步骤：load_skill + 实际工具
        )
        
        # 详细日志
        print("\n🔍 完整执行过程:")
        for i, msg in enumerate(result['messages'], 1):
            msg_type = msg.__class__.__name__
            content = str(msg.content)
            
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"\n  步骤 {i}: [{msg_type}]")
                    print(f"    调用工具: {tc['name']}")
                    args_str = str(tc['args'])
                    if len(args_str) > 100:
                        args_str = args_str[:100] + "..."
                    print(f"    参数: {args_str}")
            elif msg_type == 'ToolMessage':
                print(f"\n  步骤 {i}: [{msg_type}]")
                preview = content[:200]
                if len(content) > 200:
                    preview += "..."
                print(f"    返回: {preview}")
            else:
                print(f"\n  步骤 {i}: [{msg_type}]")
                print(f"    内容: {content[:150]}...")
        
        print(f"\n" + "=" * 70)
        print(f"🤖 最终回答: {result['messages'][-1].content}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70)
    
    print("\n💡 这个版本实现了 Anthropic 官方架构:")
    print("  1. Agent 看到所有 Skills 的元数据")
    print("  2. Agent 自己决定需要哪个 Skill")
    print("  3. Agent 主动调用 load_skill 加载")
    print("  4. Agent 获得完整指导后使用工具")


if __name__ == "__main__":
    asyncio.run(main())
