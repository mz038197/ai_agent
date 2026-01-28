from langchain_ollama import OllamaLLM


def main():
    # 初始化 Ollama LLM
    # 默认使用 llama2 模型，你可以根据需要更改为其他已安装的模型
    llm = OllamaLLM(
        model="gemma3:4b",  # 可以更改为 "llama3", "mistral", "codellama" 等
        base_url="http://localhost:11434",  # Ollama 默认地址
        temperature=0.7,  # 控制随机性，0-1之间
    )
    
    print("成功連接到 Ollama LLM!")
    print("=" * 50)
    
    try:
       
        while True:
            user_input = input("\n你: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("拜拜！下次再見!")
                break
            
            if not user_input:
                continue
            
            response = llm.invoke(user_input)
            print(f"\n模型: {response}")
            
    except Exception as e:
        print(f"错误: {str(e)}")
        print("\n请确保:")
        print("1. Ollama 已安装并运行 (ollama serve)")
        print("2. 已下载模型 (ollama pull llama2)")
        print("3. Ollama 服务运行在 http://localhost:11434")


if __name__ == "__main__":
    main()
