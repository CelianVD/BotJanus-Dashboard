"""
Authentification OAuth2 Vikidia (extension MediaWiki OAuth, flow central.vikidia.org)
+ vérification "autopatrol" multi-wikis pour l'accès Collaborateur automatique.

Remplace l'ancien système GitHub OAuth du dashboard.
"""
from __future__ import annotations

import base64
import hashlib
import os
import secrets

import requests

WIKI_OAUTH_CLIENT_ID = os.environ.get("WIKI_OAUTH_CLIENT_ID")
WIKI_OAUTH_CLIENT_SECRET = os.environ.get("WIKI_OAUTH_CLIENT_SECRET")
WIKI_OAUTH_CALLBACK = os.environ.get("WIKI_OAUTH_CALLBACK")
# Base REST du wiki central utilisé pour l'OAuth2 (ex: https://central.vikidia.org/w/rest.php)
WIKI_OAUTH_REST_BASE = (os.environ.get("WIKI_OAUTH_REST_BASE") or "").rstrip("/")
WIKI_USER_AGENT = os.environ.get("WIKI_USER_AGENT", "BotJanus/1.0")

_MISSING = [name for name, val in [
    ("WIKI_OAUTH_CLIENT_ID", WIKI_OAUTH_CLIENT_ID),
    ("WIKI_OAUTH_CLIENT_SECRET", WIKI_OAUTH_CLIENT_SECRET),
    ("WIKI_OAUTH_CALLBACK", WIKI_OAUTH_CALLBACK),
    ("WIKI_OAUTH_REST_BASE", WIKI_OAUTH_REST_BASE),
] if not val]
if _MISSING:
    raise RuntimeError(
        "wiki_auth : variable(s) d'environnement manquante(s) ou vide(s) : "
        + ", ".join(_MISSING)
        + ". Vérifie le fichier .env chargé par le process Flask (attention : sur "
        "PythonAnywhere, il faut recharger l'appli web après toute modif du .env). "
        "WIKI_OAUTH_REST_BASE doit être une URL absolue, ex : "
        "https://central.vikidia.org/w/rest.php (sans slash final)."
    )
if not WIKI_OAUTH_REST_BASE.startswith(("http://", "https://")):
    raise RuntimeError(
        f"wiki_auth : WIKI_OAUTH_REST_BASE='{WIKI_OAUTH_REST_BASE}' n'est pas une URL absolue "
        "(il manque http:// ou https://) — l'authorize_url générée serait relative au domaine "
        "du dashboard au lieu de pointer vers central.vikidia.org."
    )

AUTHORIZE_URL = f"{WIKI_OAUTH_REST_BASE}/oauth2/authorize"
TOKEN_URL = f"{WIKI_OAUTH_REST_BASE}/oauth2/access_token"
PROFILE_URL = f"{WIKI_OAUTH_REST_BASE}/oauth2/resource/profile"

# Versions linguistiques de Vikidia sur lesquelles le statut "autopatrolled"
# (ou supérieur) donne un accès Collaborateur automatique.
# Liste complète des 14 versions linguistiques actives de Vikidia (voir langs.txt).
# NB : la liste précédente contenait "uk" (Ukrainien), qui ne correspond à aucune
# version de Vikidia connue, et omettait "it", "eu", "ru", "el", "oc" — corrigé ici.
AUTOPATROL_WIKI_CODES = ["fr", "en", "es", "it", "de", "ca", "eu", "ru",
                          "scn", "el", "hy", "pt", "oc", "ar"]

# Groupes wiki considérés comme suffisants (autopatrolled ou tout groupe qui l'implique).
QUALIFYING_GROUPS = {"autopatrolled", "patroller", "sysop", "bureaucrat"}

TIMEOUT = 10


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def generate_pkce_pair() -> tuple[str, str]:
    """Renvoie (code_verifier, code_challenge) pour le flow OAuth2 PKCE (S256)."""
    verifier = _b64url(secrets.token_bytes(40))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def build_authorize_url(state: str, code_challenge: str) -> str:
    from urllib.parse import urlencode

    params = {
        "response_type": "code",
        "client_id": WIKI_OAUTH_CLIENT_ID,
        "redirect_uri": WIKI_OAUTH_CALLBACK,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str, code_verifier: str) -> dict | None:
    """Échange le code d'autorisation contre un access_token. None en cas d'échec."""
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": WIKI_OAUTH_CALLBACK,
        "client_id": WIKI_OAUTH_CLIENT_ID,
        "client_secret": WIKI_OAUTH_CLIENT_SECRET,
        "code_verifier": code_verifier,
    }
    try:
        r = requests.post(
            TOKEN_URL, data=data,
            headers={"Accept": "application/json", "User-Agent": WIKI_USER_AGENT},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return None
        token_data = r.json()
        if "access_token" not in token_data:
            return None
        return token_data
    except Exception:
        return None


def fetch_profile(access_token: str) -> dict | None:
    """Récupère l'identité Vikidia (username, sub, ...) à partir de l'access_token."""
    try:
        r = requests.get(
            PROFILE_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "User-Agent": WIKI_USER_AGENT,
                "Accept": "application/json",
            },
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return None
        profile = r.json()
        if not profile.get("username"):
            return None
        return profile
    except Exception:
        return None


def is_autopatrolled_anywhere(username: str) -> bool:
    """Renvoie True si `username` a le statut autopatrolled (ou supérieur) sur au moins
    une des versions linguistiques de Vikidia listées dans AUTOPATROL_WIKI_CODES.
    Vérification faite à chaque appel (pas de mise en cache de rôle en base)."""
    for code in AUTOPATROL_WIKI_CODES:
        try:
            url = f"https://{code}.vikidia.org/w/api.php"
            params = {
                "action": "query",
                "list": "users",
                "ususers": username,
                "usprop": "groups",
                "format": "json",
            }
            r = requests.get(
                url, params=params,
                headers={"User-Agent": WIKI_USER_AGENT},
                timeout=TIMEOUT,
            )
            if r.status_code != 200:
                continue
            data = r.json()
            users = data.get("query", {}).get("users", [])
            if not users:
                continue
            groups = set(users[0].get("groups", []))
            if groups & QUALIFYING_GROUPS:
                return True
        except Exception:
            continue
    return False