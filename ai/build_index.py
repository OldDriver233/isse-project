"""
build_index.py

功能：
    读取 data/ 目录下的文本文件，
    将其分块、向量化嵌入，并上传至 Pinecone 向量数据库。

执行：
    python ai/build_index.py

运行前提：
    - 需先在 ai/.env 中配置 API 密钥。
    - 确保 data/ 文件夹下有对应的社会学家文本资料。
"""

import os
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import DashScopeEmbeddings
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone, ServerlessSpec

load_dotenv(dotenv_path="ai/.env")

INDEX_NAME = "sociology-master"
DATA_ROOT = "data"


def main():
    """主函数：构建 Pinecone 索引并上传文本数据"""

    # 初始化 Pinecone
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    except Exception as e:
        print(f"致命错误: 无法初始化 Pinecone 客户端: {e}")
        return

    # 删除旧索引，避免重复数据
    try:
        pc.delete_index(INDEX_NAME)
        print(f"旧索引 '{INDEX_NAME}' 已成功删除。")
    except Exception:
        print(f"索引 '{INDEX_NAME}' 不存在或删除失败，继续创建新索引。")

    # 创建新索引
    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME,
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    embeddings = DashScopeEmbeddings(
        model="text-embedding-v4",
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
    )
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500,
                                              chunk_overlap=200)

    print(f"开始遍历 '{DATA_ROOT}' 文件夹并载入到 Pinecone 索引: {INDEX_NAME}")

    # 遍历 DATA_ROOT 下的所有子文件夹
    for root, _, files in os.walk(DATA_ROOT):
        # 只有当 root 不等于 DATA_ROOT 根目录时（即在子文件夹内）才定义 namespace
        if root == DATA_ROOT:
            NAMESPACE_NAME = "common"  # 根目录下的文件视为 'common' namespace
        else:
            # 提取子文件夹的名称作为 namespace
            NAMESPACE_NAME = os.path.basename(root)

        # 遍历当前子文件夹下的所有文件
        for file_name in files:
            if file_name.endswith(".txt"):  # 仅处理 .txt 文件
                file_path = os.path.join(root, file_name)

                try:
                    # 读取文本
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()

                    # 分割文本
                    docs = splitter.split_text(text)

                    # 写入向量数据库
                    PineconeVectorStore.from_texts(
                        docs,
                        embeddings,
                        index_name=INDEX_NAME,
                        namespace=NAMESPACE_NAME
                    )

                    print(f"文件 '{file_path}' (Namespace: {NAMESPACE_NAME}) 已成功载入。")  # noqa: E501

                except FileNotFoundError:
                    print(f"警告：未找到文件 '{file_path}'。")
                except Exception as e:
                    print(f"处理文件 '{file_path}' 时发生错误: {e}")


if __name__ == "__main__":
    main()
