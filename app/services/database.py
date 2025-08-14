"""
Database connection using proven Supabase patterns
Based on successful test_minimal_api.py implementation
"""
import os
from supabase import create_client, Client

def get_db() -> Client:
    """Get Supabase client using proven pattern from test_minimal_api.py"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
    
    return create_client(url, key)

# Global supabase client instance (lazy initialization)
_supabase_client = None

def get_supabase() -> Client:
    """Get or create the global supabase client."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_db()
    return _supabase_client

# For backward compatibility
supabase = None