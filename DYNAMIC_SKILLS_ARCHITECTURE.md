# 动态 Skills 架构（按照 Anthropic 官方设计）

## 🎯 目标

实现 Anthropic 官方的 **渐进式揭露（Progressive Disclosure）** 模型：
- Agent 自己决定使用哪个 Skill
- 按需加载 Skill 内容（节省 tokens）
- 支持多个 Skills，可扩展

## 📚 官方架构：三级加载

根据 [Anthropic 官方文档](https://platform.claude.com/docs/zh-TW/agents-and-tools/agent-skills/overview)：

### 级别 1：元数据（始终加载）

**内容：** Skill 的 YAML 前置资料（name + description）

**加载时机：** 在 Agent 启动时

**Token 成本：** 每个 Skill 约 100 tokens

**示例：**
```
可用的 Skills：
- google-sheets: 操作 Google Sheets 的专业技能
- email-assistant: 发送和管理电子邮件
- web-scraper: 从网页提取数据
```

### 级别 2：指令（触发时加载）

**内容：** SKILL.md 的主体内容（指导、最佳实践、工作流程）

**加载时机：** 当 Agent 决定需要这个 Skill 时

**Token 成本：** 少于 5k tokens

**触发方式：** Agent 调用 `load_skill("google-sheets")`

### 级别 3：资源和工具（根据需要加载）

**内容：** 
- Python 工具函数（tools.py）
- 其他参考文档
- 脚本和模板

**加载时机：** Skill 被激活后

**Token 成本：** 实际上无限制（工具代码不占用 context）

## 🔄 工作流程

```
启动：
  系统提示 = "你是助手\n\n可用 Skills：\n- google-sheets: ...\n- email: ..."
  工具 = [load_skill]  # 只有一个工具

用户："在 Google Sheets 的 A1 写入 Hello"
  ↓
Agent 分析：这需要 google-sheets Skill
  ↓
Agent 调用：load_skill("google-sheets")
  ↓
系统加载：
  1. SKILL.md 内容 → Context
  2. tools.py 中的工具 → 可用工具列表
  ↓
Agent 获得：完整指导 + write_cell 等工具
  ↓
Agent 调用：write_cell(spreadsheet_id="...", cell="A1", value="Hello")
  ↓
Agent 回答：用户
```

## 🏗️ 实现

### 方案 1：真正的动态加载（理想但复杂）

**挑战：** LangGraph 的 agent 在创建后工具列表是固定的，不能动态添加工具。

**解决方案：** 使用 `AgentState` 和自定义图：

```python
# 需要自己构建 LangGraph
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    messages: list
    loaded_skills: list
    available_tools: list

def should_load_skill(state):
    # 判断是否需要加载 skill
    pass

def load_skill_node(state):
    # 加载 skill 并更新可用工具
    pass

def use_tool_node(state):
    # 使用工具
    pass
```

**优点：** 完全符合 Anthropic 架构  
**缺点：** 实现复杂，需要自己构建图

### 方案 2：预加载工具 + Prompt 控制（实用）⭐

**思路：** 
- 预加载所有 Skills 的工具（但 Agent 不知道怎么用）
- 在 system prompt 中只显示元数据
- 提供 `load_skill` 工具返回完整指导
- Agent 加载 Skill 后才知道如何使用工具

**实现：**

```python
# 1. 发现所有 Skills（元数据）
skill_manager = DynamicSkillManager(SkillLoader())
available_skills = skill_manager.discover_all()

# 2. 构建 system prompt（只包含元数据）
system_prompt = f"""你是智能助手。

可用的 Skills：
{skill_manager.get_metadata_summary()}

工作流程：
1. 分析用户需求
2. 如果需要某个 Skill，先调用 load_skill("<skill-name>")
3. 获得完整指导后，使用工具完成任务
"""

# 3. 预加载所有工具（但 Agent 暂时不知道如何使用）
all_tools = skill_manager.get_all_tools()  # load_skill + 所有 skill 工具

# 4. 创建 Agent
agent = create_agent(llm, all_tools, system_prompt=system_prompt)
```

**优点：** 
- ✅ Agent 可以自己决定使用哪个 Skill
- ✅ 按需加载指导内容（节省 tokens）
- ✅ 使用标准的 `create_agent`，简单

**缺点：**
- 工具实际上已经预加载（不是真正的"级别 3 按需加载"）
- 但工具代码本身不占用 context，只有工具的 schema 占用少量 tokens

### 方案 3：Two-Step Agent（最简单）

**思路：**
1. 第一步：Agent 决定需要哪些 Skills
2. 第二步：加载这些 Skills 后重新创建 Agent

```python
# 步骤 1: 规划 Agent
planner_prompt = """你是规划助手。
可用 Skills: google-sheets, email, web-scraper

分析用户请求，回答需要哪个 Skill（只回答 skill 名称）。
"""
planner = create_agent(llm, [], system_prompt=planner_prompt)
result = await planner.ainvoke({"messages": [("user", user_query)]})
needed_skill = result['messages'][-1].content.strip()

# 步骤 2: 加载 Skill 并创建执行 Agent
content = skill_loader.load(needed_skill)
tools = skill_loader.load_tools(needed_skill)
executor = create_agent(llm, tools, system_prompt=content)
result = await executor.ainvoke({"messages": [("user", user_query)]})
```

**优点：** 
- ✅ 真正的动态加载
- ✅ 最节省 tokens
- ✅ 实现简单

**缺点：**
- 需要两次对话（规划 + 执行）
- 用户体验可能稍慢

## 📁 文件对比

### 现有实现

#### `sheets_direct.py`（直接加载）
```python
# 启动时就加载所有内容
skill_content = loader.load("google-sheets")  # 立即加载
tools = loader.load_tools("google-sheets")    # 立即加载

system_prompt = f"""你是助手。\n{skill_content}"""
agent = create_agent(llm, tools, system_prompt)
```

**特点：**
- ❌ 不管用户需不需要，都加载所有内容
- ❌ 如果有多个 Skills，全部会占用 context
- ✅ 实现简单

#### `sheets_auto.py`（半自动）
```python
# 预加载所有工具，但 prompt 中提示 agent 先 load_skill
all_tools = []
for skill in available_skills:
    tools = loader.load_tools(skill['name'])
    all_tools.extend(tools)

all_tools.append(load_skill_tool)
agent = create_agent(llm, all_tools, system_prompt)
```

**特点：**
- ⚠️ 工具已经预加载（占用少量 tokens）
- ✅ Agent 可以看到所有 Skills 的元数据
- ✅ Agent 可以调用 load_skill 获取指导
- ⚠️ 不是真正的"按需加载工具"

### 新实现

#### `sheets_dynamic.py`（完全动态）⭐ 推荐

```python
# 只加载元数据
skill_manager = DynamicSkillManager(loader)
available_skills = skill_manager.discover_all()

# System prompt 只包含元数据
system_prompt = f"""可用 Skills：
{skill_manager.get_metadata_summary()}

必须先调用 load_skill 才能使用 Skill。
"""

# 初始只有 load_skill 工具
initial_tools = [skill_manager.get_load_skill_tool()]

# Agent 调用 load_skill 后，skill_manager 会添加工具
agent = create_agent(llm, skill_manager.get_all_tools(), system_prompt)
```

**特点：**
- ✅ Agent 自己决定需要哪个 Skill
- ✅ 按需加载 Skill 内容（节省 tokens）
- ✅ 完全符合 Anthropic 架构
- ⚠️ 工具需要预加载（LangGraph 限制）

## 🧪 测试对比

### 直接加载（sheets_direct.py）

```bash
python sheets_direct.py
```

**Token 使用：**
- System prompt: ~5000 tokens（完整 SKILL.md）
- 工具 schema: ~500 tokens
- 总计启动成本: ~5500 tokens

**行为：**
- Agent 直接使用工具
- 无需加载 Skill

### 动态加载（sheets_dynamic.py）

```bash
python sheets_dynamic.py
```

**Token 使用：**
- System prompt: ~300 tokens（只有元数据）
- 第一次使用时加载 SKILL.md: +5000 tokens
- 工具 schema: ~500 tokens
- 总计启动成本: ~300 tokens
- 使用时成本: ~5800 tokens

**行为：**
1. Agent 分析用户请求
2. Agent 决定需要 google-sheets
3. Agent 调用 load_skill("google-sheets")
4. Agent 获得完整指导
5. Agent 使用工具完成任务

**优势：**
- 如果用户请求不需要任何 Skill → 节省 5000 tokens
- 如果有 10 个 Skills，只加载需要的 → 节省更多

## 📊 Token 节省示例

假设你有 5 个 Skills，每个 5000 tokens 的指导：

### 直接加载方式
```
启动成本 = 5 × 5000 = 25,000 tokens
每次对话都要消耗这些 tokens
```

### 动态加载方式
```
启动成本 = 5 × 100 = 500 tokens（只有元数据）
使用 1 个 Skill = 500 + 5000 = 5,500 tokens
使用 2 个 Skills = 500 + 10,000 = 10,500 tokens

节省 = 25,000 - 5,500 = 19,500 tokens（使用 1 个 Skill）
节省 = 25,000 - 10,500 = 14,500 tokens（使用 2 个 Skills）
```

## 🔮 未来改进

### 真正的动态工具加载

如果 LangGraph 将来支持动态添加工具，我们可以实现：

```python
# 理想实现
agent = DynamicAgent(llm, system_prompt)

# Agent 运行时
agent.on_skill_loaded = lambda skill_name, tools: agent.add_tools(tools)

# Agent 自己调用 load_skill 时，工具会自动添加
```

### 多 Agent 系统

```python
# 规划 Agent
planner = Agent(llm, tools=[])
needed_skills = planner.plan(user_query)

# 为每个 Skill 创建专门的 Agent
agents = {
    skill: create_agent(llm, load_skill_tools(skill))
    for skill in needed_skills
}

# 协调执行
coordinator.execute(user_query, agents)
```

## 📝 总结

| 实现 | 启动成本 | Agent 决定 | 按需加载 | 复杂度 |
|------|----------|-----------|----------|--------|
| sheets_direct.py | 高（5500 tokens） | ❌ 否 | ❌ 否 | 低 |
| sheets_auto.py | 中（300 + 所有工具） | ⚠️ 半自动 | ⚠️ 部分 | 中 |
| sheets_dynamic.py | 低（300 tokens） | ✅ 是 | ✅ 是 | 中 |

**推荐：**
- **单一 Skill 项目**：使用 `sheets_direct.py`（简单直接）
- **多个 Skills 项目**：使用 `sheets_dynamic.py`（符合官方架构，节省 tokens）

## 🚀 使用指南

### 运行动态 Skills 版本

```bash
python sheets_dynamic.py
```

### 预期行为

```
用户: 在 Google Sheets 的 A1 写入 Hello

Agent 思考：这需要 google-sheets Skill
  ↓
Agent 调用：load_skill("google-sheets")
  ↓
系统返回：完整的 SKILL.md 内容 + 工具列表
  ↓
Agent 理解：现在我知道如何使用 write_cell 了
  ↓
Agent 调用：write_cell(...)
  ↓
Agent 回答："✅ 已写入"
```

### 查看执行过程

运行后会显示完整的步骤：

```
🔍 完整执行过程:

  步骤 1: [HumanMessage]
    内容: 在试算表 XXX 的 A1 写入 Hello

  步骤 2: [AIMessage]
    调用工具: load_skill
    参数: {'skill_name': 'google-sheets'}

  步骤 3: [ToolMessage]
    返回: ✅ Skill 'google-sheets' 已加载
          
          ## 可用工具
          read_cell, write_cell, ...
          
          ## 使用指导
          [完整的 SKILL.md 内容]

  步骤 4: [AIMessage]
    调用工具: write_cell
    参数: {'spreadsheet_id': '...', 'cell': 'A1', 'value': 'Hello'}

  步骤 5: [ToolMessage]
    返回: ✅ 成功写入

  步骤 6: [AIMessage]
    内容: 已成功在 A1 写入 Hello
```

## 🎓 与 Anthropic 官方对比

### Anthropic 的实现（Claude.ai / API）

```
启动：
  系统提示包含所有 Skills 的元数据
  Claude 使用 bash 读取文件系统
  
触发：
  Claude 执行：bash: cat pdf-skill/SKILL.md
  内容加载到 context
  
执行：
  Claude 执行 Python 脚本或调用工具
```

### 我们的实现（sheets_dynamic.py）

```
启动：
  系统提示包含所有 Skills 的元数据
  提供 load_skill 工具
  
触发：
  Agent 调用：load_skill("google-sheets")
  DynamicSkillManager 返回 SKILL.md 内容
  
执行：
  Agent 使用预加载的工具（write_cell 等）
```

**差异：**
- Anthropic 使用文件系统 + bash
- 我们使用 Python 函数 + 工具调用

**相同点：**
- ✅ 元数据始终可见
- ✅ 完整内容按需加载
- ✅ Agent 自己决定
- ✅ 节省 tokens

## 📂 相关文件

- `sheets_dynamic.py` - 完整的动态 Skills 实现
- `utils/skill_loader.py` - Skill 加载器（支持动态加载）
- `skills/google-sheets/SKILL.md` - Skill 元数据和指导
- `skills/google-sheets/tools.py` - Skill 工具函数

## 🔗 参考资源

- [Anthropic Agent Skills 文档](https://platform.claude.com/docs/zh-TW/agents-and-tools/agent-skills/overview)
- [工程博客：使用 Agent Skills 为真实世界的代理做好准备](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Skills Cookbook](https://github.com/anthropics/claude-cookbooks/tree/main/skills)

## ✅ 下一步

1. 运行 `sheets_dynamic.py` 测试新架构
2. 添加更多 Skills（email、web-scraper 等）
3. 观察 Agent 如何自动选择合适的 Skill
4. 根据需要优化 Skill 的 description 以提高匹配准确度
