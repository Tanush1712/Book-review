import streamlit as st
from services.db_operations import get_current_user


def render_sidebar_auth_widget():
    """Renders user login status and quick actions in the Streamlit sidebar."""
    with st.sidebar:
        st.markdown("<hr style='margin: 15px 0 10px 0; border: none; border-top: 1px solid #ECEAE4;'>", unsafe_allow_html=True)
        user = get_current_user()
        
        is_custom_logged_in = "logged_in_user_id" in st.session_state and st.session_state["logged_in_user_id"] is not None

        if user:
            provider_tag = f" <span style='font-size: 11px; background: #EFEFEA; padding: 2px 6px; border-radius: 4px; color: #555;'>{user.auth_provider.upper()}</span>" if user.auth_provider and user.auth_provider != "local" else ""
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <img src="{user.avatar_url}" style="width: 36px; height: 36px; border-radius: 50%; object-fit: cover; border: 1px solid #ddd;" />
                <div style="line-height: 1.2;">
                    <div style="font-weight: 600; font-size: 13px; color: #222;">{user.display_name}</div>
                    <div style="font-size: 11px; color: #777;">@{user.username}{provider_tag}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if is_custom_logged_in:
                if st.button("🚪 Sign Out", key="sidebar_logout_btn", use_container_width=True):
                    st.session_state.pop("logged_in_user_id", None)
                    st.session_state.pop("logged_in_user_name", None)
                    st.success("Signed out successfully.")
                    st.rerun()
            else:
                if st.button("🔐 Switch / Sign In Account", key="sidebar_login_switch_btn", use_container_width=True):
                    st.switch_page("pages/0_🔐_Login.py")
        else:
            st.markdown("<div style='font-size: 13px; color: #666; margin-bottom: 8px;'>👤 Guest Reader</div>", unsafe_allow_html=True)
            if st.button("🔐 Sign In / Sign Up", key="sidebar_guest_login_btn", use_container_width=True):
                st.switch_page("pages/0_🔐_Login.py")
