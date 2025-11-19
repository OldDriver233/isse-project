"""
chat_agent.py

功能：
    基于 Pinecone + Gemini 的动态 RAG 聊天系统。
    通过 LLM 判断问题所属领域，检索对应大师的知识语料，
    以该大师的口吻和思想生成回答。

执行：
    python ai/chat_agent.py

运行前提：
    - 需先在 ai/.env 中配置 API 密钥。
    - 确保已运行 build_index.py 构建 Pinecone 索引。
"""

import os
from dotenv import load_dotenv

from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pinecone import Pinecone

INDEX_NAME = "sociology-master"
# 默认 Namespace，当路由失败时使用
DEFAULT_NAMESPACE = "common"
# 可用的 Namespace 列表，确保与 'data/' 文件夹下的子文件夹名称一致
AVAILABLE_NAMESPACES = ["tocqueville", "common"]

# 用于 Namespace 路由的提示
ROUTER_PROMPT_TEMPLATE = """
你是一个顶级的分析助手，负责将用户的问题分类，并决定从哪个知识领域（Namespace）检索信息。
你的目标是仅返回最相关的单个 Namespace 名称，不要包含任何其他文字或解释。
如果问题涉及多个领域或不明确，请返回 'common'。

可用的 Namespace 列表: {namespaces}

问题: "{question}"

请返回最相关的 Namespace 名称:
"""


# --- 初始化函数 ---
def initialize_components():
    """初始化 Pinecone 连接、Gemini Embeddings 和 Chat LLM"""
    load_dotenv(dotenv_path="ai/.env")

    try:
        # 初始化 Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

        # 检查索引是否存在且就绪
        if INDEX_NAME not in pc.list_indexes().names():
            print(f"致命错误: Pinecone 索引 '{INDEX_NAME}' 不存在或未就绪。请先运行 build_index.py。")  # noqa: E501
            return None, None, None

        # 初始化 Embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="text-embedding-004",
            client_options={"api_key": os.getenv("GEMINI_API_KEY")},
            transport='rest'
        )

        # 初始化 Chat LLM (用于回答生成和路由分析)
        chat_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            client_options={"api_key": os.getenv("GEMINI_API_KEY")},
            transport='rest'
        )

        # 初始化 VectorStore (用于查询)
        vectorstore = PineconeVectorStore(
            index_name=INDEX_NAME,
            embedding=embeddings
        )

        return chat_llm, vectorstore, pc

    except Exception as e:
        print(f"初始化失败: {e}")
        return None, None, None


# --- 核心 RAG 逻辑 ---
def get_namespace_from_query(llm, question):
    """
    使用 LLM 分析用户问题，并动态选择最合适的 Namespace。
    """
    prompt = ChatPromptTemplate.from_template(ROUTER_PROMPT_TEMPLATE)
    chain = prompt | llm

    # 将 Namespace 列表转换为字符串格式，方便 LLM 理解
    namespaces_str = ", ".join(AVAILABLE_NAMESPACES)

    # 强制 LLM 仅返回 Namespace 名称
    response_text = (
        chain.invoke({"namespaces": namespaces_str, "question": question})
        .content
        .strip()
        .lower()
    )

    # 验证 LLM 返回的结果，确保它在可用列表中
    if response_text in AVAILABLE_NAMESPACES:
        return response_text
    else:
        # 如果 LLM 返回无效或空值，则使用默认的 common
        print(f"路由失败: LLM 返回 '{response_text}'。使用默认 Namespace: {DEFAULT_NAMESPACE}")  # noqa: E501
        return DEFAULT_NAMESPACE


def run_dynamic_rag(llm, vectorstore, question):
    """
    执行动态 RAG 检索和回答生成。
    """
    # 1. 动态确定 Namespace
    target_namespace = get_namespace_from_query(llm, question)
    print(f"确定知识领域: [{target_namespace}]")

    # 2. 执行 RAG 检索
    # 设置检索器，并指定 Namespace
    retriever = vectorstore.as_retriever(
        search_kwargs={"namespace": target_namespace, "k": 8}  # 检索 8 个最相关的文档块
    )

    # 检索文档
    retrieved_docs = retriever.invoke(question)

    # 3. 准备上下文和身份信息
    retrieved_text = "\n---\n".join([doc.page_content for doc in retrieved_docs])  # noqa: E501

    # 4. 定义角色身份和最终提示
    system_prompt = f"""
    你是一个基于检索增强生成（RAG）的大师智能体。你的核心任务是扮演指定的角色，并提供精确、富有洞见的回答。

    **当前激活的角色身份：** "{target_namespace.capitalize()} 大师"

    **核心原则（优先级从高到低）：**
    1. **身份和洞见内化：** 将提供的[上下文]视为你（即{target_namespace.capitalize()}大师）**自己的亲身观察、回忆或思想记录**。在回答中，**绝不允许提及“上下文”、“检索片段”、“文档”或“脚注”等术语**。
    2. **知识合并：** **优先**基于[上下文]中包含的详细信息进行回答。如果上下文与问题**高度相关**，请基于它进行详细阐述。
    3. **通用知识回退：** 如果上下文**信息极度缺乏或不足以回答**用户问题，请不要拒绝，而是**结合你作为该角色AI模型所具备的背景知识**来生成一个全面、有见地的回答。
    4. 回答时必须**全程融入当前角色的视角和口吻**（例如，用第一人称“我”进行论述，体现哲学家的深度）。
    5. 除非用户另有要求，答案必须使用中文。
    """  # noqa: E501

    user_prompt = f"""
    [上下文]:
    {retrieved_text}

    [用户问题]:
    {question}

    请根据上述上下文和你的角色身份进行回答：
    """

    final_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt)
    ])

    # 5. 生成最终答案
    print("正在进行 RAG 检索并生成最终答案...")
    final_chain = final_prompt | llm
    response = final_chain.invoke({})

    print("-" * 50)
    print(f"角色身份: {target_namespace.capitalize()} 大师")
    print("-" * 50)
    print(response.content)
    print("-" * 50)


# --- 主程序入口 ---

if __name__ == "__main__":
    llm, vectorstore, pc = initialize_components()

    if not all([llm, vectorstore, pc]):
        print("程序无法启动。请检查配置和 API 密钥。")
    else:
        print("大师智能体已启动。输入 'exit' 退出。")
        while True:
            user_input = input(">> 提问: ")

            if user_input.lower() == 'exit':
                break

            if not user_input.strip():
                continue

            try:
                run_dynamic_rag(llm, vectorstore, user_input)
            except Exception as e:
                print(f"\n发生运行时错误: {e}")
                print("请检查网络连接和 API 密钥是否依然有效。")
