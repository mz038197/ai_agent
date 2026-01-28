"""
服務層單元測試範例
演示如何獨立測試業務邏輯
"""
from services import LLMService, ImageService


def test_llm_service_initialization():
    """測試 LLM 服務初始化"""
    service = LLMService(
        model="gemma3:4b",
        base_url="http://localhost:11434",
        temperature=0.7
    )
    
    model_info = service.get_model_info()
    
    assert model_info["model"] == "gemma3:4b"
    assert model_info["base_url"] == "http://localhost:11434"
    assert model_info["temperature"] == 0.7
    
    print("[PASS] LLM 服務初始化測試通過")


def test_image_service_base64_encoding():
    """測試圖片 Base64 編碼"""
    # 注意：需要有實際的圖片文件才能測試
    # 這裡只是示範測試結構
    try:
        # 假設有一個測試圖片
        # image_data = ImageService.encode_to_base64("test_image.jpg")
        # assert len(image_data) > 0
        print("[SKIP] 圖片編碼測試需要實際圖片文件")
    except Exception as e:
        print(f"[SKIP] 圖片測試跳過: {e}")


def test_llm_service_message_creation():
    """測試訊息創建"""
    service = LLMService()
    
    # 測試文字訊息
    text_msg = service.create_text_message("你好")
    assert text_msg.content == "你好"
    
    # 測試多模態訊息
    multimodal_msg = service.create_multimodal_message(
        "描述這張圖片",
        "data:image/jpeg;base64,test_data"
    )
    assert isinstance(multimodal_msg.content, list)
    assert len(multimodal_msg.content) == 2
    
    print("[PASS] 訊息創建測試通過")


def test_image_service_data_url_creation():
    """測試 Data URL 創建"""
    # 這是一個 mock 測試，實際使用時需要真實圖片
    try:
        # data_url = ImageService.create_image_data_url("test.jpg")
        # assert data_url.startswith("data:image/jpeg;base64,")
        print("[SKIP] Data URL 測試需要實際圖片文件")
    except Exception as e:
        print(f"[SKIP] Data URL 測試跳過: {e}")


if __name__ == "__main__":
    print("開始運行服務層測試...\n")
    
    test_llm_service_initialization()
    test_image_service_base64_encoding()
    test_llm_service_message_creation()
    test_image_service_data_url_creation()
    
    print("\n測試完成！")
