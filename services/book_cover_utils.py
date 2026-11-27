import re
import requests
from typing import List, Dict, Optional, Tuple
from services.database import SessionLocal, Book

OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"

SKIP_PREFIXES = (
    'Note', 'Warning', 'Spoiler', 'Trigger', 'Content', 'Why', 'How',
    'What', 'When', 'Where', 'Tip', 'Example', 'Key', 'Themes', 'Tropes',
    'Books Mentioned', 'Disclaimer', 'Important'
)


def _extract_title_author_pairs(text: str) -> List[Tuple[str, Optional[str]]]:
    """Extracts (title, optional_author) pairs from markdown/prose text."""
    pairs: List[Tuple[str, Optional[str]]] = []
    if not text:
        return pairs

    # 1. *Title* by Author  or  **Title** by Author
    md_by_pattern = r'(?:\*{1,2})([A-Z][^*\n]{1,65}?)(?:\*{1,2})\s+by\s+([A-Z][A-Za-z.\'\-\s&]{1,45}?)(?=[.,;!\?\n\)]|$)'
    for title, author in re.findall(md_by_pattern, text):
        t_clean = title.strip(" *'\"")
        a_clean = author.strip(" .,;:")
        if len(t_clean) > 2 and not t_clean.startswith(SKIP_PREFIXES):
            pairs.append((t_clean, a_clean))

    # 2. *Book Title* (single asterisk italics)
    italic_pattern = r'(?<!\*)\*([A-Z][^*\n]{2,60})\*(?!\*)'
    for match in re.findall(italic_pattern, text):
        clean = match.strip(" *'\"")
        if len(clean) > 2 and not clean.startswith(SKIP_PREFIXES):
            pairs.append((clean, None))

    # 3. 'Title' by Author or "Title" by Author
    quote_by_pattern = r"""['"\u201c\u201d]([A-Z][^'"\u201c\u201d\n]{2,60})['"\u201c\u201d]\s+by\s+([A-Z][A-Za-z.\'\-\s&]{1,45}?)(?=[.,;!\?\n\)]|$)"""
    for title, author in re.findall(quote_by_pattern, text):
        t_clean = title.strip()
        a_clean = author.strip(" .,;:")
        if len(t_clean) > 2:
            pairs.append((t_clean, a_clean))

    # 4. Plain "Title by Author" in short user queries (e.g. "Fallen Rook by L.J. Shen")
    plain_by_pattern = r'(?:cover\s+(?:of|for)\s+|about\s+|book\s+)?([A-Z][A-Za-z0-9:\'\-\s]{1,50}?)\s+by\s+([A-Z][A-Za-z.\'\-\s&]{1,40}?)(?=[.,;!\?\n]|$)'
    for title, author in re.findall(plain_by_pattern, text):
        t_clean = title.strip(" *'\"")
        # Remove leading conversational words if captured
        t_clean = re.sub(r'^(?:Show me|Find|Search for|Cover of|Book|Read)\s+', '', t_clean, flags=re.IGNORECASE).strip()
        a_clean = author.strip(" .,;:")
        if 2 < len(t_clean) <= 55 and not t_clean.startswith(SKIP_PREFIXES):
            pairs.append((t_clean, a_clean))

    # Deduplicate while preferring entries that include an author
    merged: Dict[str, Tuple[str, Optional[str]]] = {}
    for title, author in pairs:
        key = title.lower().strip()
        if key not in merged or (merged[key][1] is None and author is not None):
            merged[key] = (title, author)

    return list(merged.values())[:6]


def extract_book_titles(text: str) -> List[str]:
    """Extracts unique book titles from text."""
    return [title for title, _ in _extract_title_author_pairs(text)]


def _lookup_local_book(title: str) -> Optional[Dict]:
    """Checks the local SQLite database for a matching book with a cover image."""
    try:
        with SessionLocal() as db:
            book = db.query(Book).filter(Book.title.ilike(title)).first()
            if not book:
                book = db.query(Book).filter(Book.title.ilike(f"%{title}%")).first()
            if book and book.cover_image_url:
                return {
                    "book_id": book.id,
                    "open_library_id": book.open_library_id,
                    "title": book.title,
                    "search_title": title,
                    "authors": book.authors,
                    "cover_url": book.cover_image_url,
                    "open_library_url": f"https://openlibrary.org/works/{book.open_library_id}" if book.open_library_id else "",
                    "year": str(book.publish_year or ""),
                    "average_rating": book.average_rating,
                    "page_count": book.page_count,
                    "genres": book.genres,
                }
    except Exception:
        pass
    return None


def _search_open_library(title: str, author: Optional[str] = None) -> Optional[Dict]:
    """Searches Open Library with title/author and falls back to title-only search."""
    search_attempts = []
    if author:
        search_attempts.append({"title": title, "author": author, "limit": 3})
    search_attempts.append({"q": title, "limit": 5})

    fields = "key,title,subtitle,author_name,first_publish_year,cover_i,isbn,subject,number_of_pages_median,ratings_average,ratings_count"

    for params in search_attempts:
        try:
            req_params = {**params, "fields": fields}
            response = requests.get(OPEN_LIBRARY_SEARCH_URL, params=req_params, timeout=5)
            if response.status_code != 200:
                continue

            docs = response.json().get("docs", [])
            if not docs:
                continue

            # Prefer docs with a cover_i and matching author if available
            author_lower = author.lower().replace(".", "") if author else ""
            best_doc = None
            for doc in docs:
                if not doc.get("cover_i"):
                    continue
                doc_authors = " ".join(doc.get("author_name", [])).lower().replace(".", "")
                if author_lower and any(part in doc_authors for part in author_lower.split() if len(part) > 2):
                    best_doc = doc
                    break
                if best_doc is None:
                    best_doc = doc

            if best_doc and best_doc.get("cover_i"):
                cover_id = best_doc["cover_i"]
                work_key = best_doc.get("key", "").replace("/works/", "")
                isbn_list = best_doc.get("isbn", [])
                subjects = best_doc.get("subject", [])
                return {
                    "book_id": None,
                    "open_library_id": work_key,
                    "title": best_doc.get("title", title),
                    "subtitle": best_doc.get("subtitle"),
                    "search_title": title,
                    "authors": ", ".join(best_doc.get("author_name", [author or "Unknown Author"])[:2]),
                    "cover_url": f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg",
                    "open_library_url": f"https://openlibrary.org/works/{work_key}" if work_key else "",
                    "year": str(best_doc.get("first_publish_year", "")),
                    "publish_year": str(best_doc.get("first_publish_year", "N/A")),
                    "page_count": best_doc.get("number_of_pages_median", 320),
                    "isbn13": isbn_list[0] if isbn_list else "N/A",
                    "genres": ", ".join(subjects[:4]) if subjects else "Fiction",
                    "average_rating": round(float(best_doc.get("ratings_average", 4.0)), 2),
                    "ratings_count": int(best_doc.get("ratings_count", 150)),
                }
        except Exception:
            continue

    return None


def fetch_book_covers(pairs: List[Tuple[str, Optional[str]]]) -> List[Dict]:
    """Fetches book cover metadata from local DB or Open Library for (title, author) pairs."""
    results = []
    seen_titles = set()

    for title, author in pairs:
        match = _lookup_local_book(title) or _search_open_library(title, author)
        if match and match.get("cover_url"):
            norm_title = match["title"].lower().strip()
            if norm_title not in seen_titles:
                seen_titles.add(norm_title)
                results.append(match)

    return results


def get_book_covers_from_response(ai_response_text: str, user_prompt: str = "") -> List[Dict]:
    """Extracts book titles from the AI response (and user prompt) and fetches their covers."""
    pairs = _extract_title_author_pairs(ai_response_text)
    if user_prompt:
        existing = {t.lower() for t, _ in pairs}
        for title, author in _extract_title_author_pairs(user_prompt):
            if title.lower() not in existing:
                pairs.append((title, author))
    if not pairs:
        return []
    return fetch_book_covers(pairs[:6])
