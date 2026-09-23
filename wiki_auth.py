"""
Authentification OAuth2 Vikidia (extension MediaWiki OAuth, flow central.vikidia.org)
+ vérification "autopatrol" multi-wikis pour l'accès Collaborateur automatique.

Remplace l'ancien système GitHub OAuth du dashboard.
"""
from __future__ import annotations

import base64
import hashlib
import logging
import os
import secrets
import time
from logging.handlers import RotatingFileHandler

from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

WIKI_OAUTH_CLIENT_ID = os.environ.get("WIKI_OAUTH_CLIENT_ID")
WIKI_OAUTH_CLIENT_SECRET = os.environ.get("WIKI_OAUTH_CLIENT_SECRET")
WIKI_OAUTH_CALLBACK = os.environ.get("WIKI_OAUTH_CALLBACK")
# Base REST du wiki central utilisé pour l'OAuth2 (ex: https://central.vikidia.org/w/rest.php)
WIKI_OAUTH_REST_BASE = (os.environ.get("WIKI_OAUTH_REST_BASE") or "").rstrip("/")
WIKI_USER_AGENT = os.environ.get("WIKI_USER_AGENT", "BotJanus/1.0")


# ============================================================
# JOURNAL D'AUTHENTIFICATION (temps réel) : logs_vikidia_auth.txt
# ============================================================
# Une ligne est écrite ET vidée sur disque à chaque événement : `tail -f logs_vikidia_auth.txt`
# permet de suivre une connexion / vérification autopatrol en direct.
# Jamais loggés : code OAuth, access_token, client_secret, mots de passe.
# Chemin modifiable via WIKI_AUTH_LOG_PATH dans le .env. Rotation à 2 Mo (1 archive .1).
AUTH_LOG_PATH = os.environ.get("WIKI_AUTH_LOG_PATH") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "logs_vikidia_auth.txt")


def _build_auth_logger() -> logging.Logger:
    lg = logging.getLogger("vikidia_auth")
    if lg.handlers:  # évite les doublons si le module est rechargé
        return lg
    lg.setLevel(logging.INFO)
    lg.propagate = False
    try:
        handler = RotatingFileHandler(AUTH_LOG_PATH, maxBytes=2 * 1024 * 1024,
                                      backupCount=1, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s", "%Y-%m-%d %H:%M:%S"))
        lg.addHandler(handler)  # le handler vide le tampon après chaque ligne -> temps réel
    except OSError as e:
        lg.addHandler(logging.NullHandler())
        print(f"wiki_auth : impossible d'ouvrir {AUTH_LOG_PATH} ({e}) — journal désactivé.")
    return lg


_auth_logger = _build_auth_logger()


def log_auth(message: str) -> None:
    """Écrit une ligne dans logs_vikidia_auth.txt (ne lève jamais d'exception)."""
    try:
        _auth_logger.info(message)
    except Exception:
        pass


def _short(text, limit: int = 600) -> str:
    text = str(text).replace("\n", " ").replace("\r", " ")
    return text if len(text) <= limit else text[:limit] + f"…(+{len(text) - limit} car.)"


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
# Sur Vikidia le statut s'appelle "Autopatrol" (Vikidia:Autopatrol) : selon le wiki, le nom
# technique du groupe peut être "autopatrol" ou "autopatrolled" -> on accepte les deux.
# En plus des groupes, on regarde le DROIT "autopatrol" (voir _check_one_wiki), qui est
# ce que le statut confère réellement et que patrouilleurs/admins/bureaucrates ont aussi.
QUALIFYING_GROUPS = {"autopatrol", "autopatrolled", "patroller", "sysop", "bureaucrat"}

TIMEOUT = 10          # OAuth (échange de code, profil)
CHECK_TIMEOUT = 5     # vérification autopatrol : par wiki, en parallèle


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
            log_auth(f"OAUTH token : ÉCHEC HTTP {r.status_code} | corps={_short(r.text, 300)}")
            return None
        token_data = r.json()
        if "access_token" not in token_data:
            log_auth(f"OAUTH token : réponse 200 SANS access_token | clés={sorted(token_data)}")
            return None
        log_auth("OAUTH token : OK (access_token reçu)")
        return token_data
    except Exception as e:
        log_auth(f"OAUTH token : EXCEPTION {type(e).__name__}: {e}")
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
            log_auth(f"OAUTH profil : ÉCHEC HTTP {r.status_code} | corps={_short(r.text, 300)}")
            return None
        profile = r.json()
        if not profile.get("username"):
            log_auth(f"OAUTH profil : pas de 'username' | clés={sorted(profile)}")
            return None
        log_auth(f"OAUTH profil : OK | username={profile.get('username')!r} | sub={profile.get('sub')!r} "
                 f"| clés={sorted(profile)}")
        return profile
    except Exception as e:
        log_auth(f"OAUTH profil : EXCEPTION {type(e).__name__}: {e}")
        return None


def _check_one_wiki(code: str, username: str, cid: str = "-"):
    """Interroge UN wiki. Renvoie True (statut qualifiant), False (compte absent ou
    sans statut suffisant) ou None (wiki injoignable / réponse inexploitable).
    Chaque réponse est détaillée dans logs_vikidia_auth.txt."""
    t0 = time.monotonic()
    try:
        r = requests.get(
            f"https://{code}.vikidia.org/w/api.php",
            params={
                "action": "query",
                "list": "users",
                "ususers": username,
                "usprop": "groups|implicitgroups|rights",
                "format": "json",
            },
            headers={"User-Agent": WIKI_USER_AGENT},
            timeout=CHECK_TIMEOUT,
        )
        dt = time.monotonic() - t0
        if r.status_code != 200:
            log_auth(f"[{cid}] {code:>3} : HTTP {r.status_code} en {dt:.2f}s -> wiki INJOIGNABLE "
                     f"| corps={_short(r.text, 300)}")
            return None
        data = r.json()
        if "error" in data:
            log_auth(f"[{cid}] {code:>3} : erreur API en {dt:.2f}s | {_short(data['error'], 300)}")
            return None
        users = data.get("query", {}).get("users", [])
        if not users:
            log_auth(f"[{cid}] {code:>3} : réponse SANS entrée 'users' en {dt:.2f}s | brut={_short(r.text)}")
            return False
        u = users[0]
        if "missing" in u or "invalid" in u:
            log_auth(f"[{cid}] {code:>3} : compte INEXISTANT/invalide sur ce wiki ({dt:.2f}s) | brut={_short(u)}")
            return False
        groups = set(u.get("groups", []))
        implicit = set(u.get("implicitgroups", []))
        rights = set(u.get("rights", []))
        by_group = sorted((groups | implicit) & QUALIFYING_GROUPS)
        by_right = "autopatrol" in rights
        ok = bool(by_group) or by_right
        via = []
        if by_group:
            via.append(f"groupe(s) {by_group}")
        if by_right:
            via.append("droit 'autopatrol'")
        log_auth(f"[{cid}] {code:>3} : HTTP 200 en {dt:.2f}s | nom_renvoyé={u.get('name')!r} "
                 f"| groups={sorted(groups)} | implicit={sorted(implicit)} | nb_droits={len(rights)} "
                 f"-> {'QUALIFIÉ via ' + ' + '.join(via) if ok else 'non qualifié'}")
        return ok
    except Exception as e:
        log_auth(f"[{cid}] {code:>3} : EXCEPTION {type(e).__name__}: {e} "
                 f"({time.monotonic() - t0:.2f}s) -> wiki INJOIGNABLE")
        return None


def find_autopatrol_wiki(username: str):
    """Cherche le statut autopatrol (ou supérieur) de `username` sur les versions
    linguistiques de Vikidia, en interrogeant tous les wikis EN PARALLÈLE.

    Dès qu'un wiki qualifiant répond, la recherche s'arrête (les requêtes encore en
    attente sont annulées) et on renvoie son code.

    Renvoie (code_wiki, incomplet) :
      - ("fr", False)  : statut trouvé sur fr.vikidia.org -> accès accordé
      - (None, False)  : tous les wikis ont répondu, aucun statut suffisant
      - (None, True)   : rien trouvé MAIS au moins un wiki n'a pas répondu
                         (on ne peut pas conclure -> inviter à réessayer)
    """
    cid = secrets.token_hex(2)  # identifiant pour relier les lignes d'une même vérification
    log_auth(f"[{cid}] ===== DÉBUT vérification autopatrol | username={username!r} "
             f"| {len(AUTOPATROL_WIKI_CODES)} wikis en parallèle")
    if not username:
        log_auth(f"[{cid}] username vide -> refus")
        return None, False
    pool = ThreadPoolExecutor(max_workers=len(AUTOPATROL_WIKI_CODES))
    futures = {pool.submit(_check_one_wiki, code, username, cid): code
               for code in AUTOPATROL_WIKI_CODES}
    results, errors = {}, 0
    try:
        for fut in as_completed(futures):
            code = futures[fut]
            res = fut.result()
            results[code] = res
            if res:
                pending = sorted(c for f, c in futures.items() if not f.done())
                log_auth(f"[{cid}] ===== TROUVÉ sur {code}.vikidia.org -> recherche ARRÊTÉE "
                         f"(wikis non attendus : {pending or 'aucun'})")
                return code, False
            if res is None:
                errors += 1
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    log_auth(f"[{cid}] ===== AUCUN STATUT trouvé | wikis en erreur={errors} "
             f"| détail={results} -> {'INCOMPLET (réessayer)' if errors else 'refus définitif'}")
    return None, errors > 0


def is_autopatrolled_anywhere(username: str) -> bool:
    """Compatibilité : simple booléen (voir find_autopatrol_wiki pour le détail)."""
    return find_autopatrol_wiki(username)[0] is not None