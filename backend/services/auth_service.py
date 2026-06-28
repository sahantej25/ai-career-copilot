import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import jwt

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
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def register_user(email: str, password: str, name: str) -> UserPublic:
    email_norm = email.strip().lower()
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    data = _load_users_raw()
    if any(u["email"] == email_norm for u in data.get("users", [])):
        raise ValueError("An account with this email already exists.")

    user_id = str(uuid.uuid4())[:12]
    record = {
        "id": user_id,
        "email": email_norm,
        "name": name.strip() or email_norm.split("@")[0],
        "password_hash": hash_password(password),
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    data.setdefault("users", []).append(record)
    _save_users_raw(data)

    user_data_path(user_id).parent.mkdir(parents=True, exist_ok=True)
    if not user_data_path(user_id).exists():
        from models.schemas import AppData
        with open(user_data_path(user_id), "w", encoding="utf-8") as f:
            json.dump(AppData().model_dump(), f, indent=2)

    return UserPublic(id=user_id, email=email_norm, name=record["name"])


def authenticate_user(email: str, password: str) -> UserPublic:
    email_norm = email.strip().lower()
    data = _load_users_raw()
    user = next((u for u in data.get("users", []) if u["email"] == email_norm), None)
    if not user or not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid email or password.")
    return UserPublic(id=user["id"], email=user["email"], name=user["name"])


def get_user_by_id(user_id: str) -> UserPublic | None:
    data = _load_users_raw()
    user = next((u for u in data.get("users", []) if u["id"] == user_id), None)
    if not user:
        return None
    return UserPublic(id=user["id"], email=user["email"], name=user["name"])


def user_data_path(user_id: str) -> Path:
    return Path(settings.users_dir) / user_id / "data.json"
