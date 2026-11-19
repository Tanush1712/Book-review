import requests
from typing import List, Dict, Optional
from services.database import SessionLocal, Book
import json

OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
OPEN_LIBRARY_WORKS_URL = "https://openlibrary.org"


def search_books_online(query: str, limit: int = 10) -> List[Dict]:
    """Searches Open Library API for books matching the query."""
    if not query or len(query.strip()) < 2:
        return []

    try:
        params = {
            "q": query.strip(),
            "limit": limit,
            "fields": "key,title,subtitle,author_name,first_publish_year,cover_i,isbn,subject,number_of_pages_median,ratings_average,ratings_count"
        }
        response = requests.get(OPEN_LIBRARY_SEARCH_URL, params=params, timeout=7)
        if response.status_code != 200:
            return []

        data = response.json()
        docs = data.get("docs", [])
        results = []

        for item in docs:
            work_key = item.get("key", "").replace("/works/", "")
            title = item.get("title", "Untitled")
            authors = ", ".join(item.get("author_name", ["Unknown Author"]))
            cover_id = item.get("cover_i")
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300"
            
            publish_year = str(item.get("first_publish_year", "N/A"))
            page_count = item.get("number_of_pages_median", 320)
            isbn_list = item.get("isbn", [])
            isbn13 = isbn_list[0] if isbn_list else "N/A"
            subjects = item.get("subject", [])
            genres = ", ".join(subjects[:4]) if subjects else "Fiction, General"
            
            avg_rating = round(float(item.get("ratings_average", 3.9)), 2)
            ratings_count = int(item.get("ratings_count", 150))

            results.append({
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
                "ratings_count": ratings_count
            })

        return results
    except Exception as e:
        print(f"Error fetching from Open Library: {e}")
        return []


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
