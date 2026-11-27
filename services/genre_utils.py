import re
from typing import List, Set, Tuple

# Canonical genre aliases for inconsistent formatting and abbreviations
GENRE_ALIASES = {
    "sci fi": "science fiction",
    "scifi": "science fiction",
    "sf": "science fiction",
    "science-fiction": "science fiction",
    "ya": "young adult",
    "young-adult": "young adult",
    "na": "new adult",
    "new-adult": "new adult",
    "psych thriller": "psychological thriller",
    "psycho thriller": "psychological thriller",
    "hist fic": "historical fiction",
    "hist fiction": "historical fiction",
    "nonfiction": "non fiction",
    "non-fiction": "non fiction",
    "lgbt": "lgbtq+",
    "lgbtq": "lgbtq+",
    "lgbtqia": "lgbtq+",
    "romcom": "romantic comedy",
    "rom com": "romantic comedy",
    "mysteries": "mystery",
    "thrillers": "thriller",
    "romances": "romance",
    "dramas": "drama",
    "fantasies": "fantasy",
    "classics": "classic",
    "memoirs": "memoir",
    "biographies": "biography",
    "contemporary fiction": "contemporary",
}

# Known genres used to detect genre queries vs plain title/author queries
KNOWN_GENRES: Set[str] = {
    "romance",
    "mystery",
    "thriller",
    "psychological thriller",
    "historical fiction",
    "young adult",
    "new adult",
    "fantasy",
    "science fiction",
    "contemporary",
    "drama",
    "fiction",
    "non fiction",
    "horror",
    "suspense",
    "crime",
    "detective",
    "literary fiction",
    "classic",
    "dystopian",
    "adventure",
    "biography",
    "memoir",
    "poetry",
    "self help",
    "lgbtq+",
    "romantic comedy",
    "paranormal",
    "urban fantasy",
    "dark romance",
    "general",
} | set(GENRE_ALIASES.keys()) | set(GENRE_ALIASES.values())


def normalize_genre_token(text: str) -> str:
    """Normalizes a single genre string (case, hyphens, underscores, punctuation, aliases)."""
    if not text:
        return ""
    cleaned = text.lower().strip()
    # Preserve '+' in LGBTQ+ while turning separators/punctuation into spaces
    cleaned = cleaned.replace("&", " and ")
    cleaned = re.sub(r"[-_./]+", " ", cleaned)
    cleaned = re.sub(r"[^\w\s+]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return GENRE_ALIASES.get(cleaned, cleaned)


def normalize_text(text: str) -> str:
    """Normalizes general text for case- and punctuation-insensitive comparisons."""
    if not text:
        return ""
    cleaned = text.lower().strip()
    cleaned = re.sub(r"[-_]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def parse_book_genres(genres_str: str) -> List[str]:
    """Splits and normalizes a book's genre string, deduplicating while preserving order."""
    if not genres_str:
        return []
    raw_parts = re.split(r"[,;|/\n]+", genres_str)
    seen = set()
    result = []
    for part in raw_parts:
        norm = normalize_genre_token(part)
        if norm and norm not in seen:
            seen.add(norm)
            result.append(norm)
    return result


def clean_genres_display(subjects: List[str], limit: int = 5) -> str:
    """Cleans raw subject/genre tags for display and storage without duplicates."""
    if not subjects:
        return "Fiction, General"
    seen = set()
    cleaned_list = []
    for subj in subjects:
        if not isinstance(subj, str):
            continue
        raw = subj.strip()
        if not raw:
            continue
        norm = normalize_genre_token(raw)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        # Keep clean capitalization while preserving acronyms like LGBTQ+
        if norm == "lgbtq+":
            display = "LGBTQ+"
        elif raw.isupper() or raw.islower():
            display = raw.title()
        else:
            display = raw
        cleaned_list.append(display)
        if len(cleaned_list) >= limit:
            break
    return ", ".join(cleaned_list) if cleaned_list else "Fiction, General"


def _greedy_segment_genres(words: List[str], vocabulary: Set[str]) -> List[str]:
    """Attempts to segment a space-separated word list into known genre phrases."""
    n = len(words)
    tokens: List[str] = []
    i = 0
    while i < n:
        matched = None
        for span in range(min(3, n - i), 0, -1):
            candidate = normalize_genre_token(" ".join(words[i : i + span]))
            if candidate in vocabulary:
                matched = candidate
                i += span
                break
        if matched is None:
            return []
        tokens.append(matched)
    return tokens


def extract_query_genres(
    query_str: str, extra_known_genres: Set[str] = None
) -> Tuple[List[str], bool]:
    """
    Parses a search query into normalized genre tokens if it represents one or more genres.

    Returns:
        (genre_tokens, is_multi_or_genre_query)
    """
    if not query_str or not query_str.strip():
        return [], False

    vocab = set(KNOWN_GENRES)
    if extra_known_genres:
        vocab |= extra_known_genres

    raw = query_str.strip()
    has_explicit_sep = bool(re.search(r"[,;|/&+]|\band\b", raw, flags=re.IGNORECASE))

    if has_explicit_sep:
        parts = re.split(r"\s*(?:[,;|/&+]|\band\b)\s*", raw, flags=re.IGNORECASE)
        tokens = []
        seen = set()
        for p in parts:
            norm = normalize_genre_token(p)
            if norm and norm not in seen:
                seen.add(norm)
                tokens.append(norm)
        if not tokens:
            return [], False
        all_known = all(_matches_vocab(t, vocab) for t in tokens)
        return tokens, (all_known or len(tokens) > 1)

    whole_norm = normalize_genre_token(raw)
    if whole_norm in vocab:
        return [whole_norm], True

    # Try segmenting space-separated multi-genre queries like "Romance Mystery" or "Sci-Fi Fantasy"
    words = whole_norm.split()
    if len(words) >= 2:
        segmented = _greedy_segment_genres(words, vocab)
        if len(segmented) >= 2:
            # Deduplicate preserving order
            deduped = list(dict.fromkeys(segmented))
            return deduped, True

    return [], False


def _matches_vocab(token: str, vocab: Set[str]) -> bool:
    if token in vocab:
        return True
    token_words = set(token.split())
    return any(v in token_words for v in vocab if " " not in v)


def score_genre_match(query_genre: str, book_genres: List[str]) -> int:
    """
    Scores how well a single normalized query genre matches a book's normalized genre list.
    Returns 3 for exact match, 2 for word/phrase containment inside a genre tag, 0 otherwise.
    """
    if not query_genre or not book_genres:
        return 0

    if query_genre in book_genres:
        return 3

    q_words = query_genre.split()
    q_pattern = re.compile(r"(?:^|\s)" + re.escape(query_genre) + r"(?=$|\s)")
    for bg in book_genres:
        if q_pattern.search(bg):
            return 2
        bg_words = set(bg.split())
        if len(q_words) > 1 and all(w in bg_words for w in q_words):
            return 2

    return 0
