import httpx
from typing import Any, Optional
from app.config import get_config

cfg = get_config()

async def get_google_user_info(code: str, redirect_uri: str) -> dict[str, Any]:
    """Exchange Google OAuth2 code for user profile info."""
    # This expects GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in config
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": cfg.google_client_id,
        "client_secret": cfg.google_client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=data)
        resp.raise_for_status()
        tokens = resp.json()
        
        # Get profile
        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        user_resp = await client.get(user_info_url, headers=headers)
        user_resp.raise_for_status()
        return user_resp.json()

async def get_github_user_info(code: str) -> dict[str, Any]:
    """Exchange GitHub OAuth2 code for user profile info."""
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": cfg.github_client_id,
        "client_secret": cfg.github_client_secret,
        "code": code,
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=data, headers=headers)
        resp.raise_for_status()
        tokens = resp.json()
        
        if "error" in tokens:
            raise ValueError(f"GitHub Auth Error: {tokens.get('error_description')}")
            
        # Get profile
        user_url = "https://api.github.com/user"
        headers = {
            "Authorization": f"token {tokens['access_token']}",
            "Accept": "application/vnd.github.v3+json",
        }
        user_resp = await client.get(user_url, headers=headers)
        user_resp.raise_for_status()
        user_data = user_resp.json()
        
        # GitHub email might be private, need to fetch explicitly if not in user_data
        if not user_data.get("email"):
            emails_resp = await client.get("https://api.github.com/user/emails", headers=headers)
            emails_resp.raise_for_status()
            emails = emails_resp.json()
            primary_email = next((e["email"] for e in emails if e["primary"]), emails[0]["email"] if emails else None)
            user_data["email"] = primary_email
            
        return user_data
