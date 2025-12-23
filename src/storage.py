import json
from pathlib import Path
from datetime import datetime

PENDING_PATH = Path("pending_review.json")
LAST_DRAFT_PATH = Path("last_draft.json")


def save_pending(movie, review, attempts: int = 1):
    PENDING_PATH.write_text(
        json.dumps({"movie": movie, "review": review, "attempts": attempts}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_last_draft(item: dict, draft_id: str | None = None, kind: str = "movie"):
    """Save last draft metadata under `kind` key (movie or tv)."""
    data = {}
    if LAST_DRAFT_PATH.exists():
        try:
            data = json.loads(LAST_DRAFT_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    data[kind] = {
        "item": item,
        "draft_id": draft_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    LAST_DRAFT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_last_draft(kind: str | None = None):
    if not LAST_DRAFT_PATH.exists():
        return None
    try:
        data = json.loads(LAST_DRAFT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
    if kind:
        return data.get(kind)
    return data
