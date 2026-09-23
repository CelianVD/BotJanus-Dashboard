# BotJanus — Documentation technique

Dashboard Flask + API pour bot Discord, au service de Vikidia. Permet de lancer/
surveiller des scripts Python ("bots"), avec authentification via l'OAuth2 de
Vikidia (central.vikidia.org) et un système de rôles.

## 1. Architecture

```
flask_app.py       # Config, DB (SQLite), décorateurs de sécurité, moteur de
                    # lancement de scripts, planificateur, factory create_app()
wiki_auth.py        # OAuth2 PKCE vers central.vikidia.org + vérification
                    # "autopatrol" multi-wikis (requêtes action=query aux API
                    # MediaWiki de chaque version linguistique)
routes_user.py       # Blueprints auth_bp / dashboard_bp / api_bp : login,
                      # callback OAuth, dashboard, lancement/arrêt de script,
                      # historique + exports, API REST pour le bot Discord
routes_admin.py      # Blueprint admin_bp : gestion utilisateurs/rôles, backup
                      # CSV, éditeur de scripts, planification, stats, réglages
routes_contact.py    # Blueprint contact_bp : formulaire de contact + boîte
                      # de réception admin
templates.py          # Tous les templates HTML (render_template_string)
langs.txt             # Référence des versions linguistiques de Vikidia
.env / .env.example   # Secrets et configuration (voir §3)
```

`flask_app.create_app()` enregistre les 5 blueprints, initialise la base SQLite
(`init_db`, avec migration automatique `github_id` → `wiki_id` pour les
anciennes bases issues du système GitHub OAuth), démarre le thread du
planificateur (`start_scheduler_thread`) et ajoute :
- un `before_request` global qui redirige vers `/security-gate` (reCAPTCHA) si
  l'option est activée en base et que la session ne l'a pas déjà validé ;
- un `context_processor` qui injecte `t()` (traductions), `current_lang` et le
  compteur de messages non lus (visible seulement aux admins).

## 2. Authentification & rôles

### 2.1 Connexion Vikidia (OAuth2 PKCE)

`GET /login` génère une paire PKCE (`generate_pkce_pair`) et redirige vers
`central.vikidia.org` (extension MediaWiki OAuth2). `GET /oauth/wiki/callback`
échange le code contre un `access_token` puis récupère le profil
(`fetch_profile`). L'utilisateur est créé/mis à jour en base (`INSERT OR
REPLACE`) ; son rôle existant est conservé, sauf si son nom d'utilisateur
correspond à `WIKI_ROOT_ADMIN_USERNAME`, auquel cas il est promu `Admin`.

### 2.2 Connexion manuelle

`GET/POST /admin/login` — compte de secours indépendant d'OAuth, identifiants
définis par `MANUAL_LOGIN_ID` / `MANUAL_LOGIN_PASS` (voir .env). Crée/replace
l'utilisateur `MANUAL_ADMIN_ID` avec le rôle `Admin`.

### 2.3 Les trois rôles stockés en base

| Rôle            | Constante      | Donne accès à                                   |
|-----------------|----------------|--------------------------------------------------|
| `None`          | `ROLE_NONE`    | Rien par défaut — sauf vérification live (2.4)   |
| `Collaborateur` | `ROLE_COLLAB`  | Lancer/arrêter les scripts                        |
| `Admin`         | `ROLE_ADMIN`   | Tout, + gestion utilisateurs, scripts, réglages    |

### 2.4 Accès "Collaborateur" automatique par vérification live (autopatrol)

**Aucune promotion de rôle n'est enregistrée en base.** Un utilisateur en rôle
`None` peut quand même lancer un script si `wiki_auth.is_autopatrolled_anywhere
(username)` renvoie `True` : la fonction interroge l'API MediaWiki
(`action=query&list=users&usprop=groups`) de **chaque** wiki listé dans
`wiki_auth.AUTOPATROL_WIKI_CODES` (voir `langs.txt` pour la liste complète des
14 versions linguistiques de Vikidia) et considère l'accès autorisé si
l'utilisateur possède l'un des groupes `QUALIFYING_GROUPS` — c'est-à-dire
**autopatrolleur, patrouilleur, administrateur ou bureaucrate** — sur au moins
une de ces versions. Ce contrôle est refait à **chaque tentative de
lancement** (`dashboard.start_script`) et à chaque appel
`/api/discord/permissions` côté bot Discord : il n'y a donc pas de cache de
rôle à invalider si le statut wiki d'un utilisateur change.

### 2.5 Décorateurs de sécurité (`flask_app.py`)

- `login_required` : redirige vers `/` si pas de session.
- `check_role([...])` : vérifie rôle + statut banni ; `'All'` autorise tout
  utilisateur connecté non banni.
- `require_api_key` : vérifie le header `X-API-Key` (== `API_KEY`) sur les
  routes `/api/*` appelées par le bot Discord.

### 2.6 Liaison Discord ↔ Vikidia

Le bot Discord appelle `POST /api/discord/link/start` (avec `API_KEY`) pour
obtenir une URL à usage unique, valable `DISCORD_LINK_TOKEN_TTL_MINUTES = 15`.
L'utilisateur l'ouvre, se connecte via Vikidia si besoin (le token est gardé
en session le temps du round-trip OAuth), puis confirme sur
`/discord/link/<token>`. Le bot vérifie ensuite les droits via
`GET /api/discord/permissions?discord_id=...`.

## 3. Configuration — variables d'environnement

Toutes les valeurs sensibles ont été retirées du code (plus aucun secret par
défaut codé en dur) : le démarrage échoue explicitement si une variable
obligatoire manque, plutôt que de retomber silencieusement sur une valeur
faible. Voir `.env.example` pour la liste complète et des commentaires par
variable. Variables obligatoires : `FLASK_SECRET_KEY`, `WIKI_OAUTH_CLIENT_ID`,
`WIKI_OAUTH_CLIENT_SECRET`, `WIKI_OAUTH_CALLBACK`, `WIKI_OAUTH_REST_BASE`,
`MANUAL_LOGIN_PASS`, `API_KEY`, `BOTS_DIR`.

`flask_app.py` charge désormais le `.env` avec un **chemin absolu**
(`os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")`) plutôt
que de compter sur le répertoire de travail courant — important sur
PythonAnywhere où le process WSGI ne démarre pas forcément avec le dossier du
projet comme `cwd`.

## 4. Modèle de données (SQLite, `init_db`)

- `users` (wiki_id PK, username, avatar, role, is_banned, lang, ban_reason,
  discord_id) — migration auto `github_id`→`wiki_id` depuis l'ancien système.
- `discord_links` (token PK, discord_id, discord_username, created_at, used).
- `logs` (id, date, script, message).
- `settings` (key PK, value) — `lock_launch`, `captcha_enabled`.
- `script_config` (filename PK, is_active).
- `schedules` (id, script_name, frequency, time_value, last_run, next_run,
  is_enabled) — traité par `scheduler_loop` (boucle de fond, tick 30s).
- `messages` (id, wiki_id, username, content, date, is_read) — formulaire de
  contact.

## 5. Lancement de scripts

`launch_script_core` lance `python3 -u <script>` en sous-processus
(`subprocess.Popen`), un seul à la fois (`status["running"]`). La sortie est
lue ligne à ligne dans un thread (`read_output`) et journalisée en base
(`log_to_db`) ainsi que gardée en mémoire (`status["live_output"]`, 50-100
dernières lignes affichées). `/admin/scripts/toggle` permet de désactiver un
script pour les non-admins (`script_config.is_active`), et
`/admin/schedules` permet de planifier un lancement récurrent.