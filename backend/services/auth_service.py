import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import bcrypt
import jwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from config import settings
from models.schemas import UserPublic

USERS_FILE = "users.json"


def _users_path() -> Path:
    return Path(settings.users_dir) / USERS_FILE


def _load_users_raw() -> dict:
    path = _users_path()
    if not path.exists():
        return {"users": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_users_raw(data: dict) -> None:
    path = _users_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: str, email: str) -> str:
    from datetime import timedelta

    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def user_data_path(user_id: str) -> Path:
    return Path(settings.users_dir) / user_id / "data.json"


def _ensure_user_workspace(user_id: str) -> None:
    user_data_path(user_id).parent.mkdir(parents=True, exist_ok=True)
    if not user_data_path(user_id).exists():
        from models.schemas import AppData

        with open(user_data_path(user_id), "w", encoding="utf-8") as f:
            json.dump(AppData().model_dump(), f, indent=2)


def _to_public(user: dict) -> UserPublic:
    return UserPublic(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        auth_provider=user.get("auth_provider", "local"),
        picture=user.get("picture", ""),
    )


def verify_google_credential(credential: str) -> dict:
    if not settings.google_client_id:
        raise ValueError("Google sign-in is not configured on the server.")
    idinfo = id_token.verify_oauth2_token(
        credential,
        google_requests.Request(),
        settings.google_client_id,
    )
    issuer = idinfo.get("iss", "")
    if issuer not in ("accounts.google.com", "https://accounts.google.com"):
        raise ValueError("Invalid Google token issuer.")
    if not idinfo.get("email_verified"):
        raise ValueError("Google email is not verified.")
    return idinfo


def register_user(email: str, password: str, name: str) -> UserPublic:
    email_norm = email.strip().lower()
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    data = _load_users_raw()
    existing = next((u for u in data.get("users", []) if u["email"] == email_norm), None)
    if existing:
        if existing.get("auth_provider") == "google" and not existing.get("password_hash"):
            raise ValueError("This email is registered with Google. Please continue with Google sign-in.")
        raise ValueError("An account with this email already exists.")

    user_id = str(uuid.uuid4())[:12]
    record = {
        "id": user_id,
        "email": email_norm,
        "name": name.strip() or email_norm.split("@")[0],
        "password_hash": hash_password(password),
        "auth_provider": "local",
        "google_sub": "",
        "picture": "",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    data.setdefault("users", []).append(record)
    _save_users_raw(data)
    _ensure_user_workspace(user_id)
    return _to_public(record)


def authenticate_user(email: str, password: str) -> UserPublic:
    email_norm = email.strip().lower()
    data = _load_users_raw()
    user = next((u for u in data.get("users", []) if u["email"] == email_norm), None)
    if not user:
        raise ValueError("Invalid email or password.")
    if not user.get("password_hash"):
        raise ValueError("This account uses Google sign-in. Please continue with Google.")
    if not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid email or password.")
    return _to_public(user)


def authenticate_google_user(credential: str) -> UserPublic:
    idinfo = verify_google_credential(credential)
    email = idinfo["email"].strip().lower()
    google_sub = idinfo["sub"]
    name = (idinfo.get("name") or email.split("@")[0]).strip()
    picture = idinfo.get("picture") or ""

    data = _load_users_raw()
    users = data.setdefault("users", [])

    user = next((u for u in users if u.get("google_sub") == google_sub), None)
    if not user:
        user = next((u for u in users if u["email"] == email), None)
        if user:
            user["google_sub"] = google_sub
            user["auth_provider"] = "linked" if user.get("password_hash") else "google"
            if picture:
                user["picture"] = picture
            if not user.get("name"):
                user["name"] = name
            _save_users_raw(data)
        else:
            user_id = str(uuid.uuid4())[:12]
            user = {
                "id": user_id,
                "email": email,
                "name": name,
                "password_hash": "",
                "auth_provider": "google",
                "google_sub": google_sub,
                "picture": picture,
                "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
            users.append(user)
            _save_users_raw(data)
            _ensure_user_workspace(user_id)

    return _to_public(user)


def get_user_by_id(user_id: str) -> UserPublic | None:
    data = _load_users_raw()
    user = next((u for u in data.get("users", []) if u["id"] == user_id), None)
    if not user:
        return None
    return _to_public(user)
