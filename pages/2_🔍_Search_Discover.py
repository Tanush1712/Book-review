import streamlit as st
from services.db_operations import ensure_initialized, search_local_books
from services.book_api import search_books_online, import_book_to_db
from components.styles import inject_custom_css
from components.ui_cards import render_book_card

st.set_page_config(
    page_title="Search & Discover - BookLover",
    page_icon="🔍",
    layout="wide"
)

inject_custom_css()
ensure_initialized()

st.markdown("""
<div class="brand-header">
    <a href="#" class="brand-logo">📚 BookLover</a>
    <span class="brand-tagline">Search millions of books & discover your next read</span>
</div>
""", unsafe_allow_html=True)

st.markdown("## 🔍 Search & Discover")

# Pre-populate search query if passed from genre buttons
initial_query = st.session_state.get("search_query", "")

search_col, source_col = st.columns([3, 1])
with search_col:
    query = st.text_input(
        "Search by Title, Author, Genre, or ISBN",
        value=initial_query,
        placeholder="e.g. Never Never, Colleen Hoover, Mystery, 9781335004888..."
    )
with source_col:
    search_source = st.selectbox(
        "Search Catalog",
        options=["Global (Open Library API)", "Local Database Only"]
    )

if query:
    st.markdown(f"### Results for *'{query}'*")
    
    if search_source == "Local Database Only":
        local_results = search_local_books(query)
        if not local_results:
            st.warning("No local books matched your search. Try switching to 'Global (Open Library API)'!")
        else:
            cols = st.columns(min(4, max(1, len(local_results))))
            for idx, b in enumerate(local_results):
                with cols[idx % 4]:
                    render_book_card(
                        book_id=b.id,
                        title=b.title,
                        authors=b.authors,
                        cover_url=b.cover_image_url or "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300",
                        rating=b.average_rating,
                        button_key=f"search_local_{b.id}"
                    )
    else:
        with st.spinner("Searching millions of books across Open Library..."):
            online_results = search_books_online(query, limit=12)
        
        if not online_results:
            st.info("No books found online for this query. Try a different title or author.")
        else:
            st.caption(f"Found {len(online_results)} matching books from Open Library")
            grid_cols = st.columns(4)
            for idx, item in enumerate(online_results):
                with grid_cols[idx % 4]:
                    st.markdown(f"""
                    <div style="background: white; border: 1px solid #ECEAE4; border-radius: 8px; padding: 12px; margin-bottom: 15px; height: 350px; display: flex; flex-direction: column; justify-content: space-between;">
                        <div style="text-align: center;">
                            <img src="{item['cover_url']}" style="height: 170px; width: 110px; object-fit: cover; border-radius: 4px; box-shadow: 0 3px 6px rgba(0,0,0,0.1);" />
                            <div style="font-weight: 600; font-size: 13px; margin-top: 8px; line-height: 1.2; max-height: 32px; overflow: hidden; text-overflow: ellipsis; color: #222;">
                                {item['title']}
                            </div>
                            <div style="font-size: 12px; color: #666; margin-top: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                {item['authors']}
                            </div>
                        </div>
                        <div style="font-size: 11px; color: #888; text-align: center;">
                            ★ {item['average_rating']} · {item['publish_year']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("View Book Page →", key=f"import_view_{idx}", use_container_width=True):
                        # Save to database and open book page
                        new_id = import_book_to_db(item)
                        if new_id:
                            st.session_state["selected_book_id"] = new_id
                            st.switch_page("pages/1_📖_Book_Details.py")
else:
    st.info("💡 Type a book title (e.g. *Never Never*, *Fourth Wing*, *Dune*) or author name to search.")
