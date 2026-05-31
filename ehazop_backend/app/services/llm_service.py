"""LLM service with provider abstraction for Gemini and OpenAI."""

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.hazard import LLMSuggestion, Deviation, Node
from app.models.user import Study

settings = get_settings()


class LLMProvider:
    """Abstract base class for LLM providers."""

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        raise NotImplementedError

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text."""
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.LLM_MODEL

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Gemini API."""
        try:
            from google.genai import client as genai_client
            
            genai = genai_client.Client(api_key=self.api_key)
            
            response = genai.models.generate_content(
                model=self.model,
                contents=prompt,
                config=kwargs.get("config", {}),
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini generation failed: {e}")

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings using Gemini."""
        try:
            from google.genai import client as genai_client
            
            genai = genai_client.Client(api_key=self.api_key)
            
            result = genai.models.embed_content(
                model=settings.LLM_EMBEDDING_MODEL,
                contents=text,
            )
            return result.embedding
        except Exception as e:
            raise RuntimeError(f"Gemini embedding failed: {e}")


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.LLM_MODEL

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI API."""
        # Implementation would use openai library
        raise NotImplementedError("OpenAI provider not yet implemented")

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings using OpenAI."""
        # Implementation would use openai library
        raise NotImplementedError("OpenAI provider not yet implemented")


class LLMService:
    """LLM service with provider abstraction."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._provider = None

    @property
    def provider(self) -> LLMProvider:
        """Get the configured LLM provider."""
        if self._provider is None:
            if settings.LLM_PROVIDER == "gemini":
                self._provider = GeminiProvider()
            elif settings.LLM_PROVIDER == "openai":
                self._provider = OpenAIProvider()
            else:
                raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")
        return self._provider

    async def generate_suggestions(
        self,
        deviation_id: str,
        suggestion_type: str,  # cause, consequence, safeguard
        context: str | None = None,
    ) -> list[dict[str, Any]]:
        """Generate LLM suggestions for a deviation."""
        # Get deviation with context
        result = await self.db.execute(
            select(Deviation).where(Deviation.id == deviation_id)
        )
        deviation = result.scalar_one_or_none()
        if not deviation:
            raise ValueError(f"Deviation {deviation_id} not found")

        # Get node info
        node_result = await self.db.execute(
            select(Node).where(Node.id == deviation.node_id)
        )
        node = node_result.scalar_one_or_none()

        # Get study info
        study_result = await self.db.execute(
            select(Study).where(Study.id == node.study_id)
        )
        study = study_result.scalar_one_or_none()

        # Build prompt with context
        prompt = self._build_suggestion_prompt(
            study_name=study.name if study else "Unknown",
            study_type=study.study_type if study else "Unknown",
            node_name=node.name if node else "Unknown",
            node_reference=node.reference if node else "Unknown",
            node_design_intent=node.design_intent if node else "None provided",
            deviation_text=deviation.deviation_text or "Not specified",
            suggestion_type=suggestion_type,
            context=context,
        )

        # Generate response
        response_text = await self.provider.generate(prompt)

        # Parse and return suggestions
        return self._parse_suggestions(response_text, suggestion_type)

    def _build_suggestion_prompt(
        self,
        study_name: str,
        study_type: str,
        node_name: str,
        node_reference: str,
        node_design_intent: str,
        deviation_text: str,
        suggestion_type: str,
        context: str | None,
    ) -> str:
        """Build a prompt for generating suggestions."""
        type_prompts = {
            "cause": "Identify specific potential causes that could lead to this deviation. Consider equipment failure, human error, procedural failures, and external factors.",
            "consequence": "Describe the potential consequences of this deviation. Consider safety impacts, operational impacts, environmental impacts, and asset damage.",
            "safeguard": "Suggest existing safeguards or protective measures that may already be in place to prevent or mitigate this deviation.",
        }

        prompt = f"""You are a safety engineering expert helping with a {study_type} study.
Study: {study_name}
Node: {node_reference} - {node_name}
Design Intent: {node_design_intent}
Deviation: {deviation_text}

Generate 3 potential {suggestion_type}s based on this context.
{type_prompts.get(suggestion_type, '')}

Return your response as a JSON array of objects with the following structure:
[{{"content": "description of {suggestion_type}", "confidence": 0.0-1.0}}]

Each {suggestion_type} should be concise (1-2 sentences) and specific to this scenario.
If context is provided, reference it in your suggestions.
"""
        return prompt

    def _parse_suggestions(
        self,
        response_text: str,
        suggestion_type: str,
    ) -> list[dict[str, Any]]:
        """Parse LLM response into structured suggestions."""
        try:
            # Try to parse as JSON
            suggestions = json.loads(response_text)
            if isinstance(suggestions, list):
                return [
                    {
                        "content": s.get("content", ""),
                        "confidence": s.get("confidence", 0.5),
                        "suggestion_type": suggestion_type,
                        "citations": [],
                    }
                    for s in suggestions
                    if s.get("content")
                ]
        except json.JSONDecodeError:
            # Fallback: parse as plain text
            lines = response_text.strip().split("\n")
            return [
                {
                    "content": line.strip(),
                    "confidence": 0.5,
                    "suggestion_type": suggestion_type,
                    "citations": [],
                }
                for line in lines
                if line.strip()
            ]

        return []

    async def create_suggestion(
        self,
        deviation_id: str,
        suggestion_type: str,
        content: str,
        confidence: float | None = None,
        citations: list[dict] | None = None,
    ) -> LLMSuggestion:
        """Create an LLM suggestion record."""
        suggestion = LLMSuggestion(
            deviation_id=deviation_id,
            suggestion_type=suggestion_type,
            content=content,
            confidence=confidence,
            citations=citations or [],
            status="pending",
        )
        self.db.add(suggestion)
        await self.db.flush()
        await self.db.refresh(suggestion)
        return suggestion

    async def generate_and_store_suggestions(
        self,
        deviation_id: str,
        suggestion_type: str,
        context: str | None = None,
    ) -> list[LLMSuggestion]:
        """Generate suggestions and store them as pending records."""
        suggestions = await self.generate_suggestions(
            deviation_id, suggestion_type, context
        )

        created_suggestions = []
        for suggestion_data in suggestions:
            suggestion = await self.create_suggestion(
                deviation_id=deviation_id,
                suggestion_type=suggestion_type,
                content=suggestion_data["content"],
                confidence=suggestion_data.get("confidence"),
                citations=suggestion_data.get("citations"),
            )
            created_suggestions.append(suggestion)

        return created_suggestions

    async def get_pending_suggestions(
        self,
        deviation_id: str,
    ) -> list[LLMSuggestion]:
        """Get all pending suggestions for a deviation."""
        result = await self.db.execute(
            select(LLMSuggestion).where(
                LLMSuggestion.deviation_id == deviation_id,
                LLMSuggestion.status == "pending",
            )
        )
        return list(result.scalars().all())