"""LLM integration service for narrative assistance and content generation.

Provides AI-powered story writing assistance using OpenAI, Groq, and Gemini APIs
with intelligent provider selection based on task type and performance characteristics.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union, Literal
from openai import AsyncOpenAI
import google.generativeai as genai
from uuid import UUID

logger = logging.getLogger(__name__)


class LLMService:
    """Service for AI-powered narrative assistance and content generation."""

    def __init__(self):
        """Initialize LLM service with multiple providers."""
        self.openai_client = None
        self.groq_client = None
        self.gemini_model = None
        self._initialized = False
        
    def _ensure_initialized(self):
        """Lazy initialization of LLM clients."""
        if self._initialized:
            return
            
        try:
            from app.config import get_settings
            settings = get_settings()
            
            # Initialize OpenAI client
            if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
                self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            # Initialize Groq client (OpenAI-compatible)
            if hasattr(settings, 'groq_api_key') and settings.groq_api_key:
                try:
                    self.groq_client = AsyncOpenAI(
                        api_key=settings.groq_api_key,
                        base_url="https://api.groq.com/openai/v1"
                    )
                except Exception as e:
                    logger.warning(f"Failed to initialize Groq client: {e}")
            
            # Initialize Gemini client
            if hasattr(settings, 'gemini_api_key') and settings.gemini_api_key:
                try:
                    genai.configure(api_key=settings.gemini_api_key)
                    self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                except Exception as e:
                    logger.warning(f"Failed to initialize Gemini client: {e}")
                    
            self._initialized = True
            logger.info("LLM service initialized with available providers")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            self._initialized = True

    async def generate_content(
        self,
        prompt: str,
        provider: Literal["auto", "openai", "groq", "gemini"] = "auto",
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate content using specified LLM provider.
        
        Args:
            prompt: The content generation prompt
            provider: LLM provider to use ("auto" selects best available)
            model: Specific model to use (provider-dependent)
            max_tokens: Maximum tokens to generate
            temperature: Creativity level (0.0-1.0)
            system_prompt: Optional system prompt for context
            
        Returns:
            Generated content as string
        """
        self._ensure_initialized()
        
        # Auto-select provider if not specified
        if provider == "auto":
            provider = self._select_best_provider("generation")
            
        try:
            if provider == "openai" and self.openai_client:
                return await self._generate_openai(prompt, model or "gpt-4o-mini", max_tokens, temperature, system_prompt)
            elif provider == "groq" and self.groq_client:
                return await self._generate_groq(prompt, model or "llama-3.1-8b-instant", max_tokens, temperature, system_prompt)
            elif provider == "gemini" and self.gemini_model:
                return await self._generate_gemini(prompt, max_tokens, temperature, system_prompt)
            else:
                raise ValueError(f"Provider {provider} not available or not configured")
                
        except Exception as e:
            logger.error(f"Content generation failed with {provider}: {e}")
            
            # Fallback to other providers
            for fallback_provider in ["openai", "groq", "gemini"]:
                if fallback_provider != provider:
                    try:
                        return await self.generate_content(
                            prompt, fallback_provider, None, max_tokens, temperature, system_prompt
                        )
                    except Exception:
                        continue
                        
            raise Exception("All LLM providers failed")

    async def _generate_openai(self, prompt: str, model: str, max_tokens: int, temperature: float, system_prompt: Optional[str]) -> str:
        """Generate content using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content

    async def _generate_groq(self, prompt: str, model: str, max_tokens: int, temperature: float, system_prompt: Optional[str]) -> str:
        """Generate content using Groq."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.groq_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content

    async def _generate_gemini(self, prompt: str, max_tokens: int, temperature: float, system_prompt: Optional[str]) -> str:
        """Generate content using Gemini."""
        # Combine system prompt and user prompt for Gemini
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature
        )
        
        response = await asyncio.to_thread(
            self.gemini_model.generate_content,
            full_prompt,
            generation_config=generation_config
        )
        
        return response.text

    def _select_best_provider(self, task_type: str) -> str:
        """Select the best available provider for a given task type."""
        # Provider preferences by task type
        preferences = {
            "generation": ["groq", "openai", "gemini"],  # Groq for speed
            "analysis": ["openai", "gemini", "groq"],    # OpenAI for quality
            "creative": ["gemini", "openai", "groq"],    # Gemini for creativity
            "technical": ["openai", "groq", "gemini"]    # OpenAI for precision
        }
        
        task_preferences = preferences.get(task_type, ["openai", "groq", "gemini"])
        
        for provider in task_preferences:
            if (provider == "openai" and self.openai_client or
                provider == "groq" and self.groq_client or
                provider == "gemini" and self.gemini_model):
                return provider
                
        raise ValueError("No LLM providers available")

    async def analyze_narrative_consistency(
        self,
        content: str,
        character_knowledge: Dict[str, Any],
        timeline_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content for narrative consistency issues."""
        system_prompt = """You are a narrative consistency analyzer. Review the provided content for:
1. Character voice consistency
2. Timeline continuity issues  
3. Knowledge state violations
4. Plot inconsistencies

Return your analysis as a structured assessment."""

        context = f"""
Character Knowledge: {character_knowledge}
Timeline Context: {timeline_context}

Content to Analyze:
{content}
"""

        analysis = await self.generate_content(
            prompt=context,
            provider="auto",
            system_prompt=system_prompt,
            temperature=0.3  # Lower temperature for analytical tasks
        )
        
        return {
            "content": content,
            "analysis": analysis,
            "character_knowledge": character_knowledge,
            "timeline_context": timeline_context
        }

    async def expand_shorthand_notation(
        self,
        shorthand: str,
        style_guide: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Expand structured shorthand notation into full prose and dialogue."""
        system_prompt = """You are a narrative expansion specialist. Convert structured shorthand notation into full narrative prose and dialogue.

Follow these guidelines:
- Expand action notes into descriptive prose
- Convert dialogue markers into natural conversation
- Maintain the intended pacing and tone
- Preserve all story beats and character moments

Return both prose and dialogue versions."""

        style_context = ""
        if style_guide:
            style_context = f"\nStyle Guide: {style_guide}"

        prompt = f"""
Shorthand Notation:
{shorthand}
{style_context}

Please expand this into:
1. Full prose version
2. Dialogue-focused version
"""

        expansion = await self.generate_content(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6,
            provider="auto"
        )
        
        return {
            "shorthand_input": shorthand,
            "expanded_content": expansion,
            "style_guide": style_guide
        }

    async def generate_scene_content(
        self,
        scene_context: Dict[str, Any],
        character_states: List[Dict[str, Any]],
        goal_fulfillment: Optional[Dict[str, Any]] = None,
        content_type: Literal["prose", "dialogue", "mixed"] = "mixed"
    ) -> Dict[str, Any]:
        """Generate scene content based on context and character states."""
        system_prompt = f"""You are a narrative generation specialist. Create {content_type} content for a story scene.

Guidelines:
- Maintain character voice consistency based on provided states
- Advance the narrative toward specified goals
- Create engaging, contextually appropriate content
- Respect established timeline and world-building elements"""

        context_info = f"""
Scene Context: {scene_context}
Character States: {character_states}
Goal Fulfillment: {goal_fulfillment or 'General narrative progression'}

Generate {content_type} content for this scene.
"""

        content = await self.generate_content(
            prompt=context_info,
            system_prompt=system_prompt,
            temperature=0.7,
            provider="auto"
        )
        
        return {
            "generated_content": content,
            "content_type": content_type,
            "scene_context": scene_context,
            "character_states": character_states,
            "goal_fulfillment": goal_fulfillment
        }

    async def suggest_narrative_continuations(
        self,
        current_story_state: Dict[str, Any],
        character_arcs: List[Dict[str, Any]],
        available_goals: List[Dict[str, Any]],
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Suggest possible narrative continuations based on current state."""
        system_prompt = """You are a narrative planning specialist. Based on the current story state, character arcs, and available goals, suggest compelling narrative continuations.

Focus on:
- Character development opportunities
- Goal progression paths
- Dramatic potential
- Story pacing

Provide multiple distinct options with different dramatic focuses."""

        context = f"""
Current Story State: {current_story_state}
Character Arcs: {character_arcs}
Available Goals: {available_goals}

Suggest {limit} compelling narrative continuation options.
"""

        suggestions = await self.generate_content(
            prompt=context,
            system_prompt=system_prompt,
            temperature=0.8,  # Higher temperature for creative suggestions
            provider="auto"
        )
        
        return {
            "suggestions": suggestions,
            "story_state": current_story_state,
            "character_arcs": character_arcs,
            "available_goals": available_goals,
            "suggestion_count": limit
        }

    async def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all LLM providers."""
        self._ensure_initialized()
        
        status = {
            "openai": {
                "available": self.openai_client is not None,
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"] if self.openai_client else [],
                "capabilities": ["generation", "analysis", "embeddings"] if self.openai_client else []
            },
            "groq": {
                "available": self.groq_client is not None,
                "models": ["llama-3.1-8b-instant", "mixtral-8x7b-32768"] if self.groq_client else [],
                "capabilities": ["generation", "fast_inference"] if self.groq_client else []
            },
            "gemini": {
                "available": self.gemini_model is not None,
                "models": ["gemini-1.5-flash", "gemini-1.5-pro"] if self.gemini_model else [],
                "capabilities": ["generation", "multimodal", "creative"] if self.gemini_model else []
            }
        }
        
        return status


# Global LLM service instance
llm_service = LLMService()