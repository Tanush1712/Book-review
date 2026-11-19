import streamlit as st
from services.db_operations import (
    ensure_initialized, get_current_user,
    get_user_shelves_with_counts, get_shelved_books, set_book_shelf
)
from components.styles import inject_custom_css

st.set_page_config(
    page_title="My Books - BookLover",
    page_icon="📚",
    layout="wide"
)

inject_custom_css()
ensure_initialized()
current_user = get_current_user()

st.markdown("""
<div class="brand-header">
    <a href="#" class="brand-logo">📚 BookLover</a>
    <span class="brand-tagline">My Personal Library & Reading Shelves</span>
</div>
""", unsafe_allow_html=True)

st.markdown("## 📚 My Bookshelf")

# Display Shelves Stats Cards
shelves = get_user_shelves_with_counts(current_user.id)
shelf_cols = st.columns(len(shelves) + 1)

all_count = sum(s["count"] for s in shelves)
with shelf_cols[0]:
    st.metric(label="Total Shelved", value=all_count)

for i, s in enumerate(shelves):
    with shelf_cols[i + 1]:
        st.metric(label=s["name"], value=s["count"])

st.markdown("<hr style='border: none; border-top: 1px solid #ECEAE4; margin: 20px 0;'>", unsafe_allow_html=True)

# Shelf Tabs
tab_names = ["All Books"] + [s["name"] for s in shelves]
tabs = st.tabs(tab_names)

for idx, tab_name in enumerate(tab_names):
    with tabs[idx]:
        query_shelf = "All" if tab_name == "All Books" else tab_name
        books = get_shelved_books(current_user.id, shelf_name=query_shelf)

        if not books:
            st.info(f"No books in '{tab_name}' yet. Explore books and click 'Add to Shelf'!")
        else:
            for b in books:
                item_col1, item_col2, item_col3, item_col4 = st.columns([1, 4, 2, 2])
                with item_col1:
                    st.image(b["cover_url"] or "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=100", width=70)
                with item_col2:
                    st.markdown(f"**{b['title']}**")
                    st.caption(f"By {b['authors']}")
                    st.caption(f"Added: {b['added_at'].strftime('%b %d, %Y')}")
                with item_col3:
                    st.write(f"Shelf: `{b['shelf_name']}`")
                    st.caption(f"Community rating: ★ {b['average_rating']:.2f}")
                with item_col4:
                    if st.button("View Book", key=f"view_shelf_{b['book_id']}_{tab_name}", use_container_width=True):
                        st.session_state["selected_book_id"] = b["book_id"]
                        st.switch_page("pages/1_📖_Book_Details.py")
                    if st.button("Remove ✕", key=f"rem_shelf_{b['book_id']}_{tab_name}", use_container_width=True):
                        set_book_shelf(current_user.id, b["book_id"], "Remove from Shelves")
                        st.rerun()
                st.markdown("<hr style='border: none; border-top: 1px solid #F0EFEA; margin: 10px 0;'>", unsafe_allow_html=True)
