import streamlit as st


def render_book_card(book_id: int, title: str, authors: str, cover_url: str, rating: float = 4.0, button_key: str = None):
    """Renders a compact, clickable book card for carousels and grids."""
    st.markdown(f"""
    <div style="background: white; border: 1px solid #ECEAE4; border-radius: 8px; padding: 10px; text-align: center; height: 320px; display: flex; flex-direction: column; justify-content: space-between;">
        <div>
            <img src="{cover_url}" style="height: 180px; width: 120px; object-fit: cover; border-radius: 4px; box-shadow: 0 4px 8px rgba(0,0,0,0.12);" />
            <div style="font-weight: 600; font-size: 13px; margin-top: 8px; line-height: 1.2; max-height: 32px; overflow: hidden; text-overflow: ellipsis; color: #222;">
                {title}
            </div>
            <div style="font-size: 12px; color: #666; margin-top: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                {authors}
            </div>
        </div>
        <div style="font-size: 12px; color: #EAA83B; font-weight: 600;">
            ★ {rating:.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    key = button_key or f"view_book_{book_id}"
    if st.button("View Book", key=key, use_container_width=True):
        st.session_state["selected_book_id"] = book_id
        st.switch_page("pages/1_📖_Book_Details.py")
