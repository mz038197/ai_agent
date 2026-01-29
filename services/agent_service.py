"""Agent 服務層 - 整合工具調用能力"""
from typing import Dict, Any, Optional
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama


class AgentService:
    """
    Agent 服務 - 使用 LangChain Agent 自動判斷並調用工具
    
    特點：
    - LLM 自主決定何時使用知識庫檢索
    - LLM 自主決定何時使用網路搜尋
    - 支援多工具協作
    - 適合複雜推理場景
    """
    
    def __init__(
        self,
        vector_store_service,
        model: str = "qwen2.5:7b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0,
        enable_web_search: bool = True,
        web_search_results: int = 5,
        retriever_k: int = 4,
        verbose: bool = True
    ):
        """
        初始化 Agent 服務
        
        Args:
            vector_store_service: 向量存儲服務實例
            model: 支持工具調用的模型（推薦：qwen2.5, llama3.1, mistral）
            base_url: Ollama 服務地址
            temperature: 溫度參數（Agent 建議用較低值）
            enable_web_search: 是否啟用網路搜尋工具
            web_search_results: 網路搜尋結果數量
            retriever_k: 知識庫檢索文檔數量
            verbose: 是否顯示詳細推理過程
        """
        self.vector_service = vector_store_service
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.verbose = verbose
        self.retriever_k = retriever_k
        
        # 初始化 LLM（用於 Agent）
        self.llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
        )
        
        # 初始化工具
        self.tools = self._create_tools(enable_web_search, web_search_results)
        
        # 初始化 Agent
        self.agent_executor = self._create_agent()
    
    def _create_tools(self, enable_web_search: bool, num_results: int) -> list:
        """
        創建工具列表
        
        Args:
            enable_web_search: 是否啟用網路搜尋
            num_results: 搜尋結果數量
            
        Returns:
            工具列表
        """
        tools = []
        
        # 1. 知識庫檢索工具
        retriever = self.vector_service.vector_store.as_retriever(
            search_kwargs={"k": self.retriever_k}
        )
        
        retriever_tool = create_retriever_tool(
            retriever,
            name="internal_knowledge_search",
            description=(
                "查詢內部知識庫（RAG）。"
                "適合查詢已上傳的文檔、課程資料、技術文件等固定知識。"
                "當用戶詢問文檔內容、技術細節、已知資料時使用此工具。"
            )
        )
        tools.append(retriever_tool)
        
        # 2. 網路搜尋工具（可選）
        if enable_web_search:
            try:
                web_search_tool = DuckDuckGoSearchResults(
                    name="web_search",
                    num_results=num_results,
                    description=(
                        "在網際網路上搜尋最新資訊。"
                        "適合查詢時事新聞、最新技術動態、實時數據等。"
                        "當用戶需要最新資訊或知識庫中沒有的外部事實時使用。"
                    )
                )
                tools.append(web_search_tool)
            except Exception as e:
                print(f"⚠️ 網路搜尋工具初始化失敗: {e}")
        
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """
        創建 Agent Executor
        
        Returns:
            AgentExecutor 實例
        """
        # 定義 Agent 的提示詞
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("placeholder", "{chat_history}"),  # 支援多輪對話
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),  # Agent 推理過程
        ])
        
        # 創建 Agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # 創建 Executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.verbose,
            max_iterations=5,  # 最大推理步驟
            handle_parsing_errors=True,  # 處理解析錯誤
        )
        
        return agent_executor
    
    def _get_system_prompt(self) -> str:
        """
        獲取系統提示詞
        
        Returns:
            系統提示詞字符串
        """
        return """你是一個專業、嚴謹的 AI 助手，具備使用工具的能力。

**工具使用規則：**
1. **內部知識庫問題** → 使用 `internal_knowledge_search`
   - 文檔內容、技術細節、課程資料等
   
2. **需要最新資訊/外部事實** → 使用 `web_search`
   - 時事新聞、最新技術、實時數據等
   
3. **一般閒聊/常識問題** → 不使用工具，直接回答

**回答要求：**
- 使用繁體中文回答
- 基於工具返回的內容作答
- 清楚標註資訊來源（內部知識庫/網路搜尋）
- 如果工具沒有找到相關資訊，請明確說明
- 不要編造或猜測工具中沒有的資訊

**當前時間：** 請提供準確、有幫助的回答。"""
    
    def query(
        self, 
        user_input: str,
        chat_history: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        使用 Agent 處理用戶查詢
        
        Args:
            user_input: 用戶輸入
            chat_history: 對話歷史（可選）
            
        Returns:
            包含回答和元數據的字典
        """
        try:
            # 準備輸入
            agent_input = {
                "input": user_input,
                "chat_history": chat_history or []
            }
            
            # 調用 Agent
            result = self.agent_executor.invoke(agent_input)
            
            return {
                "answer": result["output"],
                "intermediate_steps": result.get("intermediate_steps", []),
                "success": True
            }
            
        except Exception as e:
            return {
                "answer": f"❌ Agent 執行時發生錯誤: {str(e)}",
                "error": str(e),
                "success": False
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        獲取 Agent 配置信息
        
        Returns:
            配置信息字典
        """
        return {
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "tools": [tool.name for tool in self.tools],
            "tool_descriptions": {
                tool.name: tool.description 
                for tool in self.tools
            },
            "retriever_k": self.retriever_k
        }
    
    def list_tools(self) -> list:
        """
        列出所有可用工具
        
        Returns:
            工具名稱列表
        """
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools
        ]
