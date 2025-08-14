#!/usr/bin/env python3
"""Test script for LLM API endpoints."""

import asyncio
import sys
import json

async def test_llm_api():
    """Test LLM API functionality."""
    try:
        print("Testing LLM API endpoints...")
        
        # Test imports
        from app.api.llm import router
        print("✅ LLM API import successful")
        
        from app.services.llm_service import llm_service
        print("✅ LLM service available")
        
        # Test provider status
        status = await llm_service.get_provider_status()
        available_providers = [p for p, info in status.items() if info['available']]
        print(f"✅ Available providers: {', '.join(available_providers)}")
        
        # Test basic content generation
        if available_providers:
            print(f"\n🧪 Testing content generation...")
            
            content = await llm_service.generate_content(
                prompt="Describe a mystical library in 2 sentences.",
                provider=available_providers[0],
                max_tokens=50,
                temperature=0.7
            )
            
            print(f"✅ Generated content: {content[:80]}...")
            
            # Test narrative analysis
            print(f"\n🔍 Testing narrative analysis...")
            
            analysis = await llm_service.analyze_narrative_consistency(
                content="The wizard opened the ancient tome. He found a spell for invisibility.",
                character_knowledge={"name": "Gandalf", "abilities": ["magic", "wisdom"]},
                timeline_context={"location": "library", "time": "midnight"}
            )
            
            print(f"✅ Analysis completed: {len(analysis['analysis'])} characters analyzed")
            
            # Test shorthand expansion
            print(f"\n📝 Testing shorthand expansion...")
            
            expansion = await llm_service.expand_shorthand_notation(
                shorthand="[Hero enters] -> [Sees treasure] -> [Dragon appears]",
                style_guide={"tone": "dramatic", "length": "brief"}
            )
            
            print(f"✅ Shorthand expanded: {len(expansion['expanded_content'])} characters")
            
        print(f"\n🎉 LLM API Phase 4 Ready!")
        print(f"📊 Available endpoints:")
        print(f"  • POST /generate - Content generation")
        print(f"  • POST /analyze - Narrative consistency analysis")
        print(f"  • POST /expand-shorthand - Shorthand notation expansion")
        print(f"  • POST /generate-scene - Scene content generation")
        print(f"  • POST /suggest-continuations - Narrative suggestions")
        print(f"  • GET /providers - Provider status")
        print(f"  • GET /health - Health check")
        print(f"  • POST /test-generation - Test endpoint")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm_api())
    sys.exit(0 if success else 1)