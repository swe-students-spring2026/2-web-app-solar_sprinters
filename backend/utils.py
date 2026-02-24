from bson import ObjectId

def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise ValueError("Invalid id format")

def serialize_doc(doc: dict) -> dict:
    """Convert MongoDB document to JSON-safe dict."""
    if not doc:
        return doc
    out = dict(doc)
    if "_id" in out:
        out["_id"] = str(out["_id"])
    return out