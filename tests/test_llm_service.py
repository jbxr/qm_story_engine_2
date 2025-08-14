#!/usr/bin/env python3
"""Test script for LLM service functionality."""

import asyncio
import sys
import os

async def test_llm_service():
    """Test LLM service initialization and basic functionality."""
    try:
        print("Testing LLM service...")
        
        # Test import
        from app.services.llm_service import llm_service
        print("✅ LLM service import successful")
        
        # Test provider status
        status = await llm_service.get_provider_status()
        print(f"✅ Provider status retrieved")
        
        available_providers = [
            provider for provider, info in status.items() 
            if info['available']
        ]
        
        print(f"\n🔌 Available LLM Providers: {', '.join(available_providers)}")
        
        for provider, info in status.items():
            if info['available']:
                print(f"  • {provider.upper()}: {', '.join(info['capabilities'])}")
                print(f"    Models: {', '.join(info['models'][:2])}...")
        
        # Test basic content generation if providers available
        if available_providers:
            print(f"\n🧪 Testing content generation with {available_providers[0]}...")
            
            test_prompt = "Write a brief description of a mysterious forest clearing."
            result = await llm_service.generate_content(
                prompt=test_prompt,
                provider=available_providers[0],
                max_tokens=100,
                temperature=0.7
            )
            
            print(f"✅ Content generation successful!")
            print(f"Generated: {result[:100]}...")
        else:
            print("⚠️  No providers available for content generation test")
        
        print(f"\n🎉 LLM Service Ready for Phase 4!")
        return True
        
    except Exception as e:
        print(f"❌ LLM service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm_service())
    sys.exit(0 if success else 1)