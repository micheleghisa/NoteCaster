import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


def _client():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])


def sign_up(email: str, password: str):
    return _client().auth.sign_up({"email": email, "password": password})


def sign_in(email: str, password: str):
    return _client().auth.sign_in_with_password({"email": email, "password": password})


def refresh_session(refresh_token: str):
    return _client().auth.refresh_session(refresh_token)
