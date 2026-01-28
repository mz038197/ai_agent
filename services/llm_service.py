"""LLM 服務層"""
from typing import List, Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, BaseMessage


class LLMService:
    """處理 LLM 相關的業務邏輯"""
    
    def __init__(
        self, 
        model: str = "gemma3:4b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7
    ):
        """
        初始化 LLM 服務
        
        Args:
            model: 模型名稱
            base_url: Ollama 服務地址
            temperature: 溫度參數（控制隨機性）
        """
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.chat = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
        )
    
    def invoke(self, messages: List[BaseMessage]) -> str:
        """
        調用 LLM 生成回應
        
        Args:
            messages: 消息列表
            
        Returns:
            模型的回應文字
        """
        response = self.chat.invoke(messages)
        return response.content
    
    def create_text_message(self, content: str) -> HumanMessage:
        """
        創建純文字訊息
        
        Args:
            content: 文字內容
            
        Returns:
            HumanMessage 對象
        """
        return HumanMessage(content=content)
    
    def create_multimodal_message(
        self, 
        text: str, 
        image_data_url: str
    ) -> HumanMessage:
        """
        創建多模態訊息（文字+圖片）
        
        Args:
            text: 文字內容
            image_data_url: 圖片的 data URL
            
        Returns:
            包含文字和圖片的 HumanMessage
        """
        return HumanMessage(
            content=[
                {"type": "text", "text": text},
                {"type": "image_url", "image_url": image_data_url}
            ]
        )
    
    def process_text(self, text: str) -> str:
        """
        處理純文字輸入
        
        Args:
            text: 用戶輸入的文字
            
        Returns:
            模型的回應
        """
        message = self.create_text_message(text)
        return self.invoke([message])
    
    def process_image_with_text(
        self, 
        text: str, 
        image_data_url: str
    ) -> str:
        """
        處理圖片+文字輸入
        
        Args:
            text: 用戶的問題
            image_data_url: 圖片的 data URL
            
        Returns:
            模型的回應
        """
        message = self.create_multimodal_message(text, image_data_url)
        return self.invoke([message])
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        獲取模型信息
        
        Returns:
            包含模型配置的字典
        """
        return {
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature
        }
