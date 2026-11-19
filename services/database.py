import os
import json
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Path to database file
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "bookstore.db")
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    avatar_url = Column(String(500), default="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150")
    bio = Column(Text, default="Passionate bookworm & avid reader 📚")
    reading_goal = Column(Integer, default=30)  # Annual reading challenge goal
    created_at = Column(DateTime, default=datetime.utcnow)

    shelves = relationship("Shelf", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    shelf_items = relationship("ShelfItem", back_populates="user", cascade="all, delete-orphan")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    open_library_id = Column(String(100), unique=True, index=True, nullable=True)
    title = Column(String(255), nullable=False, index=True)
    subtitle = Column(String(255), nullable=True)
    authors = Column(String(255), nullable=False, index=True)  # e.g., "Colleen Hoover, Tarryn Fisher"
    series_info = Column(String(255), nullable=True)           # e.g., "Never Never #1-3"
    isbn13 = Column(String(20), nullable=True, index=True)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    page_count = Column(Integer, default=350)
    publisher = Column(String(150), nullable=True)
    publish_year = Column(String(20), default="2023")
    genres = Column(String(255), default="Fiction, Romance, Mystery")  # Comma separated
    average_rating = Column(Float, default=4.0)
    ratings_count = Column(Integer, default=0)
    reviews_count = Column(Integer, default=0)
    rating_breakdown_json = Column(Text, default='{"5": 50, "4": 30, "3": 12, "2": 5, "1": 3}')

    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")
    shelf_items = relationship("ShelfItem", back_populates="book", cascade="all, delete-orphan")

    def get_rating_breakdown(self):
        try:
            return json.loads(self.rating_breakdown_json)
        except Exception:
            return {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}

    def set_rating_breakdown(self, breakdown_dict):
        self.rating_breakdown_json = json.dumps(breakdown_dict)


class Shelf(Base):
    __tablename__ = "shelves"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)  # "Want to Read", "Currently Reading", "Read", or custom
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="shelves")
    items = relationship("ShelfItem", back_populates="shelf", cascade="all, delete-orphan")


class ShelfItem(Base):
    __tablename__ = "shelf_items"

    id = Column(Integer, primary_key=True, index=True)
    shelf_id = Column(Integer, ForeignKey("shelves.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_rating = Column(Float, nullable=True)  # User's personal rating (1.0 to 5.0)
    notes = Column(Text, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)

    shelf = relationship("Shelf", back_populates="items")
    book = relationship("Book", back_populates="shelf_items")
    user = relationship("User", back_populates="shelf_items")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Float, nullable=False)  # 1.0 to 5.0 (supports half stars)
    review_text = Column(Text, nullable=False)
    contains_spoilers = Column(Boolean, default=False)
    likes_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("Book", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


def init_db():
    Base.metadata.create_all(bind=engine)
