"""
LLM Integration API - Phase 4 Implementation
Provides AI-powered narrative assistance, content generation, and story analysis endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field

from ..services.llm_service import llm_service
from ..services.database import get_supabase

router = APIRouter()


# Pydantic models for API requests/responses
class ContentGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Content generation prompt")
    provider: Literal["auto", "openai", "groq", "gemini"] = Field(default="auto", description="LLM provider")
    model: Optional[str] = Field(None, description="Specific model name")
    max_tokens: int = Field(default=1000, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, description="Creativity level (0.0-1.0)")
    system_prompt: Optional[str] = Field(None, description="System prompt for context")


class ContentGenerationResponse(BaseModel):
    success: bool
    content: str
    provider_used: str
    model_used: Optional[str] = None
    token_count: Optional[int] = None


class NarrativeAnalysisRequest(BaseModel):
    content: str = Field(..., description="Content to analyze")
    character_id: Optional[UUID] = Field(None, description="Character ID for knowledge context")
    timeline_timestamp: Optional[int] = Field(None, description="Timeline point for analysis")


class NarrativeAnalysisResponse(BaseModel):
    success: bool
    analysis: Dict[str, Any]
    consistency_score: Optional[float] = None
    issues_found: List[str] = []
    suggestions: List[str] = []


class ShorthandExpansionRequest(BaseModel):
    shorthand: str = Field(..., description="Structured shorthand notation")
    style_guide: Optional[Dict[str, Any]] = Field(None, description="Style preferences")


class ShorthandExpansionResponse(BaseModel):
    success: bool
    expanded_content: Dict[str, str]
    shorthand_input: str


class SceneGenerationRequest(BaseModel):
    scene_id: Optional[UUID] = Field(None, description="Existing scene ID for context")
    character_ids: List[UUID] = Field(default=[], description="Characters involved")
    goal_ids: List[UUID] = Field(default=[], description="Goals to fulfill")
    content_type: Literal["prose", "dialogue", "mixed"] = Field(default="mixed")
    timeline_timestamp: Optional[int] = Field(None, description="Timeline context")
    additional_context: Optional[str] = Field(None, description="Additional context")


class SceneGenerationResponse(BaseModel):
    success: bool
    generated_content: str
    content_type: str
    scene_context: Dict[str, Any]
    character_states: List[Dict[str, Any]]


class NarrativeSuggestionsRequest(BaseModel):
    current_timeline: int = Field(..., description="Current story timeline")
    character_ids: List[UUID] = Field(default=[], description="Active characters")
    available_goal_ids: List[UUID] = Field(default=[], description="Available story goals")
    suggestion_count: int = Field(default=3, description="Number of suggestions")


class NarrativeSuggestionsResponse(BaseModel):
    success: bool
    suggestions: List[Dict[str, Any]]
    story_state: Dict[str, Any]


# =============================
# Core LLM Endpoints
# =============================

@router.post("/generate", response_model=ContentGenerationResponse)
async def generate_content(request: ContentGenerationRequest):
    """Generate content using LLM with multi-provider support."""
    try:
        content = await llm_service.generate_content(
            prompt=request.prompt,
            provider=request.provider,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system_prompt=request.system_prompt
        )
        
        return ContentGenerationResponse(
            success=True,
            content=content,
            provider_used=request.provider,
            model_used=request.model
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")


@router.post("/analyze", response_model=NarrativeAnalysisResponse)
async def analyze_narrative_consistency(request: NarrativeAnalysisRequest):
    """Analyze content for narrative consistency and continuity issues."""
    try:
        db = get_supabase()
        
        # Get character knowledge context if character_id provided
        character_knowledge = {}
        if request.character_id:
            knowledge_response = await db.table("knowledge_snapshots").select(
                "knowledge_state"
            ).eq("character_id", str(request.character_id))
            
            if request.timeline_timestamp:
                knowledge_response = knowledge_response.lte("timeline_timestamp", request.timeline_timestamp)
                
            knowledge_response = knowledge_response.order("timeline_timestamp", desc=True).limit(1).execute()
            
            if knowledge_response.data:
                character_knowledge = knowledge_response.data[0]["knowledge_state"]
        
        # Get timeline context
        timeline_context = {}
        if request.timeline_timestamp:
            timeline_context["timestamp"] = request.timeline_timestamp
            
            # Get recent events around this timeline
            events_response = await db.table("milestones").select(
                "subject_id, verb, object_id, weight, metadata"
            ).lte("created_at", f"timestamp '{request.timeline_timestamp}'").order(
                "created_at", desc=True
            ).limit(10).execute()
            
            timeline_context["recent_events"] = events_response.data or []
        
        # Perform narrative analysis
        analysis_result = await llm_service.analyze_narrative_consistency(
            content=request.content,
            character_knowledge=character_knowledge,
            timeline_context=timeline_context
        )
        
        return NarrativeAnalysisResponse(
            success=True,
            analysis=analysis_result,
            consistency_score=0.8,  # Could be extracted from LLM analysis
            issues_found=[],  # Could be parsed from analysis
            suggestions=[]    # Could be extracted from analysis
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Narrative analysis failed: {str(e)}")


@router.post("/expand-shorthand", response_model=ShorthandExpansionResponse)
async def expand_shorthand_notation(request: ShorthandExpansionRequest):
    """Expand structured shorthand notation into full narrative content."""
    try:
        expansion_result = await llm_service.expand_shorthand_notation(
            shorthand=request.shorthand,
            style_guide=request.style_guide
        )
        
        return ShorthandExpansionResponse(
            success=True,
            expanded_content={"full_content": expansion_result["expanded_content"]},
            shorthand_input=request.shorthand
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shorthand expansion failed: {str(e)}")


# =============================
# Story-Aware LLM Endpoints
# =============================

@router.post("/generate-scene", response_model=SceneGenerationResponse)
async def generate_scene_content(request: SceneGenerationRequest):
    """Generate scene content based on story context and character states."""
    try:
        db = get_supabase()
        
        # Build scene context
        scene_context = {}
        if request.scene_id:
            scene_response = await db.table("scenes").select(
                "title, location_id, timestamp"
            ).eq("id", str(request.scene_id)).execute()
            
            if scene_response.data:
                scene_context = scene_response.data[0]
        
        # Get character states
        character_states = []
        for character_id in request.character_ids:
            knowledge_response = await db.table("knowledge_snapshots").select(
                "character_id, knowledge_state, timeline_timestamp"
            ).eq("character_id", str(character_id))
            
            if request.timeline_timestamp:
                knowledge_response = knowledge_response.lte(
                    "timeline_timestamp", request.timeline_timestamp
                )
                
            knowledge_response = knowledge_response.order(
                "timeline_timestamp", desc=True
            ).limit(1).execute()
            
            if knowledge_response.data:
                character_states.append(knowledge_response.data[0])
        
        # Get goal fulfillment context
        goal_fulfillment = None
        if request.goal_ids:
            goals_response = await db.table("story_goals").select(
                "id, description, target_entities, success_criteria"
            ).in_("id", [str(gid) for gid in request.goal_ids]).execute()
            
            goal_fulfillment = {
                "goals": goals_response.data or [],
                "timeline": request.timeline_timestamp
            }
        
        # Add additional context
        if request.additional_context:
            scene_context["additional_context"] = request.additional_context
        
        # Generate scene content
        generation_result = await llm_service.generate_scene_content(
            scene_context=scene_context,
            character_states=character_states,
            goal_fulfillment=goal_fulfillment,
            content_type=request.content_type
        )
        
        return SceneGenerationResponse(
            success=True,
            generated_content=generation_result["generated_content"],
            content_type=request.content_type,
            scene_context=scene_context,
            character_states=character_states
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scene generation failed: {str(e)}")


@router.post("/suggest-continuations", response_model=NarrativeSuggestionsResponse)
async def suggest_narrative_continuations(request: NarrativeSuggestionsRequest):
    """Suggest possible narrative continuations based on current story state."""
    try:
        db = get_supabase()
        
        # Build current story state
        story_state = {
            "timeline": request.current_timeline,
            "active_characters": request.character_ids
        }
        
        # Get recent milestones to understand story progression
        milestones_response = await db.table("milestones").select(
            "subject_id, verb, object_id, weight, metadata, created_at"
        ).lte("created_at", f"timestamp '{request.current_timeline}'").order(
            "created_at", desc=True
        ).limit(20).execute()
        
        story_state["recent_milestones"] = milestones_response.data or []
        
        # Get character arcs
        character_arcs = []
        for character_id in request.character_ids:
            arc_response = await db.table("knowledge_snapshots").select(
                "character_id, knowledge_state, timeline_timestamp"
            ).eq("character_id", str(character_id)).order(
                "timeline_timestamp", desc=True
            ).limit(5).execute()
            
            if arc_response.data:
                character_arcs.append({
                    "character_id": character_id,
                    "knowledge_progression": arc_response.data
                })
        
        # Get available goals
        available_goals = []
        if request.available_goal_ids:
            goals_response = await db.table("story_goals").select(
                "id, description, target_entities, success_criteria, priority"
            ).in_("id", [str(gid) for gid in request.available_goal_ids]).execute()
            
            available_goals = goals_response.data or []
        
        # Generate narrative suggestions
        suggestions_result = await llm_service.suggest_narrative_continuations(
            current_story_state=story_state,
            character_arcs=character_arcs,
            available_goals=available_goals,
            limit=request.suggestion_count
        )
        
        return NarrativeSuggestionsResponse(
            success=True,
            suggestions=[{"suggestion": suggestions_result["suggestions"]}],
            story_state=story_state
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Narrative suggestions failed: {str(e)}")


# =============================
# Utility and Status Endpoints
# =============================

@router.get("/providers")
async def get_llm_providers():
    """Get status and capabilities of all LLM providers."""
    try:
        status = await llm_service.get_provider_status()
        
        available_count = sum(1 for info in status.values() if info["available"])
        
        return {
            "success": True,
            "providers": status,
            "available_providers": available_count,
            "total_providers": len(status)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provider status check failed: {str(e)}")


@router.post("/test-generation")
async def test_content_generation(
    prompt: str = "Write a brief story about a dragon.",
    provider: Literal["auto", "openai", "groq", "gemini"] = "auto"
):
    """Test endpoint for basic content generation."""
    try:
        content = await llm_service.generate_content(
            prompt=prompt,
            provider=provider,
            max_tokens=200,
            temperature=0.7
        )
        
        return {
            "success": True,
            "prompt": prompt,
            "generated_content": content,
            "provider": provider,
            "test_status": "passed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


@router.get("/health")
async def llm_health_check():
    """Health check for LLM service and providers."""
    try:
        status = await llm_service.get_provider_status()
        
        available_providers = [
            provider for provider, info in status.items() 
            if info["available"]
        ]
        
        health_status = "healthy" if available_providers else "degraded"
        
        return {
            "success": True,
            "status": health_status,
            "available_providers": available_providers,
            "provider_details": status,
            "capabilities": [
                "content_generation",
                "narrative_analysis", 
                "scene_generation",
                "shorthand_expansion",
                "narrative_suggestions"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "available_providers": [],
            "capabilities": []
        }