import os
import json
import requests
from typing import Generator, List, Dict, Optional
import streamlit as st
from services.database import Book, User
from services.db_operations import (
    get_shelved_books,
    get_all_books,
    get_book,
    get_reviews_for_book,
)

DEFAULT_GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
DEFAULT_MODEL = "qwen/qwen3.8-27b"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def get_api_key() -> str:
    """Retrieves the Groq API key from Streamlit secrets, session state, or env."""
    # 1. Session state override
    if "custom_groq_api_key" in st.session_state and st.session_state["custom_groq_api_key"]:
        return st.session_state["custom_groq_api_key"].strip()

    # 2. Streamlit secrets
    try:
        if "GROQ_API_KEY" in st.secrets and st.secrets["GROQ_API_KEY"]:
            return st.secrets["GROQ_API_KEY"].strip()
    except Exception:
        pass

    # 3. Environment variable
    env_key = os.environ.get("GROQ_API_KEY")
    if env_key:
        return env_key.strip()

    # 4. Fallback default key
    return DEFAULT_GROQ_KEY


def build_reader_context(user: Optional[User]) -> str:
    """Extracts reader profile and bookshelf data to inject as context for the assistant."""
    if not user:
        return "The reader is browsing as a guest."

    context_parts = [
        f"Reader: {user.display_name} (@{user.username}) | Annual Goal: {user.reading_goal} books"
    ]

    try:
        shelved = get_shelved_books(user.id, shelf_name="All")
        if shelved:
            by_shelf: Dict[str, List[str]] = {}
            for item in shelved:
                shelf = item.get("shelf_name", "General")
                title = item.get("title", "Unknown")
                authors = item.get("authors", "")
                rating_info = f" ({item['user_rating']}★)" if item.get("user_rating") else ""
                by_shelf.setdefault(shelf, []).append(f"'{title}' by {authors}{rating_info}")

            shelf_summaries = [
                f"- {s_name}: {', '.join(book_list[:6])}"
                for s_name, book_list in by_shelf.items()
            ]
            context_parts.append("Bookshelves:\n" + "\n".join(shelf_summaries))
    except Exception:
        pass

    try:
        catalog = get_all_books()[:8]
        if catalog:
            cat_list = [f"'{b.title}' by {b.authors} [{b.genres}]" for b in catalog]
            context_parts.append("Catalog Books:\n- " + "\n- ".join(cat_list))
    except Exception:
        pass

    return "\n".join(context_parts)


def _format_single_book_context(book: Book, label: str) -> str:
    """Formats a book's metadata, full synopsis, and top community reviews for prompt injection."""
    lines = [
        f"[{label}]",
        f"Title: {book.title}" + (f" ({book.subtitle})" if book.subtitle else ""),
        f"Author(s): {book.authors}",
    ]
    if book.series_info:
        lines.append(f"Series: {book.series_info}")
    lines.append(f"Genres: {book.genres or 'Unknown'}")
    lines.append(
        f"Published: {book.publish_year or 'Unknown'} | Pages: {book.page_count or 'Unknown'} | "
        f"Rating: {book.average_rating:.2f}/5 ({book.ratings_count:,} ratings)"
    )

    desc = (book.description or "").strip()
    if desc:
        lines.append(f"Synopsis: {desc[:1500]}")
    else:
        lines.append("Synopsis: Not available in the database.")

    try:
        reviews = get_reviews_for_book(book.id, sort_by="Most Helpful")[:4]
        if reviews:
            rev_lines = []
            for r in reviews:
                tag = "[SPOILER] " if r.get("contains_spoilers") else ""
                snippet = (r.get("review_text") or "").strip().replace("\n", " ")[:260]
                rev_lines.append(f"- {r.get('rating')}★ {tag}{snippet}")
            lines.append("Community Reviews:\n" + "\n".join(rev_lines))
        else:
            lines.append("Community Reviews: None yet.")
    except Exception:
        pass

    return "\n".join(lines)


def build_book_context(
    book_id: Optional[int] = None,
    messages: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Collects rich, factual context for the selected book and any catalog books
    explicitly referenced in recent user messages.
    """
    blocks: List[str] = []
    included_ids = set()

    if book_id:
        try:
            selected = get_book(book_id)
            if selected:
                blocks.append(_format_single_book_context(selected, "SELECTED BOOK"))
                included_ids.add(selected.id)
        except Exception:
            pass

    if messages:
        recent_user_text = " ".join(
            m.get("content", "")
            for m in messages[-4:]
            if m.get("role") == "user"
        ).lower()
        if recent_user_text:
            try:
                for b in get_all_books(limit=50):
                    if b.id in included_ids:
                        continue
                    title_clean = (b.title or "").strip().lower()
                    if len(title_clean) >= 3 and title_clean in recent_user_text:
                        blocks.append(_format_single_book_context(b, "REFERENCED BOOK"))
                        included_ids.add(b.id)
                        if len(blocks) >= 3:
                            break
            except Exception:
                pass

    if not blocks:
        return "No specific book is currently selected."

    return "\n\n".join(blocks)


def build_system_prompt(
    user: Optional[User],
    book_id: Optional[int] = None,
    messages: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Constructs a concise, book-specific, opinionated literary prompt for BookLover AI."""
    reader_info = build_reader_context(user)
    book_context = build_book_context(book_id=book_id, messages=messages)

    return f"""You are BookLover AI, a sharp, direct, opinionated literary critic and reading companion inside the BookLover app.

BOOK CONTEXT (USE THIS FIRST):
{book_context}

READER PROFILE:
{reader_info}

CORE RULES — BOOK SPECIFICITY & HONESTY:
1. Be direct, insightful, and opinionated. Take a real stance on what works, what falls flat, and who should skip or read it. Never give diplomatic, generic, or fence-sitting answers.
2. Talk about the actual book: name real characters, dynamics, plot setups, themes, and pacing details from the BOOK CONTEXT above and your verified knowledge of that book.
3. If the user says "this book" or asks about the SELECTED BOOK, anchor your answer in that book. Ignore SELECTED BOOK if the user clearly asks about a different book or general recommendations.
4. NEVER fabricate character names, plot events, twists, quotes, or facts. If the BOOK CONTEXT lacks details (e.g., missing synopsis/reviews) and you don't reliably know the book's actual plot or characters, say plainly what you don't have enough info to verify instead of guessing or padding.
5. Don't spoil major ending twists unless the user explicitly asks for spoilers or ending details.

CORE RULES — BREVITY & CONVERSATIONAL STYLE:
1. Word budget: aim for 40–70 words for normal questions; NEVER exceed 120 words even for complex questions or multi-book recommendations.
2. Answer the question in the very first sentence.
3. Zero fluff: no greetings, no "Great question!", no intros, no disclaimers, no repeating the user's question, no sign-offs, and no describing book covers.
4. Write naturally and conversationally. Use at most 2–3 short bullets only if comparing/listing multiple books.
5. Format book titles in *italics* with the author on first mention (e.g., *Never Never* by Colleen Hoover and Tarryn Fisher) so the app can render cover cards.
"""


def stream_chat_completion(
    messages: List[Dict[str, str]],
    user: Optional[User] = None,
    book_id: Optional[int] = None,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7
) -> Generator[str, None, None]:
    """Streams response tokens from Groq API in real-time."""
    key = api_key or get_api_key()
    if not key:
        yield "⚠️ **Error:** No API key detected. Please configure your Groq API key in the sidebar."
        return

    system_prompt = build_system_prompt(user, book_id=book_id, messages=messages)
    formatted_messages = [{"role": "system", "content": system_prompt}] + messages

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": formatted_messages,
        "temperature": temperature,
        "max_tokens": 800,
        "stream": True
    }

    try:
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=40
        )

        if response.status_code != 200:
            err_msg = response.text
            try:
                err_json = response.json()
                err_msg = err_json.get("error", {}).get("message", response.text)
            except Exception:
                pass
            yield f"⚠️ **Groq API Error ({response.status_code}):** {err_msg}"
            return

        for line in response.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    data_str = decoded[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    except requests.exceptions.Timeout:
        yield "⏳ **Request Timed Out:** Groq took too long to reply. Please try asking again."
    except requests.exceptions.RequestException as e:
        yield f"🚨 **Network Connection Error:** Could not connect to Groq API ({e})."


def get_quick_prompts() -> List[Dict[str, str]]:
    """Sample curated prompt prompts for the chat chips."""
    return [
        {
            "label": "🎯 Recommend Next Read",
            "prompt": "Based on my current bookshelves and favorites, what should I read next and why?"
        },
        {
            "label": "🔥 Similar to 'Never Never'",
            "prompt": "I loved 'Never Never' by Colleen Hoover & Tarryn Fisher. Recommend 3 books with a similar fast-paced psychological mystery or romantic tension."
        },
        {
            "label": "⚡ Short Weekend Reads",
            "prompt": "Give me 3 gripping books under 350 pages that I can read in a single weekend."
        },
        {
            "label": "🤐 Spoiler-Free Analysis",
            "prompt": "Can you give me a spoiler-free overview of the themes, tropes, and trigger warnings in 'The Seven Husbands of Evelyn Hugo'?"
        }
    ]
