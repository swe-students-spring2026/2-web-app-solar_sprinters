import os
from flask import Flask, abort, jsonify, render_template, redirect, request, session, url_for
from dotenv import load_dotenv
from pymongo.errors import DuplicateKeyError, PyMongoError
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from .db import get_db
from .utils import serialize_doc, to_object_id
from .auth import (
    ProfileUser,
    clear_authenticated_user_id,
    get_authenticated_user_id,
    get_profile_by_email,
    get_profile_by_id,
    set_authenticated_user_id,
)

load_dotenv()

SAMPLE_PROFILES = [
    {
        "_id": "1",
        "name": "Violet",
        "email": "violet@example.com",
        "address": "violet@example.com",
        "major": "Computer Science",
        "tags": ["foodie", "travel"],
        "emoji": "😄",
        "description": "Loves coffee chats and hackathons",
        "age": 21,
    },
    {
        "_id": "2",
        "name": "Max",
        "email": "max@example.com",
        "address": "max@example.com",
        "major": "Economics",
        "tags": ["athletic"],
        "emoji": "🏋️",
        "description": "Rowing + data viz",
        "age": 22,
    },
]


# basic struct for each user:
# {
#   "_id": ObjectId,
#   "school_id": "N12345678",
#   "email": "abc123@nyu.edu",
#   "name": "Luke",
#   "age": 21,
#   "major": "Computer Science",
#   "gender": "Male",
#   "ethnicity": "Optional",
#   "emoji": "🔥",
#   "bio": "Love hiking and flute.",
#   "tags": ["foodie", "outdoors"],
  
#   "pending_match_requests": [ObjectId("..."), ObjectId("...")],
#   "current_matches": [ObjectId("..."), ObjectId("...")]
# }

def create_profile_in_db(form):
    """
    Create a profile from form data and insert it into MongoDB.
    Returns the inserted document id as a string.
    """
    name = form.get("name", "").strip()
    address = form.get("address", "").strip()
    normalized_email = address.lower()
    tags = form.getlist("tags")
    emoji = form.get("emoji", "").strip()
    description = form.get("description", "").strip()
    major = form.get("major", "").strip()
    age_raw = form.get("age", "").strip()

    if not name or not normalized_email:
        raise ValueError("name and address are required")

    age = None
    if age_raw:
        if not age_raw.isdigit():
            raise ValueError("age must be numeric")
        age = int(age_raw)

    db = get_db()
    duplicate = db.profiles.find_one(
        {
            "$or": [
                {"email_normalized": normalized_email},
                {"email": normalized_email},
                {"address": normalized_email},
            ]
        },
        {"_id": 1},
    )
    if duplicate:
        raise ValueError("A profile with this email already exists. Please log in instead.")

    doc = {
        "name": name,
        "email": normalized_email,
        "address": normalized_email,
        "email_normalized": normalized_email,
        "tags": tags,
        "emoji": emoji,
        "description": description,
        "age": age,
        "major": major,
        "pending_match_requests": [],
        "current_matches": [],
    }

    try:
        result = db.profiles.insert_one(doc)
    except DuplicateKeyError:
        raise ValueError("A profile with this email already exists. Please log in instead.")
    return str(result.inserted_id)

def search_profiles_in_db(args):
    """Search profiles based on query parameters and return a list of matching profiles."""
    import re

    name_q = args.get("name", "").strip()
    major_q = args.get("major", "").strip()
    tag_q = args.get("tag", "").strip()

    mongo_query = {}

    if name_q:
        mongo_query["name"] = {"$regex": re.escape(name_q), "$options": "i"}

    if major_q:
        mongo_query["major"] = {"$regex": re.escape(major_q), "$options": "i"}

    if tag_q and tag_q.lower() not in ("all", "any"):
        mongo_query["tags"] = tag_q

    db = get_db()
    docs = db.profiles.find(mongo_query).limit(50)

    return [serialize_doc(doc) for doc in docs]

def update_profile_in_db(profile_id, form):
    from .utils import to_object_id

    # lowercase and strip email to reliably compare against db
    address = form.get("address", "").strip()
    normalized_email = address.lower()

    updates = {
        "name": form.get("name", "").strip(),
        "address": normalized_email,
        "email": normalized_email,
        "email_normalized": normalized_email,
        "tags": form.getlist("tags"),
        "emoji": form.get("emoji", "").strip(),
        "description": form.get("description", "").strip(),
        "major": form.get("major", "").strip(),
    }

    age_raw = form.get("age", "").strip()
    if age_raw:
        if not age_raw.isdigit():
            raise ValueError("age must be numeric")
        updates["age"] = int(age_raw)

    # remove empty-string fields so existing values are not overwritten with ""
    clean_updates = {k: v for k, v in updates.items() if v != ""}

    db = get_db()
    result = db.profiles.update_one(
        {"_id": to_object_id(profile_id)},
        {"$set": clean_updates}
    )

    if result.matched_count == 0:
        raise ValueError("profile not found")

def get_pending_match_requests_for_profile(profile_id):
    db = get_db()

    try:
        me = db.profiles.find_one({"_id": to_object_id(profile_id)})
    except ValueError:
        raise ValueError("invalid profile id")

    if not me:
        raise ValueError("profile not found")

    pending_ids = me.get("pending_match_requests", [])
    if not pending_ids:
        return []

    sender_docs = list(db.profiles.find({"_id": {"$in": pending_ids}}))
    sender_map = {str(doc["_id"]): doc for doc in sender_docs}

    requests = []
    for sender_id in pending_ids:
        sid = str(sender_id)
        sender_doc = sender_map.get(sid)
        if sender_doc:
            requests.append({
                "_id": sid,
                "sender": serialize_doc(sender_doc),
                "status": "pending",
            })

    return requests

def delete_profile_in_db(profile_id):
    raw_id = (profile_id or "").strip()
    if not raw_id:
        raise ValueError("missing profile id")

    db = get_db()
    try:
        oid = to_object_id(raw_id)
    except ValueError:
        raise ValueError("invalid profile id")

    result = db.profiles.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise ValueError("profile not found")

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

    login_manager = LoginManager()
    login_manager.login_view = "login_page"
    login_manager.init_app(app)

    PENDING_LOGIN_PROFILE_ID_KEY = "pending_login_profile_id"
    PENDING_LOGIN_EMAIL_KEY = "pending_login_email"

    @login_manager.user_loader
    def load_user(user_id):
        profile_doc = get_profile_by_id(user_id)
        if not profile_doc:
            return None
        return ProfileUser(profile_doc)

    @app.before_request
    def sync_custom_session_user_id():
        if current_user.is_authenticated:
            set_authenticated_user_id(session, current_user.get_id())
        else:
            clear_authenticated_user_id(session)

    def load_profile(profile_id: str):
        """Fetch and serialize a profile or raise a ValueError with a friendly message."""
        pid = (profile_id or "").strip()
        if not pid:
            raise ValueError("Missing profile id. Use /profile?id=<profile_id>")

        db = get_db()
        try:
            doc = db.profiles.find_one({"_id": to_object_id(pid)})
        except ValueError:
            raise ValueError("Invalid profile id")

        if not doc:
            raise ValueError("Profile not found")

        return serialize_doc(doc)

    def current_user_id() -> str:
        if current_user.is_authenticated:
            return current_user.get_id()
        return get_authenticated_user_id(session) or ""

    def get_current_matches_for_profile(profile_id: str):
        """Return serialized profiles that are approved matches for the given profile."""
        profile = load_profile(profile_id)
        match_ids = profile.get("current_matches", [])
        if not match_ids:
            return []

        db = get_db()
        try:
            object_ids = [to_object_id(str(mid)) for mid in match_ids]
        except ValueError:
            object_ids = []

        if not object_ids:
            return []

        match_docs = list(db.profiles.find({"_id": {"$in": object_ids}}))
        return [serialize_doc(doc) for doc in match_docs]

    # Health check
    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})
    
    @app.get("/")
    def home():
        return render_template("index.html", session_user_id=current_user_id())

    @app.route("/login", methods=["GET", "POST"])
    def login_page():
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        error = None
        show_create_profile_cta = False
        email_value = ""

        if request.method == "POST":
            email_value = request.form.get("email", "").strip().lower()
            if not email_value:
                error = "Enter your NYU email to continue."
            else:
                profile_doc = get_profile_by_email(email_value)
                if not profile_doc:
                    error = "No account found for this email."
                    show_create_profile_cta = True
                else:
                    session[PENDING_LOGIN_PROFILE_ID_KEY] = str(profile_doc["_id"])
                    session[PENDING_LOGIN_EMAIL_KEY] = email_value
                    return redirect(url_for("mock_nyu_auth_page"))

        return render_template(
            "login.html",
            error=error,
            show_create_profile_cta=show_create_profile_cta,
            email_value=email_value,
        )

    @app.get("/login/nyu-auth")
    def mock_nyu_auth_page():
        pending_profile_id = (session.get(PENDING_LOGIN_PROFILE_ID_KEY) or "").strip()
        pending_email = (session.get(PENDING_LOGIN_EMAIL_KEY) or "").strip()
        if not pending_profile_id:
            return redirect(url_for("login_page"))

        return render_template("mock_nyu_auth.html", pending_email=pending_email)

    @app.post("/login/nyu-auth/verify")
    def mock_nyu_auth_verify():
        pending_profile_id = (session.get(PENDING_LOGIN_PROFILE_ID_KEY) or "").strip()
        if not pending_profile_id:
            return redirect(url_for("login_page"))

        profile_doc = get_profile_by_id(pending_profile_id)
        if not profile_doc:
            session.pop(PENDING_LOGIN_PROFILE_ID_KEY, None)
            session.pop(PENDING_LOGIN_EMAIL_KEY, None)
            return redirect(url_for("login_page"))

        login_user(ProfileUser(profile_doc))
        set_authenticated_user_id(session, str(profile_doc["_id"]))
        session.pop(PENDING_LOGIN_PROFILE_ID_KEY, None)
        session.pop(PENDING_LOGIN_EMAIL_KEY, None)
        return redirect(url_for("home"))

    @app.post("/logout")
    @login_required
    def logout():
        logout_user()
        clear_authenticated_user_id(session)
        session.pop(PENDING_LOGIN_PROFILE_ID_KEY, None)
        session.pop(PENDING_LOGIN_EMAIL_KEY, None)
        return redirect(url_for("home"))

    @app.route("/add", methods=["GET", "POST"])
    def add_page():
        if request.method == "POST":
            try:
                create_profile_in_db(request.form)
                return redirect(url_for("home"))
            except ValueError as e:
                return render_template("add.html", error=str(e), form_data={}), 400

        return render_template("add.html", error=None, form_data={})

    @app.route("/delete", methods=["GET", "POST"])
    @login_required
    def delete_page():
        from .utils import to_object_id

        profile_id = current_user_id()

        if request.method == "POST":
            try:
                delete_profile_in_db(profile_id)
                logout_user()
                clear_authenticated_user_id(session)
                return redirect(url_for("home"))
            except ValueError as e:
                return str(e), 400

        # load profile for confirmation page
        if not profile_id:
            return "Missing profile id. Use /delete?id=<profile_id>", 400

        db = get_db()
        try:
            doc = db.profiles.find_one({"_id": to_object_id(profile_id)})
        except ValueError:
            return "Invalid profile id", 400

        if not doc:
            return "Profile not found", 404

        profile = serialize_doc(doc)
        return render_template("delete.html", profile=profile)

    @app.route("/edit", methods=["GET", "POST"])
    @app.get("/edit")
    @login_required
    def edit_page():
        from .utils import to_object_id

        db = get_db()
        profile_id = current_user_id()

        try:
            doc = db.profiles.find_one({"_id": to_object_id(profile_id)})
        except ValueError:
            return "Invalid profile id", 400

        if not doc:
            return "No profile found to edit", 404

        profile = serialize_doc(doc)
        return render_template("edit.html", profile=profile)

    @app.route("/match-results", methods=["GET"])
    @login_required
    def match_results_page():
        profile_id = current_user_id()
        if not profile_id:
            return "Missing profile id. Use /match-results?id=<profile_id>", 400

        try:
            requests_list = get_pending_match_requests_for_profile(profile_id)
            matches_list = get_current_matches_for_profile(profile_id)
        except ValueError as e:
            return str(e), 400

        return render_template(
            "match_results.html",
            requests=requests_list,
            matches=matches_list,
            owner_id=profile_id,
        )

    @app.post("/matches/send")
    @login_required
    def send_match_request():
        target_id = request.form.get("target_id", "").strip()
        requester_id = current_user_id()
        back = request.form.get("back", "").strip()

        if not target_id or not requester_id:
            return "Missing target or requester id", 400

        if target_id == requester_id:
            return "Cannot send a match request to yourself", 400

        db = get_db()

        # Ensure both profiles exist
        try:
            target_doc = db.profiles.find_one({"_id": to_object_id(target_id)})
            requester_doc = db.profiles.find_one({"_id": to_object_id(requester_id)})
        except ValueError:
            return "Invalid profile id", 400

        if not target_doc or not requester_doc:
            return "Profile not found", 404

        db.profiles.update_one(
            {"_id": to_object_id(target_id)},
            {"$addToSet": {"pending_match_requests": to_object_id(requester_id)}},
        )

        if back:
            return redirect(back)
        return redirect(url_for("search_page", id=requester_id))

    @app.post("/matches/handle")
    @login_required
    def handle_match_request():
        owner_id = current_user_id()
        requester_id = request.form.get("requester_id", "").strip()
        action = request.form.get("action", "").strip()
        back = request.form.get("back", "").strip()

        if not owner_id or not requester_id or action not in ("approve", "reject"):
            return "Missing data for handling match request", 400

        db = get_db()
        try:
            owner_oid = to_object_id(owner_id)
            requester_oid = to_object_id(requester_id)
        except ValueError:
            return "Invalid profile id", 400

        # Make sure both profiles exist
        if not db.profiles.find_one({"_id": owner_oid}) or not db.profiles.find_one({"_id": requester_oid}):
            return "Profile not found", 404

        if action == "approve":
            db.profiles.update_one(
                {"_id": owner_oid},
                {
                    "$pull": {"pending_match_requests": requester_oid},
                    "$addToSet": {"current_matches": requester_oid},
                },
            )
            db.profiles.update_one(
                {"_id": requester_oid},
                {"$addToSet": {"current_matches": owner_oid}},
            )
        else:
            db.profiles.update_one(
                {"_id": owner_oid},
                {"$pull": {"pending_match_requests": requester_oid}},
            )

        if back:
            return redirect(back)
        return redirect(url_for("match_results_page", id=owner_id))

    @app.get("/search")
    @login_required
    def search_page():
        db = get_db()
        docs = db.profiles.find({}).limit(100)
        profiles = [serialize_doc(doc) for doc in docs]
        viewer_id = current_user_id()
        return render_template("search.html", profiles=profiles, viewer_id=viewer_id)

    @app.post("/profiles/<profile_id>/update")
    @login_required
    def update_profile(profile_id):
        if profile_id != current_user_id():
            abort(403)

        try:
            update_profile_in_db(profile_id, request.form)
        except ValueError:
            return "Invalid update request", 400

        return redirect(url_for("view_profile_page", profile_id=profile_id))
    @app.get("/profile")
    @login_required
    def view_profile():
        profile_id = request.args.get("id", "").strip() or current_user_id()
        viewer_id = current_user_id()
        source = request.args.get("from", "").strip()
        back = request.args.get("back", "").strip()

        try:
            profile = load_profile(profile_id)
        except ValueError as e:
            return str(e), 400

        already_matched = False
        if viewer_id and viewer_id != profile_id:
            try:
                viewer_profile = load_profile(viewer_id)
            except ValueError:
                viewer_profile = None

            if viewer_profile:
                matches_raw = viewer_profile.get("current_matches", [])
                match_ids = {str(mid) for mid in matches_raw}
                already_matched = str(profile_id) in match_ids or str(profile["_id"]) in match_ids

        return render_template(
            "view.html",
            profile=profile,
            viewer_id=viewer_id,
            source=source,
            back=back,
            already_matched=already_matched,
        )

    @app.get("/profiles/<profile_id>")
    @login_required
    def view_profile_page(profile_id):
        # Keep old path working; funnel through the query-based view for consistency
        return redirect(url_for("view_profile", id=profile_id))


    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG") == "1")
