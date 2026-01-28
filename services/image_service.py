"""圖片處理服務"""
import base64
from typing import Optional


class ImageService:
    """處理圖片相關的業務邏輯"""
    
    @staticmethod
    def encode_to_base64(image_path: str) -> str:
        """
        將圖片編碼為 base64 格式
        
        Args:
            image_path: 圖片檔案路徑
            
        Returns:
            base64 編碼的字串
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    @staticmethod
    def create_image_data_url(image_path: str, mime_type: Optional[str] = "image/jpeg") -> str:
        """
        創建圖片的 data URL
        
        Args:
            image_path: 圖片檔案路徑
            mime_type: 圖片的 MIME 類型
            
        Returns:
            完整的 data URL
        """
        image_data = ImageService.encode_to_base64(image_path)
        return f"data:{mime_type};base64,{image_data}"
