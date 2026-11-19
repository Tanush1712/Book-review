import streamlit as st
import pandas as pd
from services.db_operations import (
    ensure_initialized, get_current_user,
    get_shelved_books, set_book_shelf
)
from services.database import SessionLocal, Book, ShelfItem
from components.styles import inject_custom_css

st.set_page_config(
    page_title="Profile & Reading Goal - BookLover",
    page_icon="👤",
    layout="wide"
)

inject_custom_css()
ensure_initialized()
current_user = get_current_user()

st.markdown("""
<div class="brand-header">
    <a href="#" class="brand-logo">📚 BookLover</a>
    <span class="brand-tagline">Reader Profile & Reading Challenge</span>
</div>
""", unsafe_allow_html=True)

# User Profile Header Card
p_col1, p_col2 = st.columns([1, 4])
with p_col1:
    st.image(current_user.avatar_url, width=130)
with p_col2:
    st.markdown(f"## {current_user.display_name}")
    st.caption(f"@{current_user.username} · Member since {current_user.created_at.strftime('%B %Y')}")
    st.write(current_user.bio)

st.markdown("<hr style='border: none; border-top: 1px solid #ECEAE4; margin: 25px 0;'>", unsafe_allow_html=True)

# 2026 Reading Challenge
st.markdown("### 🎯 2026 Reading Challenge")

read_books = get_shelved_books(current_user.id, shelf_name="Read")
read_count = len(read_books)
goal = current_user.reading_goal or 30
pct = min(1.0, read_count / goal) if goal > 0 else 0.0

st.progress(pct, text=f"**{read_count}** of **{goal}** books read ({pct * 100:.0f}%)")

goal_col1, goal_col2 = st.columns([2, 1])
with goal_col1:
    if read_count >= goal:
        st.balloons()
        st.success("🎉 Congratulations! You have achieved your 2026 Reading Goal!")
    else:
        st.info(f"Keep it up! You need {goal - read_count} more books to reach your 2026 goal.")
with goal_col2:
    new_goal = st.number_input("Update Annual Goal:", min_value=1, max_value=365, value=goal)
    if new_goal != goal:
        with SessionLocal() as db:
            u = db.query(current_user.__class__).filter_by(id=current_user.id).first()
            if u:
                u.reading_goal = new_goal
                db.commit()
                st.success("Goal updated!")
                st.rerun()

st.markdown("<hr style='border: none; border-top: 1px solid #ECEAE4; margin: 30px 0;'>", unsafe_allow_html=True)

# Goodreads CSV Export Importer
st.markdown("### 📥 Import Your Library from Goodreads")
st.write(
    "Already have a Goodreads account? Export your reading history (`goodreads_library_export.csv`) "
    "from Goodreads settings, and upload it here to auto-import your books and shelves!"
)

uploaded_file = st.file_uploader("Upload Goodreads CSV Export", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success(f"Loaded CSV with {len(df)} rows!")
        
        # Display sample
        preview_cols = [c for c in ["Title", "Author", "My Rating", "Exclusive Shelf", "Year Published"] if c in df.columns]
        st.dataframe(df[preview_cols].head(5), use_container_width=True)

        if st.button("🚀 Import Books to My Bookshelf", type="primary"):
            imported_count = 0
            with SessionLocal() as db:
                for _, row in df.iterrows():
                    title = str(row.get("Title", "")).strip()
                    author = str(row.get("Author", "")).strip()
                    shelf = str(row.get("Exclusive Shelf", "Read")).replace("-", " ").title()

                    if not title or title.lower() == "nan":
                        continue

                    # Check or create book in DB
                    book_record = db.query(Book).filter(Book.title.ilike(title)).first()
                    if not book_record:
                        book_record = Book(
                            title=title,
                            authors=author or "Unknown Author",
                            average_rating=float(row.get("Average Rating", 4.0)) if "Average Rating" in row else 4.0,
                            ratings_count=100,
                            reviews_count=10,
                            cover_image_url="https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300"
                        )
                        db.add(book_record)
                        db.flush()

                    # Put on shelf
                    set_book_shelf(current_user.id, book_record.id, shelf)
                    imported_count += 1

            st.success(f"Successfully imported {imported_count} books to your shelves!")
            st.rerun()

    except Exception as e:
        st.error(f"Error parsing CSV file: {e}")
