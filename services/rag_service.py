"""RAG（檢索增強生成）服務層"""
from typing import List, Optional
from langchain_core.documents import Document
from .document_service import DocumentService
from .vector_store_service import VectorStoreService
from .llm_service import LLMService


class RAGService:
    """RAG（檢索增強生成）服務 - 整合文檔處理、向量檢索和 LLM 生成"""
    
    def __init__(
        self, 
        document_service: DocumentService,
        vector_store_service: VectorStoreService,
        llm_service: LLMService,
        default_k: int = 4
    ):
        """
        初始化 RAG 服務
        
        Args:
            document_service: 文檔處理服務
            vector_store_service: 向量存儲服務
            llm_service: LLM 服務
            default_k: 預設檢索的文檔數量
        """
        self.doc_service = document_service
        self.vector_service = vector_store_service
        self.llm_service = llm_service
        self.default_k = default_k
    
    def ingest_file(self, file_path: str) -> dict:
        """
        攝入文件到知識庫
        
        Args:
            file_path: 文件路徑
            
        Returns:
            包含處理結果的字典
        """
        # 處理文件（加載 + 分割）
        chunks = self.doc_service.process_file(file_path)
        
        # 添加到向量存儲
        ids = self.vector_service.add_documents(chunks)
        
        return {
            "chunks_count": len(chunks),
            "document_ids": ids,
            "file_path": file_path
        }
    
    def query_with_context(
        self, 
        query: str, 
        k: Optional[int] = None,
        use_mmr: bool = False,
        include_sources: bool = True
    ) -> str:
        """
        使用檢索到的上下文回答問題
        
        Args:
            query: 用戶問題
            k: 檢索的文檔數量（None 則使用預設值）
            use_mmr: 是否使用最大邊際相關性搜索（避免重複內容）
            include_sources: 是否在回答中包含來源信息
            
        Returns:
            AI 回答
        """
        k = k or self.default_k
        
        # 1. 檢索相關文檔
        if use_mmr:
            relevant_docs = self.vector_service.max_marginal_relevance_search(query, k=k)
        else:
            relevant_docs = self.vector_service.similarity_search(query, k=k)
        
        # 如果沒有找到相關文檔
        if not relevant_docs:
            return self.llm_service.send_message(
                f"{query}\n\n（注意：知識庫中沒有找到相關資料，以下是基於模型知識的回答）"
            )
        
        # 2. 構建上下文
        context = self._format_context(relevant_docs)
        
        # 3. 構建提示詞
        prompt = self._build_prompt(query, context)
        
        # 4. 調用 LLM（會自動使用歷史記憶）
        response = self.llm_service.send_message(prompt)
        
        # 5. 如果需要，添加來源信息
        if include_sources:
            sources = self._format_sources(relevant_docs)
            response = f"{response}\n\n{sources}"
        
        return response
    
    def query_with_score(
        self, 
        query: str, 
        k: Optional[int] = None,
        score_threshold: float = 1.5
    ) -> str:
        """
        使用帶分數的檢索（可以過濾不相關的結果）
        
        Args:
            query: 用戶問題
            k: 檢索的文檔數量
            score_threshold: 相似度分數閾值（越低越嚴格）
            
        Returns:
            AI 回答
        """
        k = k or self.default_k
        
        # 檢索帶分數的文檔
        results = self.vector_service.similarity_search_with_score(query, k=k)
        
        # 過濾低分文檔
        filtered_docs = [doc for doc, score in results if score <= score_threshold]
        
        if not filtered_docs:
            return self.llm_service.send_message(
                f"{query}\n\n（注意：知識庫中沒有找到足夠相關的資料）"
            )
        
        # 構建上下文並生成回答
        context = self._format_context(filtered_docs)
        prompt = self._build_prompt(query, context)
        response = self.llm_service.send_message(prompt)
        
        return response
    
    def _format_context(self, documents: List[Document]) -> str:
        """
        格式化檢索到的文檔作為上下文
        
        Args:
            documents: 文檔列表
            
        Returns:
            格式化的上下文字符串
        """
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            # 提取元數據
            source = doc.metadata.get('source', 'Unknown')
            page = doc.metadata.get('page', '')
            
            # 格式化文檔塊
            source_info = f"來源: {source}"
            if page:
                source_info += f", 第 {page} 頁"
            
            context_parts.append(
                f"[文檔片段 {i}] ({source_info})\n{doc.page_content}\n"
            )
        
        return "\n".join(context_parts)
    
    def _format_sources(self, documents: List[Document]) -> str:
        """
        格式化來源信息
        
        Args:
            documents: 文檔列表
            
        Returns:
            格式化的來源信息
        """
        # 去重來源
        sources = set()
        for doc in documents:
            source = doc.metadata.get('source', 'Unknown')
            sources.add(source)
        
        sources_list = list(sources)
        if len(sources_list) == 1:
            return f"📚 **資料來源：** {sources_list[0]}"
        else:
            sources_str = "\n".join([f"  - {s}" for s in sources_list])
            return f"📚 **資料來源：**\n{sources_str}"
    
    def _build_prompt(self, query: str, context: str) -> str:
        """
        構建包含上下文的提示詞
        
        Args:
            query: 用戶問題
            context: 檢索到的上下文
            
        Returns:
            完整的提示詞
        """
        return f"""請根據以下提供的上下文信息來回答問題。

**重要規則：**
1. 僅基於提供的上下文信息回答
2. 如果上下文中沒有相關信息，請明確說明
3. 不要編造或推測上下文中沒有的信息
4. 可以整合多個文檔片段的信息

**上下文信息：**
{context}

**問題：** {query}

**回答：**"""
    
    def get_knowledge_base_stats(self) -> dict:
        """
        獲取知識庫統計信息
        
        Returns:
            統計信息字典
        """
        store_info = self.vector_service.get_store_info()
        
        return {
            "total_chunks": store_info["total_documents"],
            "collection_name": store_info["collection_name"],
            "embedding_model": store_info["embedding_model"],
            "supported_formats": self.doc_service.get_supported_formats()
        }
    
    def clear_knowledge_base(self) -> None:
        """清空整個知識庫"""
        self.vector_service.delete_collection()
    
    def search_documents(self, query: str, k: int = 4) -> List[Document]:
        """
        僅搜索文檔，不生成回答（用於預覽相關文檔）
        
        Args:
            query: 查詢文本
            k: 返回的文檔數量
            
        Returns:
            相關文檔列表
        """
        return self.vector_service.similarity_search(query, k=k)
