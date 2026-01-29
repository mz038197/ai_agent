"""LLM 服務層"""
from typing import List, Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


class LLMService:
    """處理 LLM 相關的業務邏輯"""
    
    def __init__(
        self, 
        model: str = "gemma3:4b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        max_history: int = 20
    ):
        """
        初始化 LLM 服務
        
        Args:
            model: 模型名稱
            base_url: Ollama 服務地址
            temperature: 溫度參數（控制隨機性）
            max_history: 保留的最大歷史訊息數量（預設 20 條，即 10 輪對話）
        """
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_history = max_history
        self.chat = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
        )
        # 對話歷史記錄
        self.messages: List[BaseMessage] = []
    

    def send_message(
        self, 
        content: str, 
        image_url: Optional[str] = None
    ) -> str:
        """
        統一的訊息發送接口（對外唯一方法）
        自動判斷是純文字還是多模態訊息，並管理對話歷史
        
        Args:
            content: 用戶輸入的文字內容
            image_url: 可選的圖片 URL（base64 data URL 或普通 URL）
            
        Returns:
            模型的回應文字
        """

        content=[{"type": "text", "text": content}]
        if image_url:
            content.append({"type": "image_url", "image_url": image_url})
            
        user_message = HumanMessage(content=content)
        
        # 將新訊息加入歷史
        self.messages.append(user_message)
        
        # 限制歷史長度（避免 token 超限）
        messages_to_send = self._get_limited_history()
        
        # 調用模型
        response = self.chat.invoke(messages_to_send)
        
        # 將 AI 回應加入歷史
        ai_message = AIMessage(content=response.content)
        self.messages.append(ai_message)
        
        return response.content
    
    def _get_limited_history(self) -> List[BaseMessage]:
        """
        獲取受限制的歷史訊息（內部方法）
        只保留最近的 max_history 條訊息
        
        Returns:
            受限制的訊息列表
        """
        if len(self.messages) > self.max_history:
            return self.messages[-self.max_history:]
        return self.messages
    
    def clear_history(self) -> None:
        """清除對話歷史"""
        self.messages = []
    
    def get_history_length(self) -> int:
        """
        獲取當前歷史訊息數量
        
        Returns:
            訊息數量
        """
        return len(self.messages)
    
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
