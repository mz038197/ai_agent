# Agent 模式使用指南

## 📚 概述

本项目已集成 LangChain Agent 功能，支持 LLM 自主调用工具来完成复杂任务。

## 🎯 四种运行模式对比

| 模式 | 命令 | 工作方式 | 适用场景 |
|------|------|---------|---------|
| **聊天模式** | `/chat` | 纯 LLM 对话，不使用知识库 | 闲聊、常识问题 |
| **RAG 模式** | `/rag` | 强制检索知识库 | 查询已上传的文档 |
| **自动模式** | `/auto` | 基于相似度自动判断是否检索 | 混合场景（默认） |
| **Agent 模式** | `/agent` | LLM 自主决定使用哪些工具 | 复杂查询、需要多种信息源 |

## 🛠️ Agent 可用工具

### 1. 内部知识库检索 (`internal_knowledge_search`)
- 检索已上传的文档内容
- 适合：技术文档、课程资料、内部知识

### 2. 网络搜索 (`web_search`)
- 使用 DuckDuckGo 搜索互联网
- 适合：时事新闻、最新技术、实时信息

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载支持工具调用的模型

Agent 模式需要支持函数调用的模型：

```bash
# 推荐模型（按性能排序）
ollama pull qwen2.5:7b        # 推荐，中文支持好
ollama pull llama3.1:8b       # 也不错
ollama pull mistral:7b        # 英文为主
```

### 3. 启动应用

```bash
chainlit run app.py
```

### 4. 切换到 Agent 模式

在聊天界面输入：
```
/agent
```

## 💡 使用示例

### 示例 1：混合查询（知识库 + 网络）

**用户提问：**
```
RAG 在 LangChain 的典型做法是什么？如果我要找最新消息又该怎么做？
```

**Agent 行为：**
1. 🔍 使用 `internal_knowledge_search` 查询知识库中的 RAG 资料
2. 🌐 使用 `web_search` 搜索最新的 LangChain 新闻
3. 📝 综合两个工具的结果生成回答

### 示例 2：仅知识库查询

**用户提问：**
```
我的文档中关于数据库设计的部分说了什么？
```

**Agent 行为：**
1. 🔍 仅使用 `internal_knowledge_search`
2. 📝 基于文档内容回答

### 示例 3：仅网络搜索

**用户提问：**
```
今天的天气怎么样？
```

**Agent 行为：**
1. 🌐 仅使用 `web_search`
2. 📝 返回搜索结果

### 示例 4：无需工具

**用户提问：**
```
你好，今天心情怎么样？
```

**Agent 行为：**
1. 💬 不使用任何工具，直接回答

## ⚙️ 配置说明

在 `app.py` 中调整配置：

```python
CONFIG = {
    "AGENT_MODEL": "qwen2.5:7b",      # Agent 使用的模型
    "AGENT_TEMPERATURE": 0,           # 温度（Agent 建议用 0）
    "ENABLE_WEB_SEARCH": True,        # 是否启用网络搜索
    # ... 其他配置
}
```

### AgentService 参数

```python
agent_service = AgentService(
    vector_store_service=vector_service,
    model="qwen2.5:7b",              # 模型名称
    base_url="http://localhost:11434",
    temperature=0,                    # 温度
    enable_web_search=True,           # 启用网络搜索
    web_search_results=5,             # 搜索结果数量
    retriever_k=4,                    # 知识库检索数量
    verbose=True                      # 显示推理过程（调试用）
)
```

## 🔧 故障排除

### Agent 模式不可用

**可能原因：**
1. 未安装支持工具调用的模型
2. 模型版本过旧
3. 网络搜索工具初始化失败

**解决方案：**
```bash
# 1. 确保下载了正确的模型
ollama pull qwen2.5:7b

# 2. 检查 Ollama 版本
ollama --version  # 建议 >= 0.1.0

# 3. 测试模型是否支持工具调用
ollama run qwen2.5:7b
```

### 网络搜索失败

如果网络搜索工具无法使用：

```python
# 在 app.py 中禁用网络搜索
CONFIG = {
    "ENABLE_WEB_SEARCH": False,  # 设为 False
    # ...
}
```

### Agent 响应缓慢

Agent 需要多次推理，会比普通模式慢：

1. 使用更快的模型（如 `qwen2.5:7b`）
2. 减少 `max_iterations`（在 `agent_service.py` 中）
3. 对简单问题使用其他模式

## 📊 性能对比

| 模式 | 响应速度 | 准确性 | 灵活性 | 成本 |
|------|---------|--------|--------|------|
| Chat | ⚡⚡⚡ | ⭐⭐ | ⭐ | 💰 |
| RAG | ⚡⚡ | ⭐⭐⭐ | ⭐⭐ | 💰💰 |
| Auto | ⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 💰💰 |
| Agent | ⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 💰💰💰 |

## 🎨 架构设计

```
用户输入
    ↓
AgentService
    ↓
LLM (决策)
    ↓
┌─────────┬─────────────┐
│         │             │
Tool 1    Tool 2      Tool N
知识库    网络搜索     ...
│         │             │
└─────────┴─────────────┘
    ↓
聚合结果
    ↓
最终回答
```

## 📝 开发说明

### 添加新工具

在 `AgentService._create_tools()` 中添加：

```python
from langchain_community.tools import WikipediaQueryRun

# 创建新工具
wiki_tool = WikipediaQueryRun(
    name="wikipedia_search",
    description="搜索维基百科"
)

tools.append(wiki_tool)
```

### 自定义系统提示词

在 `AgentService._get_system_prompt()` 中修改：

```python
def _get_system_prompt(self) -> str:
    return """你的自定义提示词..."""
```

## 🔗 相关资源

- [LangChain 官方文档](https://python.langchain.com/)
- [Ollama 模型列表](https://ollama.com/library)
- [DuckDuckGo 搜索 API](https://github.com/deedy5/duckduckgo_search)

## ❓ 常见问题

### Q: Agent 模式和 Auto 模式有什么区别？

**Auto 模式：**
- 基于相似度分数判断
- 固定的决策逻辑（硬编码）
- 只能使用知识库

**Agent 模式：**
- LLM 动态决策
- 可以使用多个工具
- 更智能，但更慢更贵

### Q: 什么时候应该使用 Agent 模式？

- ✅ 需要综合多种信息源（知识库 + 网络）
- ✅ 复杂的多步推理
- ✅ 不确定需要哪些工具时
- ❌ 简单的问答
- ❌ 对速度要求高的场景

### Q: 能否保留对话历史？

Agent 模式支持对话历史，修改 `app.py`：

```python
# 在用户会话中保存历史
chat_history = cl.user_session.get("chat_history", [])
result = agent_service.query(
    user_input=message.content,
    chat_history=chat_history  # 传入历史
)
```

## 📈 后续规划

- [ ] 支持更多工具（计算器、数据库查询等）
- [ ] 优化 Agent 提示词
- [ ] 添加工具使用统计
- [ ] 支持流式输出
- [ ] 集成更强大的搜索引擎

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
