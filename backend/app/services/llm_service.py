"""
LLM and query service - handles LLM interactions and response generation.
"""

from typing import List, AsyncGenerator
import time

import httpx

from app.core.config import settings
from app.rag.retriever import get_rag_retriever
from app.utils.logger import logger


class LLMService:
    """Service for LLM interactions."""

    def __init__(
        self,
        api_url: str = None,
        api_token: str = None,
        model: str = None,
        timeout: float = None,
        max_tokens: int = None,
    ):
        """Initialize LLM service."""
        self.api_url = (api_url or settings.llm_api_url).strip()
        self.api_token = (api_token or settings.llm_api_token).strip()
        self.model = model or settings.llm_model_label
        self.timeout = timeout or settings.llm_timeout_seconds
        self.max_tokens = max_tokens or settings.llm_max_tokens
        self.client = httpx.AsyncClient(timeout=self.timeout)

        if self.api_url:
            logger.info(
                f"Initialized external LLM service with model: {self.model} via {self.api_url}"
            )
        else:
            logger.warning("No external LLM API configured. Using fallback responses.")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

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

    def _format_conversation_history(self, conversation_history: List[dict] = None) -> str:
        """Format prior conversation turns for single-prompt APIs."""
        if not conversation_history:
            return ""

        lines = []
        for message in conversation_history[-4:]:
            role = "Assistant" if message.get("role") == "assistant" else "User"
            content = (message.get("content") or "").strip()
            if content:
                lines.append(f"{role}: {content}")

        if not lines:
            return ""

        return "Conversation History:\n" + "\n".join(lines) + "\n\n"

    async def _request_completion(self, prompt: str, system_prompt: str) -> str:
        """Call the configured external LLM endpoint."""
        if not self.api_url:
            return (
                "No external LLM endpoint is configured. Set LLM_API_URL to your model "
                "service and try again."
            )

        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        response = await self.client.post(
            self.api_url,
            json={
                "prompt": prompt,
                "system_prompt": system_prompt,
                "max_tokens": self.max_tokens,
            },
            headers=headers,
        )
        response.raise_for_status()

        payload = response.json()
        answer = (
            payload.get("answer")
            or payload.get("response")
            or payload.get("text")
            or ""
        ).strip()

        if not answer:
            raise ValueError("External LLM endpoint returned an empty response payload")

        return answer

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
            start_time = time.time()

            # Format context
            context = self._format_context(retrieved_chunks)
            system_prompt = self._create_system_prompt(context)
            prompt = (
                f"{self._format_conversation_history(conversation_history)}"
                f"Current User Question:\n{query}"
            )

            try:
                response_text = await self._request_completion(prompt, system_prompt)
            except Exception as exc:
                logger.error(f"Error querying external LLM endpoint: {str(exc)}")
                response_text = (
                    "The configured LLM endpoint is currently unavailable. "
                    "Please try again in a moment."
                )

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
            response_text, _, _ = await self.query(
                query=query,
                retrieved_chunks=retrieved_chunks,
                conversation_history=conversation_history,
                stream=False,
            )

            for token in response_text.split():
                yield token + " "

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
