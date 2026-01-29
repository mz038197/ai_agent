"""
Agent 服務測試腳本
用於測試 AgentService 的功能
"""
from services import (
    DocumentService,
    VectorStoreService,
    AgentService
)


def test_agent():
    """測試 Agent 功能"""
    
    print("=" * 60)
    print("🤖 Agent 服務測試")
    print("=" * 60)
    
    # 1. 初始化服務
    print("\n📦 初始化服務...")
    
    vector_service = VectorStoreService(
        persist_directory="./chroma_db",
        embedding_model="nomic-embed-text",
        base_url="http://localhost:11434"
    )
    
    print(f"✅ 向量存儲服務已初始化")
    print(f"   - 知識庫文檔數: {vector_service.get_collection_count()}")
    
    # 2. 初始化 Agent
    print("\n🤖 初始化 Agent 服務...")
    
    try:
        agent_service = AgentService(
            vector_store_service=vector_service,
            model="qwen2.5:7b",  # 確保已下載此模型
            base_url="http://localhost:11434",
            temperature=0,
            enable_web_search=True,
            verbose=True  # 顯示推理過程
        )
        print("✅ Agent 服務已初始化")
        
        # 顯示工具信息
        tools = agent_service.list_tools()
        print(f"\n🛠️ 可用工具 ({len(tools)} 個):")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description'][:50]}...")
        
    except Exception as e:
        print(f"❌ Agent 初始化失敗: {e}")
        print("\n請確保:")
        print("1. Ollama 服務正在運行")
        print("2. 已下載支持工具調用的模型: ollama pull qwen2.5:7b")
        return
    
    # 3. 測試查詢
    print("\n" + "=" * 60)
    print("📝 開始測試查詢")
    print("=" * 60)
    
    test_queries = [
        {
            "name": "測試 1：知識庫查詢",
            "query": "RAG 是什麼？",
            "expected": "應該檢索知識庫"
        },
        {
            "name": "測試 2：網路搜尋",
            "query": "今天的日期是幾號？",
            "expected": "應該使用網路搜尋"
        },
        {
            "name": "測試 3：混合查詢",
            "query": "RAG 在 LangChain 的做法是什麼？最新的版本有什麼更新？",
            "expected": "應該同時使用知識庫和網路搜尋"
        },
        {
            "name": "測試 4：閒聊",
            "query": "你好，今天心情怎麼樣？",
            "expected": "不應該使用任何工具"
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{'─' * 60}")
        print(f"🧪 {test['name']}")
        print(f"❓ 問題: {test['query']}")
        print(f"🎯 預期: {test['expected']}")
        print(f"{'─' * 60}\n")
        
        try:
            result = agent_service.query(test['query'])
            
            if result['success']:
                print(f"✅ 回答:\n{result['answer']}\n")
                
                # 顯示使用的工具
                if result.get('intermediate_steps'):
                    print(f"🔧 使用的工具:")
                    for step in result['intermediate_steps']:
                        if hasattr(step[0], 'tool'):
                            print(f"   - {step[0].tool}")
            else:
                print(f"❌ 錯誤: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            print(f"❌ 查詢失敗: {e}")
        
        # 詢問是否繼續
        if i < len(test_queries):
            input("\n⏸️  按 Enter 繼續下一個測試...")
    
    print("\n" + "=" * 60)
    print("✅ 測試完成")
    print("=" * 60)


def quick_test():
    """快速測試單個查詢"""
    print("🤖 Agent 快速測試\n")
    
    # 初始化
    vector_service = VectorStoreService()
    agent_service = AgentService(
        vector_store_service=vector_service,
        model="qwen2.5:7b",
        verbose=True
    )
    
    # 自定義查詢
    query = input("請輸入測試問題: ").strip()
    if not query:
        query = "RAG 是什麼？"
    
    print(f"\n問題: {query}\n")
    print("─" * 60)
    
    result = agent_service.query(query)
    
    if result['success']:
        print(f"\n回答:\n{result['answer']}")
    else:
        print(f"\n錯誤: {result.get('error')}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_test()
    else:
        test_agent()
