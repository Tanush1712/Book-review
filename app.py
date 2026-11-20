import streamlit as st
from services.db_operations import ensure_initialized, get_all_books, get_book
from components.styles import inject_custom_css
from components.ui_cards import render_book_card

st.set_page_config(
    page_title="BookLover - Modern Book Discovery & Reviews",
    page_icon="📚",
    layout="wide"
)

inject_custom_css()
ensure_initialized()

from components.auth_widget import render_sidebar_auth_widget
render_sidebar_auth_widget()

# Top Navigation / Brand
st.markdown("""
<div class="brand-header">
    <a href="#" class="brand-logo">📚 BookLover</a>
    <span class="brand-tagline">Meet your next favorite book. Read reviews, track your library, and connect with readers.</span>
</div>
""", unsafe_allow_html=True)

# Hero Spotlight on Never Never (The benchmark book from user)
never_never = get_book(1)
if never_never:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #F3F1EB 0%, #FFFFFF 100%); border: 1px solid #E8E5DD; border-radius: 12px; padding: 24px; margin-bottom: 35px; box-shadow: 0 4px 15px rgba(0,0,0,0.03);">
        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #397858; font-weight: 700; margin-bottom: 6px;">Featured Book Spotlight</div>
    </div>
    """, unsafe_allow_html=True)

    h_col1, h_col2 = st.columns([1, 2.5], gap="medium")
    with h_col1:
        st.image(
            never_never.cover_image_url or "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1666887550i/63120226.jpg",
            width=220
        )
    with h_col2:
        st.markdown(f"## {never_never.title}")
        st.markdown(f"**By {never_never.authors}** · *{never_never.series_info or ''}*")
        st.markdown(f"★ **{never_never.average_rating:.2f}** ({never_never.ratings_count:,} ratings)")
        
        st.write((never_never.description or "")[:280] + "...")
        
        btn_col1, btn_col2 = st.columns([1, 2])
        with btn_col1:
            if st.button("Explore Book Details Page →", type="primary", use_container_width=True):
                st.session_state["selected_book_id"] = never_never.id
                st.switch_page("pages/1_📖_Book_Details.py")
        with btn_col2:
            if st.button("🔍 Search Catalog", use_container_width=False):
                st.switch_page("pages/2_🔍_Search_Discover.py")

st.markdown("<hr style='border: none; border-top: 1px solid #ECEAE4; margin: 30px 0;'>", unsafe_allow_html=True)

# Trending Books Grid
st.markdown("### 🔥 Trending & Popular in the Community")
all_books = get_all_books()

cols = st.columns(min(4, len(all_books)))
for i, b in enumerate(all_books[:4]):
    with cols[i % 4]:
        render_book_card(
            book_id=b.id,
            title=b.title,
            authors=b.authors,
            cover_url=b.cover_image_url or "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300",
            rating=b.average_rating,
            button_key=f"home_book_{b.id}"
        )

# Browse by Popular Genres
st.markdown("<hr style='border: none; border-top: 1px solid #ECEAE4; margin: 35px 0;'>", unsafe_allow_html=True)
st.markdown("### 🏷️ Browse by Genre")

genres = ["Romance", "Mystery", "Thriller", "Psychological Thriller", "Historical Fiction", "Young Adult", "Fantasy"]
g_cols = st.columns(len(genres))
for idx, g in enumerate(genres):
    with g_cols[idx]:
        if st.button(g, key=f"genre_btn_{idx}", use_container_width=True):
            st.session_state["search_query"] = g
            st.switch_page("pages/2_🔍_Search_Discover.py")
