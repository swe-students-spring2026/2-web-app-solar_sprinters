import os
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
from .db import get_db
from .utils import serialize_doc

load_dotenv()


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
    
    @app.get("/add")
    def add_page():
        return render_template("add.html")
    
    @app.get("/delete")
    def delete_page():
        return render_template("delete.html")

    @app.get("/edit")
    def edit_page():
        return render_template("edit.html")

    @app.get("/match-results")
    def match_results_page():
        return render_template("match_results.html")
    
    @app.get("/search")
    def search_page():
        return render_template("search.html")
    

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG") == "1")