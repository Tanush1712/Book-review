import streamlit as st
from services.db_operations import (
    ensure_initialized, get_book, get_current_user,
    get_book_shelf_status, set_book_shelf, get_reviews_for_book,
    add_review, like_review, get_all_books
)
from components.styles import inject_custom_css
from components.rating_histogram import render_rating_histogram
from components.ui_cards import render_book_card

st.set_page_config(
    page_title="Book Details - BookLover",
    page_icon="📖",
    layout="wide"
)

inject_custom_css()
ensure_initialized()

from components.auth_widget import render_sidebar_auth_widget
render_sidebar_auth_widget()

current_user = get_current_user()

# Determine selected book
if "selected_book_id" not in st.session_state:
    st.session_state["selected_book_id"] = 1  # Default to Never Never

book = get_book(st.session_state["selected_book_id"])
if not book:
    st.error("Book not found.")
    if st.button("← Back to Catalog"):
        st.switch_page("views/home.py")
    st.stop()

# Top Brand Header
st.markdown("""
<div class="brand-header">
    <a href="#" class="brand-logo">📚 BookLover</a>
    <span class="brand-tagline">Goodreads Alternative for Avid Readers</span>
</div>
""", unsafe_allow_html=True)

# 2-Column Hero Layout
col_left, col_right = st.columns([1, 2.2], gap="large")

with col_left:
    # High-resolution book cover
    cover_img = book.cover_image_url or "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400"
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <div class="book-cover-container">
            <img src="{cover_img}" style="width: 100%; max-width: 280px; border-radius: 8px; display: block;" />
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Shelf Selector Widget
    current_shelf = get_book_shelf_status(current_user.id, book.id) or "Add to Shelf"
    shelf_options = ["Add to Shelf", "Want to Read", "Currently Reading", "Read", "Favorites", "Remove from Shelves"]
    curr_index = shelf_options.index(current_shelf) if current_shelf in shelf_options else 0

    st.markdown("**Your Bookshelf:**")
    selected_shelf = st.selectbox(
        "Shelf status",
        options=shelf_options,
        index=curr_index,
        label_visibility="collapsed"
    )

    if selected_shelf != current_shelf and selected_shelf != "Add to Shelf":
        set_book_shelf(current_user.id, book.id, selected_shelf)
        st.success(f"Moved to '{selected_shelf}'!")
        st.rerun()
    elif selected_shelf == "Remove from Shelves" and current_shelf != "Add to Shelf":
        set_book_shelf(current_user.id, book.id, "Remove from Shelves")
        st.info("Removed from your shelves.")
        st.rerun()

    # Rate this book section
    st.markdown("<div style='margin-top: 15px;'><strong>Rate this book:</strong></div>", unsafe_allow_html=True)
    star_cols = st.columns(5)
    for i, star_col in enumerate(star_cols, start=1):
        with star_col:
            if st.button(f"{i} ★", key=f"rate_{i}", use_container_width=True):
                # Add a quick user rating
                st.session_state["quick_rating_submitted"] = i
                st.success(f"You rated this {i} stars!")

    # Affiliate / Preview buttons
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.link_button("📖 Sample", "https://openlibrary.org", use_container_width=True)
    with b_col2:
        st.link_button("🛒 Buy", "https://www.amazon.com", use_container_width=True)

    if st.button("🤖 Ask AI About This Book", use_container_width=True):
        st.session_state["ai_book_id"] = book.id
        st.session_state["queued_prompt"] = f"Tell me more about '{book.title}' by {book.authors}. What are its main tropes, mood, pacing, and who would enjoy it most?"
        st.switch_page("pages/5_🤖_AI_Assistant.py")


with col_right:
    # Title & Subtitle
    st.markdown(f"<h1 style='margin-bottom: 2px;'>{book.title}</h1>", unsafe_allow_html=True)
    if book.subtitle:
        st.markdown(f"<div style='font-size: 18px; color: #555; margin-bottom: 6px;'>{book.subtitle}</div>", unsafe_allow_html=True)
    
    # Series
    if book.series_info:
        st.markdown(f"<div style='font-size: 14px; color: #888; margin-bottom: 8px;'><em>Series: {book.series_info}</em></div>", unsafe_allow_html=True)

    # Authors
    st.markdown(f"<div style='font-size: 18px; font-weight: 500; margin-bottom: 12px;'>By <strong>{book.authors}</strong></div>", unsafe_allow_html=True)

    # Ratings Header Summary
    full_stars = int(round(book.average_rating))
    star_str = "★" * full_stars + "☆" * (5 - full_stars)
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 18px;">
        <span class="rating-score">{book.average_rating:.2f}</span>
        <span class="star-gold">{star_str}</span>
        <span class="rating-meta">· {book.ratings_count:,} ratings · {book.reviews_count:,} reviews</span>
    </div>
    """, unsafe_allow_html=True)

    # Synopsis / Description
    st.markdown("### Synopsis")
    desc_paragraphs = (book.description or "No description available.").split("\n\n")
    st.write(desc_paragraphs[0])
    if len(desc_paragraphs) > 1:
        with st.expander("Read full synopsis..."):
            for p in desc_paragraphs[1:]:
                st.write(p)

    # Genre Tags
    st.markdown("<div style='margin-top: 14px; margin-bottom: 6px;'><strong>Genres:</strong></div>", unsafe_allow_html=True)
    genre_html = ""
    for g in (book.genres or "").split(","):
        g_clean = g.strip()
        if g_clean:
            genre_html += f'<span class="genre-badge">{g_clean}</span>'
    st.markdown(genre_html, unsafe_allow_html=True)

    # Book Metadata Grid
    st.markdown("<hr style='border: none; border-top: 1px solid #ECEAE4; margin: 20px 0;'>", unsafe_allow_html=True)
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.caption("Format & Length")
        st.write(f"📄 {book.page_count} pages, Paperback")
    with m_col2:
        st.caption("Publication")
        st.write(f"📅 Published {book.publish_year}")
        if book.publisher:
            st.caption(f"by {book.publisher}")
    with m_col3:
        st.caption("ISBN")
        st.write(f"🔢 {book.isbn13 or 'N/A'}")

# --- Section Divider ---
st.markdown("<hr style='border: none; border-top: 1px solid #E0DED7; margin: 35px 0 25px 0;'>", unsafe_allow_html=True)

# --- Ratings & Reviews Breakdown ---
st.markdown("## Ratings & Community Reviews")

breakdown_col, action_col = st.columns([1.6, 1])

with breakdown_col:
    render_rating_histogram(book.get_rating_breakdown(), book.ratings_count, book.average_rating)

with action_col:
    st.markdown("<div style='padding-top: 18px;'></div>", unsafe_allow_html=True)
    with st.expander("📝 **Write a Review for this Book**", expanded=False):
        with st.form("write_review_form"):
            review_rating = st.select_slider(
                "Your Rating:",
                options=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
                value=4.0
            )
            review_text = st.text_area(
                "Your Thoughts:",
                placeholder="What did you think of the characters, plot, and pacing? Keep it spoiler-free or check the box below!",
                height=120
            )
            has_spoilers = st.checkbox("⚠️ This review contains spoilers")
            submitted = st.form_submit_button("Submit Review", use_container_width=True)

            if submitted:
                if len(review_text.strip()) < 5:
                    st.warning("Please share a few sentences in your review.")
                else:
                    add_review(book.id, current_user.id, review_rating, review_text, has_spoilers)
                    st.success("Your review was posted!")
                    st.rerun()

# --- Filter & Sort Controls ---
f_col1, f_col2, _ = st.columns([1, 1, 2])
with f_col1:
    star_filter = st.selectbox(
        "Filter by Rating",
        options=["All Stars", "5 Stars", "4 Stars", "3 Stars", "2 Stars", "1 Star"]
    )
    filter_val = None
    if star_filter != "All Stars":
        filter_val = float(star_filter.split()[0])

with f_col2:
    sort_by = st.selectbox(
        "Sort Reviews by",
        options=["Most Helpful", "Newest", "Highest Rating", "Lowest Rating"]
    )

# --- Reviews List ---
reviews = get_reviews_for_book(book.id, star_filter=filter_val, sort_by=sort_by)

if not reviews:
    st.info("No reviews match this filter. Be the first to write one!")
else:
    for rev in reviews:
        stars_int = int(round(rev["rating"]))
        stars_display = "★" * stars_int + "☆" * (5 - stars_int)
        date_str = rev["created_at"].strftime("%b %d, %Y")
        
        st.markdown(f"""
        <div class="review-card">
            <div class="reviewer-header">
                <img src="{rev['user_avatar']}" class="reviewer-avatar" />
                <div>
                    <div class="reviewer-name">{rev['user_name']}</div>
                    <div class="review-date">Reviewed on {date_str}</div>
                </div>
                <div style="margin-left: auto;">
                    <span class="star-gold">{stars_display}</span>
                    <span style="font-weight: 600; font-size: 14px; margin-left: 4px;">{rev['rating']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if rev["contains_spoilers"]:
            with st.expander("⚠️ **Warning: This review contains spoilers. Click to reveal.**"):
                st.write(rev["review_text"])
        else:
            st.write(rev["review_text"])

        st.markdown(f"""
            <div style="margin-top: 12px; font-size: 13px; color: #666; display: flex; align-items: center; gap: 15px;">
                <span>👍 {rev['likes_count']} people found this helpful</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Helpful Upvote Button
        if st.button(f"Helpful 👍 ({rev['likes_count']})", key=f"like_rev_{rev['id']}"):
            like_review(rev["id"])
            st.rerun()

# --- Readers Also Enjoyed Section ---
st.markdown("<hr style='border: none; border-top: 1px solid #E0DED7; margin: 40px 0 25px 0;'>", unsafe_allow_html=True)
st.markdown("## Readers Also Enjoyed")

all_books = [b for b in get_all_books() if b.id != book.id][:4]
if all_books:
    rec_cols = st.columns(len(all_books))
    for col, rec_book in zip(rec_cols, all_books):
        with col:
            render_book_card(
                book_id=rec_book.id,
                title=rec_book.title,
                authors=rec_book.authors,
                cover_url=rec_book.cover_image_url or "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300",
                rating=rec_book.average_rating,
                button_key=f"rec_nav_{rec_book.id}"
            )
