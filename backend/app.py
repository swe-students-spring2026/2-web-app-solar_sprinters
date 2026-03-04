import os
from flask import Flask, jsonify, render_template, redirect, request, url_for
from dotenv import load_dotenv
from pymongo.errors import DuplicateKeyError, PyMongoError
from .db import get_db
from .utils import serialize_doc, to_object_id

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
    from .utils import to_object_id

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
    from .utils import to_object_id

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

    # Health check
    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})
    
    @app.get("/")
    def home():
        return render_template("index.html")

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
    def delete_page():
        from .utils import to_object_id

        profile_id = request.args.get("id", "").strip()

        if request.method == "POST":
            profile_id = request.form.get("id", "").strip() or profile_id
            try:
                delete_profile_in_db(profile_id)
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
    def edit_page():
        from .utils import to_object_id

        db = get_db()
        profile_id = request.args.get("id", "").strip()

        if profile_id:
            try:
                doc = db.profiles.find_one({"_id": to_object_id(profile_id)})
            except ValueError:
                return "Invalid profile id", 400
        else:
            # fallback: open most recently created profile
            doc = db.profiles.find_one(sort=[("_id", -1)])

        if not doc:
            return "No profile found to edit", 404

        profile = serialize_doc(doc)
        return render_template("edit.html", profile=profile)

    @app.route("/match-results", methods=["GET"])
    def match_results_page():
        profile_id = request.args.get("id", "").strip()
        if not profile_id:
            return "Missing profile id. Use /match-results?id=<profile_id>", 400

        try:
            requests_list = get_pending_match_requests_for_profile(profile_id)
        except ValueError as e:
            return str(e), 400

        return render_template("match_results.html", requests=requests_list)

    @app.post("/match-results/handle")
    def handle_request():
        # Placeholder for accept/reject actions
        return redirect(url_for("match_results_page"))

    @app.get("/search")
    def search_page():
        db = get_db()
        docs = db.profiles.find({}).limit(100)
        profiles = [serialize_doc(doc) for doc in docs]
        return render_template("search.html", profiles=profiles)

    @app.post("/profiles/<profile_id>/update")
    def update_profile(profile_id):
        try:
            update_profile_in_db(profile_id, request.form)
        except ValueError:
            return "Invalid update request", 400

        return redirect(url_for("view_profile_page", profile_id=profile_id))
    @app.get("/profiles/<profile_id>")
    def view_profile_page(profile_id):  

        db = get_db()
        try:
            doc = db.profiles.find_one({"_id": to_object_id(profile_id)})
        except ValueError:
            return "Invalid profile id", 400

        if not doc:
            return "Profile not found", 404

        profile = serialize_doc(doc)
        return render_template("view.html", **profile)


    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG") == "1")
