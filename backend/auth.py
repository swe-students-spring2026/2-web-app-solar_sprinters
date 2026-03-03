from flask_login import UserMixin

from .db import get_db
from .utils import serialize_doc, to_object_id

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
    return db.profiles.find_one({"email_normalized": normalized})


def get_profile_by_id(profile_id: str):
    try:
        oid = to_object_id(profile_id)
    except ValueError:
        return None

    db = get_db()
    return db.profiles.find_one({"_id": oid})


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
