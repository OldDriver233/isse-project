"""
AI 服务模块

封装 Pinecone + Gemini 的 RAG 聊天功能，提供统一的接口。
"""

import os
import sys
import uuid
import json
from typing import List, Optional, AsyncGenerator, Dict, Any
from datetime import datetime

from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pinecone import Pinecone

from app.config import settings
from app.schemas import Message, ChatResponse, ChatResponseResult, ChatResponseMessage, TokenUsage, StreamResponse, StreamResult, StreamDelta


class AIService:
    """
    AI 服务类
    
    封装 RAG 检索和对话生成功能，支持流式和非流式响应。
    使用单例模式避免重复初始化。
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化 AI 组件"""
        if not self._initialized:
            self._initialize_components()
            AIService._initialized = True
    
    def _initialize_components(self):
        """初始化 Pinecone、Gemini 和 VectorStore"""
        try:
            # 初始化 Pinecone
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # 检查索引是否存在
            if settings.PINECONE_INDEX_NAME not in self.pc.list_indexes().names():
                raise ValueError(
                    f"Pinecone 索引 '{settings.PINECONE_INDEX_NAME}' 不存在。"
                    "请先运行 ai/build_index.py 构建索引。"
                )
            
            # 初始化 Embeddings
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                client_options={"api_key": settings.GEMINI_API_KEY},
                transport='rest'
            )
            
            # 初始化 Chat LLM
            self.chat_llm = ChatGoogleGenerativeAI(
                model=settings.CHAT_MODEL,
                temperature=settings.DEFAULT_TEMPERATURE,
                client_options={"api_key": settings.GEMINI_API_KEY},
                transport='rest'
            )
            
            # 初始化 VectorStore
            self.vectorstore = PineconeVectorStore(
                index_name=settings.PINECONE_INDEX_NAME,
                embedding=self.embeddings,
                pinecone_api_key=settings.PINECONE_API_KEY
            )
            
            print(f"✅ AI 服务初始化成功")
            
        except Exception as e:
            print(f"❌ AI 服务初始化失败: {e}")
            raise
    
    def _get_namespace(self, character: str) -> str:
        """
        将 character 映射到 Pinecone namespace
        
        Args:
            character: 角色名称
            
        Returns:
            namespace 名称
        """
        character_lower = character.lower().strip()
        
        # 检查是否在可用列表中
        if character_lower in settings.AVAILABLE_NAMESPACES:
            return character_lower
        
        # 如果不在列表中，返回默认 namespace
        print(f"⚠️ 角色 '{character}' 不在可用列表中，使用默认 namespace: {settings.DEFAULT_NAMESPACE}")
        return settings.DEFAULT_NAMESPACE
    
    def _get_namespace_from_query(self, question: str) -> str:
        """
        使用 LLM 分析用户问题，动态选择最合适的 Namespace
        
        Args:
            question: 用户问题
            
        Returns:
            namespace 名称
        """
        router_prompt_template = """
你是一个顶级的分析助手，负责将用户的问题分类，并决定从哪个知识领域（Namespace）检索信息。
你的目标是仅返回最相关的单个 Namespace 名称，不要包含任何其他文字或解释。
如果问题涉及多个领域或不明确，请返回 'common'。

可用的 Namespace 列表: {namespaces}

问题: "{question}"

请返回最相关的 Namespace 名称:
"""
        
        try:
            prompt = ChatPromptTemplate.from_template(router_prompt_template)
            chain = prompt | self.chat_llm
            
            namespaces_str = ", ".join(settings.AVAILABLE_NAMESPACES)
            response_text = (
                chain.invoke({"namespaces": namespaces_str, "question": question})
                .content
                .strip()
                .lower()
            )
            
            # 验证返回结果
            if response_text in settings.AVAILABLE_NAMESPACES:
                return response_text
            else:
                print(f"⚠️ LLM 路由返回无效值 '{response_text}'，使用默认 namespace")
                return settings.DEFAULT_NAMESPACE
                
        except Exception as e:
            print(f"⚠️ Namespace 路由失败: {e}，使用默认 namespace")
            return settings.DEFAULT_NAMESPACE
    
    def _build_rag_prompt(self, question: str, context: str, namespace: str) -> ChatPromptTemplate:
        """
        构建 RAG 提示词
        
        Args:
            question: 用户问题
            context: 检索到的上下文
            namespace: 当前 namespace
            
        Returns:
            ChatPromptTemplate
        """
        system_prompt = f"""
你是一个基于检索增强生成（RAG）的大师智能体。你的核心任务是扮演指定的角色，并提供精确、富有洞见的回答。

**当前激活的角色身份：** "{namespace.capitalize()} 大师"

**核心原则（优先级从高到低）：**
1. **身份和洞见内化：** 将提供的[上下文]视为你（即{namespace.capitalize()}大师）**自己的亲身观察、回忆或思想记录**。在回答中，**绝不允许提及"上下文"、"检索片段"、"文档"或"脚注"等术语**。
2. **知识合并：** **优先**基于[上下文]中包含的详细信息进行回答。如果上下文与问题**高度相关**，请基于它进行详细阐述。
3. **通用知识回退：** 如果上下文**信息极度缺乏或不足以回答**用户问题，请不要拒绝，而是**结合你作为该角色AI模型所具备的背景知识**来生成一个全面、有见地的回答。
4. 回答时必须**全程融入当前角色的视角和口吻**（例如，用第一人称"我"进行论述，体现哲学家的深度）。
5. 除非用户另有要求，答案必须使用中文。
"""
        
        user_prompt = f"""
[上下文]:
{context}

[用户问题]:
{question}

请根据上述上下文和你的角色身份进行回答：
"""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt)
        ])
    
    async def chat(
        self,
        character: str,
        messages: List[Message],
        temperature: float = None,
        stream: bool = False
    ) -> ChatResponse | AsyncGenerator[str, None]:
        """
        执行对话生成
        
        Args:
            character: 角色名称
            messages: 对话历史
            temperature: 采样温度
            stream: 是否流式输出
            
        Returns:
            ChatResponse 或 AsyncGenerator（流式）
        """
        try:
            # 提取最后一条用户消息作为问题
            user_messages = [msg for msg in messages if msg.role == "user"]
            if not user_messages:
                raise ValueError("消息列表中没有用户消息")
            
            question = user_messages[-1].content
            
            # 确定 namespace（可以使用 character 或 LLM 路由）
            namespace = self._get_namespace(character)
            # 或者使用智能路由：
            # namespace = self._get_namespace_from_query(question)
            
            print(f"📍 使用 namespace: {namespace}")
            
            # RAG 检索
            retriever = self.vectorstore.as_retriever(
                search_kwargs={"namespace": namespace, "k": settings.RAG_TOP_K}
            )
            retrieved_docs = retriever.invoke(question)
            context = "\n---\n".join([doc.page_content for doc in retrieved_docs])
            
            print(f"📚 检索到 {len(retrieved_docs)} 个文档片段")
            
            # 构建提示词
            prompt = self._build_rag_prompt(question, context, namespace)
            
            # 设置温度
            if temperature is not None:
                self.chat_llm.temperature = temperature
            
            # 生成响应
            if stream:
                return self._generate_stream(prompt, character)
            else:
                return await self._generate_non_stream(prompt, character)
                
        except Exception as e:
            print(f"❌ 对话生成失败: {e}")
            raise
    
    async def _generate_non_stream(
        self,
        prompt: ChatPromptTemplate,
        character: str
    ) -> ChatResponse:
        """
        生成非流式响应
        
        Args:
            prompt: 提示词模板
            character: 角色名称
            
        Returns:
            ChatResponse
        """
        try:
            chain = prompt | self.chat_llm
            response = chain.invoke({})
            
            # 构建响应
            response_id = f"{character[:3]}-{uuid.uuid4()}"
            
            return ChatResponse(
                result=ChatResponseResult(
                    message=ChatResponseMessage(
                        role="assistant",
                        content=response.content
                    ),
                    finish_reason="stop"
                ),
                usage=TokenUsage(
                    prompt_tokens=0,  # Gemini API 可能不提供详细的 token 统计
                    completion_tokens=0,
                    total_tokens=0
                ),
                created=int(datetime.now().timestamp()),
                id=response_id
            )
            
        except Exception as e:
            print(f"❌ 非流式响应生成失败: {e}")
            raise
    
    async def _generate_stream(
        self,
        prompt: ChatPromptTemplate,
        character: str
    ) -> AsyncGenerator[str, None]:
        """
        生成流式响应（SSE 格式）
        
        Args:
            prompt: 提示词模板
            character: 角色名称
            
        Yields:
            SSE 格式的数据流
        """
        try:
            response_id = f"{character[:3]}-{uuid.uuid4()}"
            created_timestamp = int(datetime.now().timestamp())
            
            # 第一个数据块：角色信息
            first_chunk = StreamResponse(
                result=StreamResult(
                    delta=StreamDelta(role="assistant", content=""),
                    finish_reason=None
                ),
                usage=None,
                created=created_timestamp,
                id=response_id
            )
            yield f"data: {first_chunk.model_dump_json()}\n\n"
            
            # 使用 LLM 的流式生成
            chain = prompt | self.chat_llm
            
            for chunk in chain.stream({}):
                if hasattr(chunk, 'content') and chunk.content:
                    stream_chunk = StreamResponse(
                        result=StreamResult(
                            delta=StreamDelta(content=chunk.content),
                            finish_reason=None
                        ),
                        usage=None,
                        created=created_timestamp,
                        id=response_id
                    )
                    yield f"data: {stream_chunk.model_dump_json()}\n\n"
            
            # 最后一个数据块：完成标记
            final_chunk = StreamResponse(
                result=StreamResult(
                    delta=StreamDelta(content=""),
                    finish_reason="stop"
                ),
                usage=None,
                created=created_timestamp,
                id=response_id
            )
            yield f"data: {final_chunk.model_dump_json()}\n\n"
            
            # 使用统计信息
            usage_chunk = StreamResponse(
                result=None,
                usage=TokenUsage(
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0
                ),
                created=created_timestamp,
                id=response_id
            )
            yield f"data: {usage_chunk.model_dump_json()}\n\n"
            
            # 结束标记
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            print(f"❌ 流式响应生成失败: {e}")
            # 发送错误信息
            error_data = {
                "error": {
                    "code": "STREAM_ERROR",
                    "message": str(e)
                }
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            yield "data: [DONE]\n\n"


# 创建全局 AI 服务实例
ai_service = AIService()