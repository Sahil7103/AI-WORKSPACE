"""
LLM and query service - handles LLM interactions and response generation.
"""

from typing import List, AsyncGenerator, Optional
import asyncio
import re
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

    async def warmup(self, prompt: Optional[str] = None) -> bool:
        """Warm the external LLM endpoint with a lightweight request."""
        if not self.api_url:
            return False

        warmup_prompt = (prompt or settings.llm_warmup_prompt).strip()
        if not warmup_prompt:
            return False

        try:
            await self._request_completion(
                prompt=warmup_prompt,
                system_prompt=(
                    "You are a healthcheck assistant. "
                    "Reply with a very short plain-text response only."
                ),
            )
            logger.info("External LLM warmup completed")
            return True
        except Exception as exc:
            logger.warning(f"External LLM warmup failed: {str(exc)}")
            return False

    async def keepalive_once(self) -> bool:
        """Ping the configured LLM endpoint once to reduce cold starts."""
        return await self.warmup(settings.llm_keepalive_prompt)

    def _format_context(self, retrieved_chunks: List[dict]) -> str:
        """Format retrieved chunks as context."""
        if not retrieved_chunks:
            return (
                "# Retrieved Documents Context\n\n"
                "No relevant internal documents were retrieved for this request.\n"
            )

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

Answer questions based on the provided context whenever relevant. If no useful context is available,
you may still answer simple conversational prompts naturally, but be clear that no internal documents
were used. Cite sources when context is available.

{context}

Response style requirements:
- Write like a polished professional AI product
- Lead with the answer, not filler
- Use short markdown headings only when they improve clarity
- Use bullet points for multiple items, comparisons, steps, recommendations, or grouped facts
- Keep paragraphs tight: usually 1 to 3 sentences
- Highlight the most important phrases using **bold**
- Use `inline code` for commands, file names, API fields, IDs, and technical terms when useful
- Avoid unnecessary preambles, repeated caveats, and robotic wording

Grounding rules:
- Be concise and accurate
- Always mention which document(s) you're referencing when context is available
- If the answer comes from the retrieved context, clearly anchor the answer to that context
- If no useful context is available, say so briefly and then answer as a general assistant if possible
- If uncertain, ask for clarification instead of guessing
- Never make up information not in the context

Preferred answer patterns:
- For direct factual questions: a short answer first, then 2 to 5 bullet points if helpful
- For summaries: begin with a one-line takeaway, then key points
- For how-to questions: use numbered steps
- For recommendations: state the recommendation first, then concise reasoning
- For comparisons: use short labeled bullets

Formatting rules:
- Output clean markdown-style text only
- Do not output JSON, XML, or meta labels like "Final Answer"
- Do not overuse headings
- Do not use tables unless the comparison is genuinely easier to read that way"""

    def _normalize_response_text(self, text: str) -> str:
        """Preserve readable markdown-style spacing from model responses."""
        normalized = (text or "").replace("\r\n", "\n").strip()
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized

    def _chunk_stream_text(self, text: str) -> List[str]:
        """Split text into streaming chunks while preserving whitespace and newlines."""
        pieces = re.findall(r"\n+|[^\S\n]+|[^\s]+", text)
        if not pieces:
            return [text] if text else []

        chunks = []
        buffer = ""
        for piece in pieces:
            if piece.startswith("\n"):
                if buffer:
                    chunks.append(buffer)
                    buffer = ""
                chunks.append(piece)
                continue

            buffer += piece
            if len(buffer) >= 14 or piece.endswith((".", ",", "!", "?", ":", ";")):
                chunks.append(buffer)
                buffer = ""

        if buffer:
            chunks.append(buffer)

        return chunks

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

        last_error = None

        for attempt in range(1, 3):
            try:
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
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status_code = exc.response.status_code if exc.response else None
                if status_code is not None and status_code < 500:
                    raise
            except httpx.RequestError as exc:
                last_error = exc

            if attempt < 2:
                logger.warning(
                    f"External LLM request failed on attempt {attempt}; retrying once."
                )
                await asyncio.sleep(0.6)

        raise last_error or RuntimeError("External LLM request failed")

    def _sanitize_title(
        self,
        title: str,
        fallback_query: str,
        max_words: int = 6,
        max_chars: int = 48,
    ) -> str:
        """Normalize generated titles into short, task-style labels."""
        cleaned = (title or "").strip()
        cleaned = re.sub(r"\*+", "", cleaned)
        cleaned = re.sub(r"^['\"`#*\-\s]+|['\"`#*\-\s]+$", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(
            r"^(task title|title|chat title)\s*:?[\s-]*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = cleaned.strip(" .,:;!?-")

        if not cleaned:
            cleaned = fallback_query or ""

        words = cleaned.split()
        if len(words) > max_words:
            cleaned = " ".join(words[:max_words])

        cleaned = cleaned[:max_chars].rstrip(" ,:;.-")
        if not cleaned:
            cleaned = "New Chat"

        return cleaned[0].upper() + cleaned[1:]

    def _format_title_tokens(self, text: str) -> str:
        """Apply lightweight title casing with common acronym preservation."""
        acronyms = {
            "api": "API",
            "ai": "AI",
            "hr": "HR",
            "sql": "SQL",
            "ui": "UI",
            "ux": "UX",
            "cv": "CV",
            "pdf": "PDF",
            "docx": "DOCX",
            "rag": "RAG",
            "jwt": "JWT",
            "faiss": "FAISS",
            "python": "Python",
            "github": "GitHub",
            "slack": "Slack",
            "gmail": "Gmail",
        }
        words = []
        for word in text.split():
            stripped = word.strip()
            lower = stripped.lower()
            words.append(acronyms.get(lower, stripped.capitalize()))
        return " ".join(words)

    def _heuristic_session_title(self, query: str) -> str:
        """Infer a concise task title from the user's first message."""
        text = (query or "").strip().lower()
        text = re.sub(r"\s+", " ", text)
        for pattern in [
            r"^(hi|hello|hey|please)\s+",
            r"^(can you|could you|would you)\s+",
            r"^(help me)\s+",
            r"^(i want to know|tell me about)\s+",
        ]:
            text = re.sub(pattern, "", text)
        text = text.strip(" .,:;!?-")

        def cleanup_subject(subject: str) -> str:
            subject = re.sub(r"^(the|a|an|my)\s+", "", subject.strip())
            subject = re.sub(r"\b(per week|for employees|for me)\b", "", subject)
            subject = re.sub(r"\b(roles?)\b$", "", subject).strip()
            subject = re.sub(r"\s+", " ", subject).strip(" .,:;!?-")
            return self._format_title_tokens(subject)

        patterns = [
            (r"^(summarize|summarise|summary of)\s+(.*)$", "Summary"),
            (r"^(debug|fix|troubleshoot|resolve)\s+(.*)$", "Debugging"),
            (r"^(explain|describe)\s+(.*)$", ""),
            (r"^(compare)\s+(.*)$", "Comparison"),
            (r"^(draft|write|create)\s+(.*)$", "Draft"),
        ]

        for pattern, suffix in patterns:
            match = re.match(pattern, text)
            if match:
                subject = cleanup_subject(match.group(2))
                if suffix == "Debugging":
                    subject = re.sub(r"\b(error|issue|problem)\b$", "", subject, flags=re.IGNORECASE).strip()
                if not suffix:
                    return subject or "New Chat"
                if suffix == "Comparison":
                    return f"{subject} Comparison" if subject else "Comparison"
                if suffix == "Draft":
                    return f"{subject} Draft" if subject else "Draft"
                return f"{subject} {suffix}".strip() if subject else suffix

        resume_match = re.match(r"^(review|analyze|analyse|assess|evaluate)\s+my\s+(resume|cv)(?:\s+for\s+(.*?))?$", text)
        if resume_match:
            role = cleanup_subject(resume_match.group(3) or "")
            return f"{role} Resume Review".strip() if role else "Resume Review"

        if "resume" in text or "cv" in text:
            return "Resume Review"

        if "policy" in text:
            return f"{cleanup_subject(text)}".strip() or "Policy Question"

        words = [
            word for word in re.findall(r"[a-zA-Z0-9+#.]+", text)
            if word not in {"the", "a", "an", "my", "for", "with", "and", "to", "of", "on", "in"}
        ]
        if not words:
            return "New Chat"

        return self._format_title_tokens(" ".join(words[:5]))

    def _is_valid_generated_title(self, title: str, query: str) -> bool:
        """Reject noisy model-generated titles and use heuristic fallback instead."""
        lowered = title.lower()
        if any(token in lowered for token in ["###", "task title", "section name"]):
            return False
        if " or " in lowered:
            return False
        words = title.split()
        if len(words) < 2 or len(words) > 6:
            return False
        if len(set(word.lower() for word in words)) <= max(1, len(words) // 2):
            return False
        query_words = set(re.findall(r"[a-zA-Z0-9+#.]+", query.lower()))
        title_words = set(re.findall(r"[a-zA-Z0-9+#.]+", title.lower()))
        return bool(title_words) and not title_words.issubset({"new", "chat"}) and len(title_words & query_words) >= 1

    async def generate_session_title(
        self,
        first_query: str,
        conversation_history: Optional[List[dict]] = None,
    ) -> str:
        """Generate a short task-oriented title for a new chat."""
        return self._heuristic_session_title(first_query)

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
                logger.error(f"Error querying external LLM endpoint after retry: {str(exc)}")
                response_text = (
                    "The configured LLM endpoint is currently unavailable. "
                    "Please try again in a moment."
                )

            response_text = self._normalize_response_text(response_text)

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

            for chunk in self._chunk_stream_text(response_text):
                yield chunk

        except Exception as e:
            logger.error(f"Error streaming query: {str(e)}")
            yield f"Error: {str(e)}"


class QueryService:
    """Service orchestrating the full query pipeline."""

    def __init__(self, llm_service: LLMService = None):
        """Initialize query service."""
        self.llm = llm_service or LLMService()

    async def generate_session_title(
        self,
        first_query: str,
        conversation_history: Optional[List[dict]] = None,
    ) -> str:
        """Generate a smart task-based title for a new chat."""
        return await self.llm.generate_session_title(first_query, conversation_history)

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
            retrieved_chunks = []
            try:
                retriever = await get_rag_retriever()
                retrieved_chunks = await retriever.retrieve(
                    query,
                    k=max_results,
                    similarity_threshold=similarity_threshold,
                    allowed_doc_ids=document_ids,
                )
            except Exception as exc:
                logger.warning(
                    f"Retriever unavailable for query '{query}': {str(exc)}. "
                    "Continuing without document context."
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
            retrieved_chunks = []
            try:
                retriever = await get_rag_retriever()
                retrieved_chunks = await retriever.retrieve(
                    query,
                    k=max_results,
                    similarity_threshold=similarity_threshold,
                    allowed_doc_ids=document_ids,
                )
            except Exception as exc:
                logger.warning(
                    f"Retriever unavailable for streaming query '{query}': {str(exc)}. "
                    "Continuing without document context."
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

    async def warmup_dependencies(self) -> None:
        """Warm the LLM endpoint and embedding stack in the background."""
        if settings.llm_warmup_on_startup:
            await self.llm.warmup()

        if settings.warm_embeddings_on_startup:
            try:
                retriever = await get_rag_retriever()
                retriever.initialize_embedding_model()
                logger.info("Embedding model warmup completed")
            except Exception as exc:
                logger.warning(f"Embedding warmup failed: {str(exc)}")
