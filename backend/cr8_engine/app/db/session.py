# session.py
from supabase import create_client, Client
from app.core.config import settings

url = settings.DATABASE_URL
key = settings.SUPABASE_ANON_KEY

supabase: Client = create_client(url, key)

# Dependency to get the supabase client


def get_db():
    return supabase
