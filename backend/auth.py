try:
    from flask_login import UserMixin
except ModuleNotFoundError:
    class UserMixin:
        """Fallback so import doesn't mess with compile before flask_login is installed in env."""


from .db import get_db
from .utils import serialize_doc, to_object_id

SESSION_USER_ID_KEY = "current_user_id"
ALLOWED_EMAIL_DOMAINS = {"nyu.edu", "stern.nyu.edu", "tandon.nyu.edu"}


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def is_allowed_domain(email: str) -> bool:
    normalized = normalize_email(email)
    if "@" not in normalized:
        return False

    domain = normalized.rsplit("@", 1)[1]
    return domain in ALLOWED_EMAIL_DOMAINS


def get_profile_by_email(email: str):
    normalized = normalize_email(email)
    if not normalized:
        return None

    db = get_db()
    return db.profiles.find_one(
        {
            "$or": [
                {"email_normalized": normalized},
                {"email": normalized},
                {"address": normalized},
            ]
        }
    )


def get_profile_by_id(profile_id: str):
    try:
        oid = to_object_id(profile_id)
    except ValueError:
        return None

    db = get_db()
    return db.profiles.find_one({"_id": oid})


def get_authenticated_user_id(session_obj):
    user_id = (session_obj.get(SESSION_USER_ID_KEY) or "").strip()
    return user_id or None


def set_authenticated_user_id(session_obj, profile_id: str):
    session_obj[SESSION_USER_ID_KEY] = str(profile_id).strip()


def clear_authenticated_user_id(session_obj):
    session_obj.pop(SESSION_USER_ID_KEY, None)


class ProfileUser(UserMixin):
    def __init__(self, profile_doc: dict):
        self.profile = serialize_doc(profile_doc)

    def get_id(self) -> str:
        return self.profile["_id"]

    @property
    def name(self) -> str:
        return self.profile.get("name", "User")

    @property
    def email(self) -> str:
        return self.profile.get("email", "")
