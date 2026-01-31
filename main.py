from langchain_ollama import ChatOllama


def main():
    # 初始化 Ollama LLM
    # 默认使用 llama2 模型，你可以根据需要更改为其他已安装的模型
    llm = ChatOllama(model="gemma3:4b")


if __name__ == "__main__":
    main()
