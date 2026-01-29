"""文檔處理服務層"""
from typing import List
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class DocumentService:
    """處理文檔加載、分割等業務邏輯"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化文檔服務
        
        Args:
            chunk_size: 每個文本塊的大小（字符數）
            chunk_overlap: 塊之間的重疊字符數（保證上下文連貫）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]  # 優先在段落處分割
        )
    
    def load_document(self, file_path: str) -> List[Document]:
        """
        根據文件類型自動選擇加載器
        
        Args:
            file_path: 文件路徑
            
        Returns:
            文檔列表
            
        Raises:
            ValueError: 不支援的文件格式
        """
        file_path_lower = file_path.lower()
        
        if file_path_lower.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path_lower.endswith('.txt'):
            loader = TextLoader(file_path, encoding='utf-8')
        elif file_path_lower.endswith(('.md', '.markdown')):
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            raise ValueError(f"不支援的文件格式: {file_path}")
        
        return loader.load()
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        將文檔分割成小塊
        
        Args:
            documents: 原始文檔列表
            
        Returns:
            分割後的文檔塊列表
        """
        return self.text_splitter.split_documents(documents)
    
    def process_file(self, file_path: str) -> List[Document]:
        """
        完整的文件處理流程：加載 -> 分割
        
        Args:
            file_path: 文件路徑
            
        Returns:
            處理後的文檔塊列表
        """
        # 加載文檔
        documents = self.load_document(file_path)
        
        # 分割文檔
        chunks = self.split_documents(documents)
        
        return chunks
    
    def get_supported_formats(self) -> List[str]:
        """
        獲取支援的文件格式列表
        
        Returns:
            支援的文件格式列表
        """
        return ['.pdf', '.txt', '.md', '.markdown']
