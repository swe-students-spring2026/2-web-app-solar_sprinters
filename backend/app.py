import os
from flask import Flask, jsonify, render_template, redirect, request, url_for
from dotenv import load_dotenv
from .db import get_db
from .utils import serialize_doc

load_dotenv()


# temp profiles to demo for now, need to connect database
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
    tags = form.getlist("tags")
    emoji = form.get("emoji", "").strip()
    description = form.get("description", "").strip()
    major = form.get("major", "").strip()
    age_raw = form.get("age", "").strip()

    if not name or not address:
        raise ValueError("name and address are required")

    age = None
    if age_raw:
        if not age_raw.isdigit():
            raise ValueError("age must be numeric")
        age = int(age_raw)

    doc = {
        "name": name,
        "email": address,
        "address": address,
        "tags": tags,
        "emoji": emoji,
        "description": description,
        "age": age,
        "major": major,
        "pending_match_requests": [],
        "current_matches": [],
    }

    db = get_db()
    result = db.profiles.insert_one(doc)
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
            except ValueError:
                return render_template("add.html"), 400

        return render_template("add.html")

    @app.route("/delete", methods=["GET", "POST"])
    def delete_page():
        profile = SAMPLE_PROFILES[0]

        if request.method == "POST":
            return redirect(url_for("home"))

        return render_template("delete.html", profile=profile)

    @app.route("/edit", methods=["GET", "POST"])
    def edit_page():
        profile = SAMPLE_PROFILES[0]

        if request.method == "POST":
            updated = {
                "name": request.form.get("name", profile["name"]),
                "address": request.form.get("address", profile["address"]),
                "tags": request.form.getlist("tags") or profile["tags"],
                "emoji": request.form.get("emoji", profile["emoji"]),
                "description": request.form.get("description", profile["description"]),
                "age": request.form.get("age", profile["age"]),
                "major": request.form.get("major", profile["major"]),
            }

            return render_template(
                "view.html",
                name=updated["name"],
                address=updated["address"],
                tags=updated["tags"],
                emoji=updated["emoji"],
                description=updated["description"],
                age=updated["age"],
                major=updated["major"],
            )

        return render_template("edit.html", profile=profile)

    @app.route("/match-results", methods=["GET"])
    def match_results_page():
        requests = [
            {
                "_id": "req1",
                "sender": SAMPLE_PROFILES[1],
                "status": "pending",
            }
        ]
        return render_template("match_results.html", requests=requests)

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
        profile = SAMPLE_PROFILES[0]
        updated = {
            "name": request.form.get("name", profile["name"]),
            "address": request.form.get("address", profile["address"]),
            "tags": request.form.getlist("tags") or profile["tags"],
            "emoji": request.form.get("emoji", profile["emoji"]),
            "description": request.form.get("description", profile["description"]),
            "age": request.form.get("age", profile["age"]),
            "major": request.form.get("major", profile["major"]),
        }
        return render_template(
            "view.html",
            name=updated["name"],
            address=updated["address"],
            tags=updated["tags"],
            emoji=updated["emoji"],
            description=updated["description"],
            age=updated["age"],
            major=updated["major"],
        )
    @app.get("/profiles/<profile_id>")
    def view_profile_page(profile_id):
        from .utils import to_object_id  # local import to avoid changing top imports

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
