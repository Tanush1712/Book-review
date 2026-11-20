import json
from datetime import datetime
from sqlalchemy.orm import Session
from services.database import SessionLocal, init_db, User, Book, Shelf, ShelfItem, Review


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_initialized():
    """Initializes tables and seeds initial data if empty."""
    init_db()
    with SessionLocal() as db:
        user = db.query(User).filter_by(username="tanush_reader").first()
        if not user:
            user = User(
                username="tanush_reader",
                display_name="Tanush (Avid Reader)",
                email="tanush@bookreview.app",
                avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
                bio="Reading is dreaming with open eyes. Lover of thrillers, romance, and thought-provoking mysteries.",
                reading_goal=30
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Create default shelves
            default_shelves = ["Want to Read", "Currently Reading", "Read", "Favorites"]
            for s_name in default_shelves:
                db.add(Shelf(user_id=user.id, name=s_name, is_default=True))
            db.commit()

        # Seed featured book "Never Never" if not present
        never_never = db.query(Book).filter_by(title="Never Never").first()
        if not never_never:
            seed_initial_catalog(db, user)


def seed_initial_catalog(db: Session, demo_user: User):
    """Seeds the catalog with Never Never (from the user link) and companion books."""
    
    # 1. Never Never by Colleen Hoover & Tarryn Fisher (Direct benchmark book)
    never_never = Book(
        open_library_id="OL17930368W",
        title="Never Never",
        subtitle="The Complete Novel",
        authors="Colleen Hoover, Tarryn Fisher",
        series_info="Never Never #1-3",
        isbn13="9781335004888",
        description=(
            "Charlize Wynwood and Silas Nash have been best friends since they could walk "
            "and in love since the age of fourteen. But as of this morning... they are complete "
            "strangers. Their first kiss, their first fight, the moment they fell in love... "
            "every memory has vanished.\n\n"
            "Now Silas and Charlie must work together to uncover who they were and why they woke "
            "up with no memories. But the more they learn about the couple they used to be, "
            "the more they question why they were ever together to begin with. Forgetting is terrifying, "
            "but remembering may be worse."
        ),
        cover_image_url="https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1666887550i/63120226.jpg",
        page_count=416,
        publisher="Canary Street Press",
        publish_year="2023",
        genres="Romance, Mystery, Young Adult, Contemporary, Thriller, New Adult",
        average_rating=3.85,
        ratings_count=142500,
        reviews_count=12400,
        rating_breakdown_json=json.dumps({
            "5": 64125,
            "4": 39900,
            "3": 21375,
            "2": 9975,
            "1": 7125
        })
    )
    db.add(never_never)
    db.flush()

    # Seed companion books for "Readers Also Enjoyed"
    companions = [
        Book(
            open_library_id="OL20042456W",
            title="Verity",
            authors="Colleen Hoover",
            series_info=None,
            isbn13="9781538724736",
            description="Lowen Ashleigh is a struggling writer on the brink of financial ruin when she accepts the job offer of a lifetime.",
            cover_image_url="https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1634158558i/59344312.jpg",
            page_count=336,
            publisher="Grand Central Publishing",
            publish_year="2018",
            genres="Thriller, Mystery, Romance, Psychological Thriller",
            average_rating=4.34,
            ratings_count=2150000,
            reviews_count=182000,
            rating_breakdown_json=json.dumps({"5": 1180000, "4": 620000, "3": 210000, "2": 85000, "1": 55000})
        ),
        Book(
            open_library_id="OL17930800W",
            title="It Ends with Us",
            authors="Colleen Hoover",
            series_info="It Ends with Us #1",
            isbn13="9781501110368",
            description="Lily hasn't always had it easy, but that's never stopped her from working hard for the life she wants.",
            cover_image_url="https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1688011813i/27362503.jpg",
            page_count=384,
            publisher="Atria Books",
            publish_year="2016",
            genres="Romance, Contemporary, New Adult, Drama",
            average_rating=4.14,
            ratings_count=3200000,
            reviews_count=295000,
            rating_breakdown_json=json.dumps({"5": 1650000, "4": 920000, "3": 390000, "2": 140000, "1": 100000})
        ),
        Book(
            open_library_id="OL19623835W",
            title="The Seven Husbands of Evelyn Hugo",
            authors="Taylor Jenkins Reid",
            series_info=None,
            isbn13="9781501161933",
            description="Aging and reclusive Hollywood movie icon Evelyn Hugo is finally ready to tell the truth about her glamorous and scandalous life.",
            cover_image_url="https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1664458703i/32620332.jpg",
            page_count=400,
            publisher="Atria Books",
            publish_year="2017",
            genres="Historical Fiction, LGBTQ+, Romance, Drama",
            average_rating=4.42,
            ratings_count=2780000,
            reviews_count=264000,
            rating_breakdown_json=json.dumps({"5": 1620000, "4": 810000, "3": 240000, "2": 70000, "1": 40000})
        ),
        Book(
            open_library_id="OL20845341W",
            title="Love and Other Words",
            authors="Christina Lauren",
            series_info=None,
            isbn13="9781501128011",
            description="The story of a heartbroken woman who reunites with the love of her life, and the secret that drove them apart.",
            cover_image_url="https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1511211186i/36206591.jpg",
            page_count=432,
            publisher="Gallery Books",
            publish_year="2018",
            genres="Romance, Contemporary, Fiction",
            average_rating=4.28,
            ratings_count=520000,
            reviews_count=48000,
            rating_breakdown_json=json.dumps({"5": 280000, "4": 150000, "3": 62000, "2": 18000, "1": 10000})
        )
    ]
    for b in companions:
        db.add(b)
    db.flush()

    # Seed realistic community reviews for Never Never
    dummy_reviews = [
        (
            5.0,
            "I could not put this book down! The mystery of Silas and Charlie waking up with complete amnesia kept me turning pages all night. The alternating POV between Colleen Hoover and Tarryn Fisher is brilliant—you can definitely feel their distinct voices complementing each other.",
            False,
            412
        ),
        (
            4.0,
            "A fast-paced, addictive read. Silas is absolute boyfriend material even with zero memories. Note on the ending:\n\nSilas and Charlie finding the letters in the safe was such an emotional climax! The supernatural undertone with the Tarot cards wasn't 100% explained, but the romance made up for it.",
            True,
            189
        ),
        (
            4.5,
            "Read this in a single sitting! If you love suspense mixed with intense emotional chemistry, this is for you. Silas writing notes to his future self gave me all the feels.",
            False,
            97
        ),
        (
            3.0,
            "Good concept, but the middle drag was real. I loved Part 1 the most. Part 3 felt slightly rushed to tie all the memory-loss loose ends together. Still worth a read if you're a CoHo or Tarryn Fisher fan.",
            False,
            54
        )
    ]

    for rating, text, spoilers, likes in dummy_reviews:
        db.add(Review(
            book_id=never_never.id,
            user_id=demo_user.id,
            rating=rating,
            review_text=text,
            contains_spoilers=spoilers,
            likes_count=likes
        ))

    # Add Never Never to demo user's "Currently Reading" shelf
    curr_shelf = db.query(Shelf).filter_by(user_id=demo_user.id, name="Currently Reading").first()
    if curr_shelf:
        db.add(ShelfItem(
            shelf_id=curr_shelf.id,
            book_id=never_never.id,
            user_id=demo_user.id,
            user_rating=4.0
        ))

    # Add Verity to "Read" shelf
    verity = db.query(Book).filter_by(title="Verity").first()
    read_shelf = db.query(Shelf).filter_by(user_id=demo_user.id, name="Read").first()
    if verity and read_shelf:
        db.add(ShelfItem(
            shelf_id=read_shelf.id,
            book_id=verity.id,
            user_id=demo_user.id,
            user_rating=5.0
        ))

    db.commit()


# --- Book Operations ---

def get_book(book_id: int):
    with SessionLocal() as db:
        return db.query(Book).filter(Book.id == book_id).first()


def get_all_books(limit: int = 50):
    with SessionLocal() as db:
        return db.query(Book).limit(limit).all()


def search_local_books(query_str: str):
    with SessionLocal() as db:
        search_pattern = f"%{query_str}%"
        return db.query(Book).filter(
            (Book.title.ilike(search_pattern)) |
            (Book.authors.ilike(search_pattern)) |
            (Book.genres.ilike(search_pattern)) |
            (Book.isbn13.ilike(search_pattern))
        ).all()


def get_reviews_for_book(book_id: int, star_filter: float = None, sort_by: str = "Most Helpful"):
    with SessionLocal() as db:
        q = db.query(Review, User).join(User, Review.user_id == User.id).filter(Review.book_id == book_id)
        if star_filter is not None and star_filter > 0:
            q = q.filter(Review.rating >= star_filter, Review.rating < star_filter + 1.0)
        
        if sort_by == "Most Helpful":
            q = q.order_by(Review.likes_count.desc(), Review.created_at.desc())
        elif sort_by == "Newest":
            q = q.order_by(Review.created_at.desc())
        elif sort_by == "Highest Rating":
            q = q.order_by(Review.rating.desc(), Review.created_at.desc())
        elif sort_by == "Lowest Rating":
            q = q.order_by(Review.rating.asc(), Review.created_at.desc())
            
        results = q.all()
        # Return list of dicts for clean consumption
        return [
            {
                "id": r.Review.id,
                "rating": r.Review.rating,
                "review_text": r.Review.review_text,
                "contains_spoilers": r.Review.contains_spoilers,
                "likes_count": r.Review.likes_count,
                "created_at": r.Review.created_at,
                "user_name": r.User.display_name,
                "user_avatar": r.User.avatar_url
            }
            for r in results
        ]


def add_review(book_id: int, user_id: int, rating: float, text: str, contains_spoilers: bool):
    with SessionLocal() as db:
        review = Review(
            book_id=book_id,
            user_id=user_id,
            rating=rating,
            review_text=text,
            contains_spoilers=contains_spoilers,
            likes_count=0
        )
        db.add(review)

        # Update book average rating and breakdown
        book = db.query(Book).filter_by(id=book_id).first()
        if book:
            breakdown = book.get_rating_breakdown()
            star_key = str(int(round(rating)))
            if star_key in breakdown:
                breakdown[star_key] += 1
            else:
                breakdown[star_key] = 1
            book.set_rating_breakdown(breakdown)
            
            book.ratings_count += 1
            book.reviews_count += 1
            # Recalculate average
            total_sum = sum(int(k) * v for k, v in breakdown.items())
            total_count = sum(breakdown.values())
            if total_count > 0:
                book.average_rating = round(total_sum / total_count, 2)
        
        db.commit()
        return True


def like_review(review_id: int):
    with SessionLocal() as db:
        rev = db.query(Review).filter_by(id=review_id).first()
        if rev:
            rev.likes_count += 1
            db.commit()
            return rev.likes_count
        return 0


# --- Shelving Operations ---

def get_current_user():
    import streamlit as st
    user_id = st.session_state.get("logged_in_user_id")
    with SessionLocal() as db:
        if user_id:
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                return user
        return db.query(User).filter_by(username="tanush_reader").first() or db.query(User).first()


def get_user_shelves_with_counts(user_id: int):
    with SessionLocal() as db:
        shelves = db.query(Shelf).filter_by(user_id=user_id).all()
        result = []
        for s in shelves:
            count = db.query(ShelfItem).filter_by(shelf_id=s.id).count()
            result.append({"id": s.id, "name": s.name, "count": count})
        return result


def get_book_shelf_status(user_id: int, book_id: int):
    """Returns shelf name if book is shelved, else None."""
    with SessionLocal() as db:
        item = db.query(ShelfItem).filter_by(user_id=user_id, book_id=book_id).first()
        if item:
            shelf = db.query(Shelf).filter_by(id=item.shelf_id).first()
            return shelf.name if shelf else None
        return None


def set_book_shelf(user_id: int, book_id: int, target_shelf_name: str):
    """Moves book to target shelf, or removes if 'None'."""
    with SessionLocal() as db:
        # Delete existing shelf entry for this book
        db.query(ShelfItem).filter_by(user_id=user_id, book_id=book_id).delete()
        
        if target_shelf_name and target_shelf_name != "Remove from Shelves":
            shelf = db.query(Shelf).filter_by(user_id=user_id, name=target_shelf_name).first()
            if not shelf:
                shelf = Shelf(user_id=user_id, name=target_shelf_name)
                db.add(shelf)
                db.flush()
            
            db.add(ShelfItem(shelf_id=shelf.id, book_id=book_id, user_id=user_id))
        
        db.commit()


def get_shelved_books(user_id: int, shelf_name: str = "All"):
    with SessionLocal() as db:
        if shelf_name == "All":
            items = db.query(ShelfItem, Book, Shelf).join(Book, ShelfItem.book_id == Book.id).join(Shelf, ShelfItem.shelf_id == Shelf.id).filter(ShelfItem.user_id == user_id).all()
        else:
            items = db.query(ShelfItem, Book, Shelf).join(Book, ShelfItem.book_id == Book.id).join(Shelf, ShelfItem.shelf_id == Shelf.id).filter(ShelfItem.user_id == user_id, Shelf.name == shelf_name).all()
        
        return [
            {
                "book_id": item.Book.id,
                "title": item.Book.title,
                "authors": item.Book.authors,
                "cover_url": item.Book.cover_image_url,
                "average_rating": item.Book.average_rating,
                "shelf_name": item.Shelf.name,
                "user_rating": item.ShelfItem.user_rating,
                "added_at": item.ShelfItem.added_at
            }
            for item in items
        ]
