import requests
from typing import List, Dict, Optional
from services.database import SessionLocal, Book
from services.genre_utils import (
    clean_genres_display,
    extract_query_genres,
    parse_book_genres,
    score_genre_match,
)
import json

OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
OPEN_LIBRARY_WORKS_URL = "https://openlibrary.org"
SEARCH_FIELDS = (
    "key,title,subtitle,author_name,first_publish_year,cover_i,"
    "isbn,subject,number_of_pages_median,ratings_average,ratings_count"
)


def _doc_to_book_dict(item: Dict) -> Dict:
    """Normalizes a raw Open Library search doc into the app's standard dict format."""
    work_key = item.get("key", "").replace("/works/", "")
    title = item.get("title", "Untitled")
    authors = ", ".join(item.get("author_name", ["Unknown Author"]))
    cover_id = item.get("cover_i")
    cover_url = (
        f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        if cover_id
        else "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300"
    )

    publish_year = str(item.get("first_publish_year", "N/A"))
    page_count = item.get("number_of_pages_median", 320)
    isbn_list = item.get("isbn", [])
    isbn13 = isbn_list[0] if isbn_list else "N/A"
    subjects = item.get("subject", [])
    genres = clean_genres_display(subjects, limit=5)

    avg_rating = round(float(item.get("ratings_average", 3.9)), 2)
    ratings_count = int(item.get("ratings_count", 150))

    return {
        "open_library_id": work_key,
        "title": title,
        "subtitle": item.get("subtitle"),
        "authors": authors,
        "publish_year": publish_year,
        "cover_url": cover_url,
        "page_count": page_count,
        "isbn13": isbn13,
        "genres": genres,
        "average_rating": avg_rating,
        "ratings_count": ratings_count,
        "_raw_subjects": subjects,
    }


def _fetch_open_library_docs(params: Dict) -> List[Dict]:
    """Executes a single Open Library /search.json request safely."""
    try:
        req_params = {**params, "fields": SEARCH_FIELDS}
        response = requests.get(OPEN_LIBRARY_SEARCH_URL, params=req_params, timeout=7)
        if response.status_code != 200:
            return []
        return response.json().get("docs", [])
    except Exception as e:
        print(f"Error fetching from Open Library: {e}")
        return []


def _search_genres_online(query_genres: List[str], raw_query: str, limit: int) -> List[Dict]:
    """Queries Open Library specifically by subject for single and multi-genre searches."""
    collected: Dict[str, Dict] = {}

    def _add_docs(docs: List[Dict]):
        for doc in docs:
            book = _doc_to_book_dict(doc)
            dedup_key = book["open_library_id"] or book["title"].lower().strip()
            if dedup_key and dedup_key not in collected:
                collected[dedup_key] = book

    if len(query_genres) == 1:
        g = query_genres[0]
        docs = _fetch_open_library_docs({"subject": g, "limit": max(limit * 2, 16)})
        if not docs:
            docs = _fetch_open_library_docs({"q": f'subject:"{g}"', "limit": max(limit * 2, 16)})
        if not docs:
            docs = _fetch_open_library_docs({"q": g, "limit": limit})
        _add_docs(docs)
    else:
        # Try combined subject query first so books matching multiple genres appear first
        combined_q = " ".join(f'subject:"{g}"' for g in query_genres)
        _add_docs(_fetch_open_library_docs({"q": combined_q, "limit": max(limit, 12)}))

        # Supplement with per-genre subject queries if needed
        if len(collected) < limit:
            per_genre_limit = max(6, (limit // len(query_genres)) + 4)
            for g in query_genres:
                _add_docs(_fetch_open_library_docs({"subject": g, "limit": per_genre_limit}))

        if not collected:
            _add_docs(_fetch_open_library_docs({"q": " ".join(query_genres), "limit": limit}))

    # Score and rank results by how many requested genres they match
    ranked = []
    for book in collected.values():
        subject_tokens = parse_book_genres(", ".join(book.pop("_raw_subjects", []) or []))
        if not subject_tokens:
            subject_tokens = parse_book_genres(book.get("genres", ""))

        matched_count = 0
        genre_score = 0
        for qg in query_genres:
            s = score_genre_match(qg, subject_tokens)
            if s > 0:
                matched_count += 1
                genre_score += s

        ranked.append((matched_count, genre_score, book.get("ratings_count", 0), book))

    ranked.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    return [item[3] for item in ranked[:limit]]


def search_books_online(query: str, limit: int = 10) -> List[Dict]:
    """Searches Open Library API for books matching a title, author, ISBN, or genre query."""
    if not query or len(query.strip()) < 2:
        return []

    raw_query = query.strip()
    query_genres, is_genre_query = extract_query_genres(raw_query)

    if is_genre_query and query_genres:
        return _search_genres_online(query_genres, raw_query, limit)

    docs = _fetch_open_library_docs({"q": raw_query, "limit": limit})
    results = []
    for item in docs:
        book = _doc_to_book_dict(item)
        book.pop("_raw_subjects", None)
        results.append(book)
    return results


def import_book_to_db(book_dict: Dict) -> Optional[int]:
    """Saves an online book into the local database and returns the new or existing book ID."""
    with SessionLocal() as db:
        # Check by open_library_id or title
        existing = None
        if book_dict.get("open_library_id"):
            existing = db.query(Book).filter_by(open_library_id=book_dict["open_library_id"]).first()
        if not existing and book_dict.get("title"):
            existing = db.query(Book).filter(Book.title.ilike(book_dict["title"])).first()

        if existing:
            return existing.id

        # Fetch full description from Open Library if available
        description = "A captivating read loved by readers across the globe. Explore the characters, unravel the plot, and join the community discussion."
        try:
            if book_dict.get("open_library_id"):
                work_res = requests.get(f"{OPEN_LIBRARY_WORKS_URL}/works/{book_dict['open_library_id']}.json", timeout=5)
                if work_res.status_code == 200:
                    work_data = work_res.json()
                    desc_obj = work_data.get("description")
                    if isinstance(desc_obj, dict):
                        description = desc_obj.get("value", description)
                    elif isinstance(desc_obj, str):
                        description = desc_obj
        except Exception:
            pass

        # Build initial rating breakdown
        ratings_count = book_dict.get("ratings_count", 250) or 250
        breakdown = {
            "5": int(ratings_count * 0.45),
            "4": int(ratings_count * 0.30),
            "3": int(ratings_count * 0.15),
            "2": int(ratings_count * 0.07),
            "1": int(ratings_count * 0.03)
        }

        new_book = Book(
            open_library_id=book_dict.get("open_library_id"),
            title=book_dict["title"],
            subtitle=book_dict.get("subtitle"),
            authors=book_dict.get("authors", "Unknown"),
            isbn13=book_dict.get("isbn13"),
            description=description,
            cover_image_url=book_dict.get("cover_url"),
            page_count=book_dict.get("page_count", 320),
            publisher=book_dict.get("publisher", "Independent Publisher"),
            publish_year=book_dict.get("publish_year", "2022"),
            genres=book_dict.get("genres", "Fiction, Literature"),
            average_rating=book_dict.get("average_rating", 4.0),
            ratings_count=ratings_count,
            reviews_count=max(5, int(ratings_count * 0.08)),
            rating_breakdown_json=json.dumps(breakdown)
        )
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        return new_book.id
