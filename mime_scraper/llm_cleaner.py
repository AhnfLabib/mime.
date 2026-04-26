import os
import json
import re
from typing import Dict, Any, List

from bs4 import BeautifulSoup

MODEL_NAME = os.getenv("GEMINI_MODEL_CLEAN", "gemini-2.5-flash")


SYSTEM_INSTRUCTIONS = (
    "You standardize scraped creepypasta stories into this JSON strictly:\n"
    "{\n"
    "  \"title\": \"clean title (no quotes/escapes)\",\n"
    "  \"author\": \"normalized author or 'Unknown'\",\n"
    "  \"publication_date\": \"ISO-8601 or '' if unknown\",\n"
    "  \"tags\": [\"canonical, kebab-case, deduped, <=12 items\"],\n"
    "  \"content\": \"clean text: no html, no leftover boilerplate\",\n"
    "  \"notes\": \"brief rationale of changes\"\n"
    "}\n"
    "Rules:\n"
    "- Remove HTML artifacts and weird quotes.\n"
    "- Title: dequote, trim, capitalize properly; strip site prefixes/suffixes.\n"
    "- Tags: map synonyms to canonical set (e.g., 'ghosts'->'supernatural', 'ai'->'technology'), lowercase-kebab-case, dedupe.\n"
    "- Dates: parse if obvious; else ''.\n"
    "- Never invent content; only clean.\n"
    "Return ONLY JSON."
)


TAG_SYNONYMS = {
    "ghost": "supernatural",
    "ghosts": "supernatural",
    "spirit": "supernatural",
    "demon": "supernatural",
    "demons": "supernatural",
    "monster": "creature",
    "monsters": "creature",
    "ai": "technology",
    "artificial-intelligence": "technology",
    "sci-fi": "sci-fi",
    "science-fiction": "sci-fi",
    "analog-horror": "analog-horror",
    "urban-legend": "urban-legend",
    "ritual": "occult",
}

_genai = None


def _ensure_genai_configured() -> bool:
    global _genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return False
    try:
        if _genai is None:
            import google.generativeai as genai  # lazy import to avoid hard dependency
            genai.configure(api_key=api_key)
            _genai = genai
        return True
    except Exception:
        return False


def _best_effort_json_parse(text: str) -> Dict[str, Any]:
    text = text.strip() if text else ""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass
    return {}


def _sanitize_content(content: str) -> str:
    """Remove HTML artifacts, control chars, and normalize whitespace."""
    if not content:
        return ""
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text(separator="\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text


def _normalize_tags(tags: List[str]) -> List[str]:
    normalized = []
    for raw in tags or []:
        slug = raw.lower().strip()
        slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
        if not slug:
            continue
        slug = TAG_SYNONYMS.get(slug, slug)
        if slug not in normalized:
            normalized.append(slug)
        if len(normalized) >= 12:
            break
    return normalized


def clean_story_with_gemini(story: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize a scraped story using Gemini. Returns a dict with cleaned fields.

    If GEMINI_API_KEY is not set or model fails, returns a best-effort passthrough.
    """
    if not _ensure_genai_configured():
        return {
            "title": (story.get("title", "") or "").strip().strip('"'),
            "author": story.get("author", "Unknown") or "Unknown",
            "publication_date": story.get("publication_date", "") or "",
            "tags": _normalize_tags(story.get("tags", []) or []),
            "content": _sanitize_content(story.get("content", "") or ""),
            "clean_notes": "GEMINI_API_KEY not configured; heuristic cleanup applied.",
        }

    title = story.get("title", "")
    author = story.get("author", "")
    date = story.get("publication_date", "")
    tags = story.get("tags", [])
    content = story.get("content", "")

    # Cap content length to control costs
    max_chars = 12000
    content_slice = content[:max_chars] if isinstance(content, str) else ""

    prompt = (
        f"Scraped story:\n"
        f"TITLE: {title}\n"
        f"AUTHOR: {author}\n"
        f"DATE: {date}\n"
        f"TAGS: {tags}\n"
        f"CONTENT:\n{content_slice}"
    )

    try:
        if not _ensure_genai_configured():
            raise RuntimeError("Gemini not configured")
        model = _genai.GenerativeModel(MODEL_NAME, system_instruction=SYSTEM_INSTRUCTIONS)
        resp = model.generate_content(prompt)
        text = (resp.text or "").strip()
        cleaned = _best_effort_json_parse(text)
    except Exception as e:
        cleaned = {}
        notes = f"Gemini error: {e}"
    else:
        notes = cleaned.get("notes", "")

    sanitized_content = _sanitize_content(cleaned.get("content") or content or "")
    normalized_tags = _normalize_tags(cleaned.get("tags") or tags or [])

    return {
        "title": (cleaned.get("title") or title or "").strip().strip('"'),
        "author": cleaned.get("author") or author or "Unknown",
        "publication_date": cleaned.get("publication_date") or date or "",
        "tags": normalized_tags,
        "content": sanitized_content,
        "clean_notes": notes or "LLM cleaning applied.",
    }


