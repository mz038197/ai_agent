"""向量存儲服務層"""
from typing import List, Optional, Tuple
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document


class VectorStoreService:
    """處理向量存儲的業務邏輯（使用 Chroma DB）"""
    
    def __init__(
        self, 
        persist_directory: str = "./chroma_db",
        embedding_model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
        collection_name: str = "documents"
    ):
        """
        初始化向量存儲服務
        
        Args:
            persist_directory: Chroma DB 存儲路徑
            embedding_model: Ollama 嵌入模型名稱（需先下載：ollama pull nomic-embed-text）
            base_url: Ollama 服務地址
            collection_name: 集合名稱
        """
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.base_url = base_url
        
        # 初始化嵌入模型
        self.embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url=base_url
        )
        
        # 初始化或加載向量存儲
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        添加文檔到向量存儲
        
        Args:
            documents: 文檔列表
            
        Returns:
            文檔 ID 列表
        """
        ids = self.vector_store.add_documents(documents)
        return ids
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 4
    ) -> List[Document]:
        """
        相似度搜索
        
        Args:
            query: 查詢文本
            k: 返回的文檔數量
            
        Returns:
            相關文檔列表
        """
        return self.vector_store.similarity_search(query, k=k)
    
    def similarity_search_with_score(
        self, 
        query: str, 
        k: int = 4
    ) -> List[Tuple[Document, float]]:
        """
        帶分數的相似度搜索（分數越低表示越相關）
        
        Args:
            query: 查詢文本
            k: 返回的文檔數量
            
        Returns:
            (文檔, 相似度分數) 的列表
        """
        return self.vector_store.similarity_search_with_score(query, k=k)
    
    def max_marginal_relevance_search(
        self, 
        query: str, 
        k: int = 4,
        fetch_k: int = 20
    ) -> List[Document]:
        """
        最大邊際相關性搜索（避免返回重複內容）
        
        Args:
            query: 查詢文本
            k: 返回的文檔數量
            fetch_k: 初始檢索的文檔數量
            
        Returns:
            相關且多樣化的文檔列表
        """
        return self.vector_store.max_marginal_relevance_search(
            query, 
            k=k, 
            fetch_k=fetch_k
        )
    
    def delete_collection(self) -> None:
        """刪除整個集合（清空知識庫）"""
        self.vector_store.delete_collection()
        
        # 重新初始化空的向量存儲
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )
    
    def get_collection_count(self) -> int:
        """
        獲取集合中的文檔數量
        
        Returns:
            文檔塊的總數量
        """
        try:
            return self.vector_store._collection.count()
        except Exception:
            return 0
    
    def search_by_metadata(
        self, 
        query: str, 
        metadata_filter: dict,
        k: int = 4
    ) -> List[Document]:
        """
        根據元數據過濾的搜索
        
        Args:
            query: 查詢文本
            metadata_filter: 元數據過濾條件（例如：{"source": "manual.pdf"}）
            k: 返回的文檔數量
            
        Returns:
            符合條件的文檔列表
        """
        return self.vector_store.similarity_search(
            query, 
            k=k, 
            filter=metadata_filter
        )
    
    def get_store_info(self) -> dict:
        """
        獲取向量存儲的信息
        
        Returns:
            包含存儲信息的字典
        """
        return {
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "embedding_model": self.embedding_model,
            "total_documents": self.get_collection_count()
        }
