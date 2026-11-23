import os
import json
import requests
from typing import Generator, List, Dict, Optional
import streamlit as st
from services.database import SessionLocal, Book, User, Shelf, ShelfItem
from services.db_operations import get_shelved_books, get_all_books

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
        return "The reader is currently browsing as a guest."

    context_parts = [
        f"Reader Name: {user.display_name} (@{user.username})",
        f"Bio: {user.bio or 'No bio provided'}",
        f"Annual Reading Challenge Goal: {user.reading_goal} books/year"
    ]

    try:
        shelved = get_shelved_books(user.id, shelf_name="All")
        if shelved:
            by_shelf: Dict[str, List[str]] = {}
            for item in shelved:
                shelf = item.get("shelf_name", "General")
                title = item.get("title", "Unknown")
                authors = item.get("authors", "")
                rating_info = f" (User rated: {item['user_rating']}★)" if item.get("user_rating") else ""
                entry = f"'{title}' by {authors}{rating_info}"
                by_shelf.setdefault(shelf, []).append(entry)

            shelf_summaries = []
            for s_name, book_list in by_shelf.items():
                shelf_summaries.append(f"- Shelf '{s_name}': {', '.join(book_list[:8])}")
            
            context_parts.append("Reader's Current Bookshelves:\n" + "\n".join(shelf_summaries))
    except Exception as e:
        context_parts.append(f"(Could not fetch bookshelf details: {e})")

    # Catalog books available in BookLover
    try:
        catalog = get_all_books()[:6]
        if catalog:
            cat_list = [f"'{b.title}' by {b.authors} ({b.average_rating:.1f}★)" for b in catalog]
            context_parts.append("Featured books available in BookLover library:\n- " + "\n- ".join(cat_list))
    except Exception:
        pass

    return "\n\n".join(context_parts)


def build_system_prompt(user: Optional[User]) -> str:
    """Constructs a rich literary persona for the AI Book Assistant."""
    reader_info = build_reader_context(user)
    
    return f"""You are 'BookLover AI' — a warm, witty, articulate, and deeply knowledgeable literary companion embedded in the BookLover app.

YOUR CAPABILITIES & PURPOSE:
1. Provide personalized book recommendations tailored to the reader's taste, favorite tropes, and reading mood.
2. Recommend books from or inspired by their personal bookshelves when relevant.
3. Help users discover hidden gems, explain complex themes or book endings, discuss characters, and break down series reading orders.
4. Protect readers from unwanted spoilers! Always give a clear spoiler warning before discussing plot twists.
5. Provide helpful reading stats and motivation towards their reading challenge goal.

READER PROFILE & CONTEXT:
{reader_info}

TONE & STYLE GUIDELINES:
- Warm, enthusiastic, and literary (like talking to a passionate bookstore curator or librarian friend).
- Format book titles in *italics* and always mention the author (e.g. *Never Never* by Colleen Hoover and Tarryn Fisher).
- Use bullet points, bold key themes, and concise paragraphs for readability.
- If recommending multiple books, provide 1-2 sentences on *why* they will enjoy each one (themes, tropes, pacing).
- Keep answers engaging, directly addressing the reader by their name when natural.
"""


def stream_chat_completion(
    messages: List[Dict[str, str]],
    user: Optional[User] = None,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7
) -> Generator[str, None, None]:
    """Streams response tokens from Groq API in real-time."""
    key = api_key or get_api_key()
    if not key:
        yield "⚠️ **Error:** No API key detected. Please configure your Groq API key in the sidebar."
        return

    system_prompt = build_system_prompt(user)
    formatted_messages = [{"role": "system", "content": system_prompt}] + messages

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": formatted_messages,
        "temperature": temperature,
        "max_tokens": 1200,
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
