"""
LLM and query service - handles LLM interactions and response generation.
"""

from typing import List, Optional, AsyncGenerator
import json
from datetime import datetime

from app.rag.retriever import get_rag_retriever
from app.utils.logger import logger


class LLMService:
    """Service for LLM interactions."""

    def __init__(self, api_key: str = None, model: str = "gpt-4-turbo-preview"):
        """Initialize LLM service."""
        try:
            import openai

            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
            else:
                self.client = openai.OpenAI()

            self.model = model
            logger.info(f"Initialized LLM service with model: {model}")
        except Exception as e:
            logger.warning(f"OpenAI not available: {str(e)}. Using mock responses.")
            self.client = None
            self.model = model

    def _format_context(self, retrieved_chunks: List[dict]) -> str:
        """Format retrieved chunks as context."""
        context = "# Retrieved Documents Context\n\n"

        for i, chunk in enumerate(retrieved_chunks, 1):
            context += f"## Source {i}: {chunk.get('metadata', {}).get('filename', 'Unknown')}\n"
            context += f"Similarity: {chunk['similarity']:.2%}\n"
            context += f"{chunk['text']}\n\n"

        return context

    def _create_system_prompt(self, context: str) -> str:
        """Create system prompt with context."""
        return f"""You are an AI assistant for an organization's internal knowledge base. 
You help employees find information and answer questions based on organizational documents.

Answer questions based strictly on the provided context. If the answer is not in the context, 
say so clearly. Always cite your sources.

{context}

Guidelines:
- Be concise and accurate
- Always mention which document(s) you're referencing
- If uncertain, ask for clarification
- Never make up information not in the context"""

    async def query(
        self,
        query: str,
        retrieved_chunks: List[dict],
        conversation_history: List[dict] = None,
        stream: bool = True,
    ) -> tuple:
        """
        Query the LLM with RAG context.

        Args:
            query: User query
            retrieved_chunks: Retrieved context chunks
            conversation_history: Previous messages for context
            stream: Whether to stream response

        Returns:
            (response_text, sources, response_time_ms)
        """
        try:
            import time

            start_time = time.time()

            # Format context
            context = self._format_context(retrieved_chunks)
            system_prompt = self._create_system_prompt(context)

            # Build messages
            messages = []

            # Add conversation history if provided
            if conversation_history:
                messages.extend(
                    conversation_history[-4:]
                )  # Last 4 messages for context

            # Add current query
            messages.append({"role": "user", "content": query})

            if not self.client:
                # Mock response for development
                response_text = f"(Mock Response) Based on the retrieved documents, here's the answer to '{query}':\n\n"
                response_text += "This is a placeholder response. Configure OpenAI API key for real responses."
            else:
                # Call OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *messages,
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                )

                response_text = response.choices[0].message.content

            response_time_ms = (time.time() - start_time) * 1000

            # Extract sources
            sources = [
                {
                    "doc_id": chunk.get("doc_id"),
                    "filename": chunk.get("metadata", {}).get("filename"),
                    "chunk_index": chunk.get("chunk_index"),
                    "similarity": chunk["similarity"],
                }
                for chunk in retrieved_chunks
            ]

            logger.info(f"Query processed in {response_time_ms:.2f}ms")

            return response_text, sources, response_time_ms

        except Exception as e:
            logger.error(f"Error querying LLM: {str(e)}")
            raise

    async def stream_query(
        self,
        query: str,
        retrieved_chunks: List[dict],
        conversation_history: List[dict] = None,
    ) -> AsyncGenerator:
        """
        Stream LLM response token by token.

        Args:
            query: User query
            retrieved_chunks: Retrieved context chunks
            conversation_history: Previous messages

        Yields:
            Response tokens
        """
        try:
            # Format context
            context = self._format_context(retrieved_chunks)
            system_prompt = self._create_system_prompt(context)

            # Build messages
            messages = []
            if conversation_history:
                messages.extend(conversation_history[-4:])
            messages.append({"role": "user", "content": query})

            if not self.client:
                # Mock streaming response
                mock_response = "This is a mock streaming response. Configure OpenAI API key for real streaming."
                for token in mock_response.split():
                    yield token + " "
            else:
                # Stream from OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *messages,
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                    stream=True,
                )

                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Error streaming query: {str(e)}")
            yield f"Error: {str(e)}"


class QueryService:
    """Service orchestrating the full query pipeline."""

    def __init__(self, llm_service: LLMService = None):
        """Initialize query service."""
        self.llm = llm_service or LLMService()

    async def process_query(
        self,
        query: str,
        user_id: int = None,
        session_id: int = None,
        document_ids: List[int] = None,
        conversation_history: List[dict] = None,
        similarity_threshold: float = 0.7,
        max_results: int = 5,
    ) -> dict:
        """
        Process a user query end-to-end.

        Pipeline:
        1. Detect query intent
        2. Retrieve relevant documents
        3. Query LLM with context
        4. Format and return response
        """
        try:
            # Get RAG retriever
            retriever = await get_rag_retriever()

            # Retrieve relevant chunks
            retrieved_chunks = await retriever.retrieve(
                query,
                k=max_results,
                similarity_threshold=similarity_threshold,
            )

            # Query LLM
            response, sources, response_time = await self.llm.query(
                query,
                retrieved_chunks,
                conversation_history,
                stream=False,
            )

            return {
                "query": query,
                "response": response,
                "sources": sources,
                "response_time_ms": response_time,
                "retrieved_count": len(retrieved_chunks),
            }

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

    async def process_query_streaming(
        self,
        query: str,
        user_id: int = None,
        session_id: int = None,
        document_ids: List[int] = None,
        conversation_history: List[dict] = None,
        similarity_threshold: float = 0.7,
        max_results: int = 5,
    ) -> AsyncGenerator:
        """Process query with streaming response."""
        try:
            retriever = await get_rag_retriever()

            # Retrieve chunks
            retrieved_chunks = await retriever.retrieve(
                query,
                k=max_results,
                similarity_threshold=similarity_threshold,
            )

            # Stream response
            async for token in self.llm.stream_query(
                query,
                retrieved_chunks,
                conversation_history,
            ):
                yield token

        except Exception as e:
            logger.error(f"Error in streaming query: {str(e)}")
            yield f"Error: {str(e)}"
