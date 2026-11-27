import streamlit as st

is_logged_in = bool(st.session_state.get("logged_in_user_id"))

if not is_logged_in:
    pg = st.navigation(
        [st.Page("pages/0_🔐_Login.py", title="Login", icon="🔐", default=True)],
        position="hidden"
    )
    pg.run()
else:
    pg = st.navigation([
        st.Page("views/home.py", title="Home", icon="🏠", default=True),
        st.Page("pages/0_🔐_Login.py", title="Login", icon="🔐", url_path="login"),
        st.Page("pages/1_📖_Book_Details.py", title="Book Details", icon="📖", url_path="book-details"),
        st.Page("pages/2_🔍_Search_Discover.py", title="Search & Discover", icon="🔍", url_path="search"),
        st.Page("pages/3_📚_My_Books.py", title="My Books", icon="📚", url_path="my-books"),
        st.Page("pages/4_👤_Profile.py", title="Profile", icon="👤", url_path="profile"),
        st.Page("pages/5_🤖_AI_Assistant.py", title="AI Assistant", icon="🤖", url_path="ai-assistant"),
    ])
    pg.run()
