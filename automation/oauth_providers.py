"""Google/Meta OAuth provider adapters with fixed endpoints and PKCE for Google."""
from __future__ import annotations

import os
from urllib.parse import urlencode

import httpx

CONFIG = {
    "google_docs": ("google", "https://accounts.google.com/o/oauth2/v2/auth",
                    "https://oauth2.googleapis.com/token",
                    "https://www.googleapis.com/auth/documents"),
    "google_sheets": ("google", "https://accounts.google.com/o/oauth2/v2/auth",
                      "https://oauth2.googleapis.com/token",
                      "https://www.googleapis.com/auth/spreadsheets"),
    "facebook_page": ("meta", "https://www.facebook.com/v22.0/dialog/oauth",
                      "https://graph.facebook.com/v22.0/oauth/access_token",
                      "pages_show_list,pages_read_engagement"),
    "instagram": ("meta", "https://www.facebook.com/v22.0/dialog/oauth",
                  "https://graph.facebook.com/v22.0/oauth/access_token",
                  "instagram_basic,pages_show_list"),
}


def settings(provider: str):
    if provider not in CONFIG:
        raise ValueError("Unsupported OAuth provider")
    family, auth_url, token_url, scope = CONFIG[provider]
    prefix = "OMNI_GOOGLE" if family == "google" else "OMNI_META"
    client_id = os.getenv(prefix + "_CLIENT_ID", "")
    client_secret = os.getenv(prefix + "_CLIENT_SECRET", "")
    redirect = os.getenv("OMNI_OAUTH_REDIRECT_URI", "")
    if not client_id or not client_secret or not redirect.startswith("https://"):
        raise RuntimeError("OAuth application configuration is incomplete")
    return client_id, client_secret, redirect, auth_url, token_url, scope, family


def authorization_url(provider: str, state: str, challenge: str) -> str:
    client_id, _, redirect, auth_url, _, scope, family = settings(provider)
    params = {"client_id": client_id, "redirect_uri": redirect,
              "response_type": "code", "state": state, "scope": scope}
    if family == "google":
        params.update({"access_type": "offline", "prompt": "consent",
                       "code_challenge": challenge, "code_challenge_method": "S256"})
    return auth_url + "?" + urlencode(params)


def exchange_code(provider: str, code: str, verifier: str) -> dict:
    client_id, client_secret, redirect, _, token_url, _, family = settings(provider)
    data = {"client_id": client_id, "client_secret": client_secret,
            "redirect_uri": redirect, "code": code, "grant_type": "authorization_code"}
    if family == "google":
        data["code_verifier"] = verifier
    with httpx.Client(timeout=12, follow_redirects=False) as client:
        response = client.post(token_url, data=data)
        response.raise_for_status()
        result = response.json()
    if not isinstance(result, dict) or not isinstance(result.get("access_token"), str):
        raise TypeError("OAuth provider returned no access token")
    return result
