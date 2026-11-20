import streamlit as st
from services.db_operations import ensure_initialized, get_current_user
from services.auth_service import (
    evaluate_password_strength, generate_strong_password,
    register_user, login_user, sso_authenticate
)
from components.styles import inject_custom_css

st.set_page_config(
    page_title="Account & Authentication - BookLover",
    page_icon="🔐",
    layout="wide"
)

inject_custom_css()
ensure_initialized()

st.markdown("""
<div class="brand-header">
    <a href="#" class="brand-logo">📚 BookLover</a>
    <span class="brand-tagline">Reader Authentication & Account Access</span>
</div>
""", unsafe_allow_html=True)

# Check active user status
current_user = get_current_user()
is_custom_logged_in = "logged_in_user_id" in st.session_state and st.session_state["logged_in_user_id"] is not None

# If user is actively logged in, display active profile card with logout
if is_custom_logged_in and current_user:
    st.markdown(f"""
    <div class="auth-container" style="max-width: 650px; margin: 20px auto;">
        <div style="display: flex; align-items: center; gap: 18px; margin-bottom: 20px;">
            <img src="{current_user.avatar_url}" style="width: 72px; height: 72px; border-radius: 50%; object-fit: cover; border: 2px solid #397858;" />
            <div>
                <h2 style="margin: 0; font-size: 24px;">{current_user.display_name}</h2>
                <div style="color: #666; font-size: 14px;">@{current_user.username} · {current_user.email}</div>
                <div style="margin-top: 6px;">
                    <span style="background: #E8F5E9; color: #2E7D32; font-size: 12px; font-weight: 600; padding: 3px 8px; border-radius: 4px;">
                        ✓ Active Session ({current_user.auth_provider.upper()} AUTH)
                    </span>
                </div>
            </div>
        </div>
        <p style="color: #555; font-size: 14px;">{current_user.bio}</p>
    </div>
    """, unsafe_allow_html=True)

    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
    with btn_col1:
        if st.button("📚 Go to My Bookshelf", use_container_width=True):
            st.switch_page("pages/3_📚_My_Books.py")
    with btn_col2:
        if st.button("👤 View Full Profile", use_container_width=True):
            st.switch_page("pages/4_👤_Profile.py")
    with btn_col3:
        if st.button("🚪 Sign Out", type="secondary", use_container_width=True):
            st.session_state.pop("logged_in_user_id", None)
            st.session_state.pop("logged_in_user_name", None)
            st.success("You have signed out.")
            st.rerun()

    st.stop()


# --- Main Login / Register / SSO Layout ---
st.markdown("<div style='max-width: 650px; margin: 0 auto;'>", unsafe_allow_html=True)

tabs = st.tabs(["🔑 Sign In", "📝 Create Account (Sign Up)", "🌐 Single Sign-On (SSO)"])

# ==========================================
# TAB 1: SIGN IN (LOGIN)
# ==========================================
with tabs[0]:
    st.markdown("### Welcome Back, Reader")
    st.caption("Sign in to access your reading challenge, saved shelves, and community reviews.")

    with st.form("signin_form"):
        login_input = st.text_input(
            "Username or Email",
            placeholder="e.g. tanush_reader or reader@example.com"
        )
        login_password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )
        remember_me = st.checkbox("Remember this device", value=True)
        login_submitted = st.form_submit_button("Sign In →", type="primary", use_container_width=True)

        if login_submitted:
            if not login_input or not login_password:
                st.warning("Please fill in both fields.")
            else:
                success, msg, user = login_user(login_input, login_password)
                if success:
                    st.session_state["logged_in_user_id"] = user.id
                    st.session_state["logged_in_user_name"] = user.display_name
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    with st.expander("💡 Quick Fill with Demo Account"):
        st.write("Click below to log in as the pre-configured demo user:")
        if st.button("Sign In as Tanush (Demo User)", key="demo_login_btn", use_container_width=True):
            demo_user = current_user
            if demo_user:
                st.session_state["logged_in_user_id"] = demo_user.id
                st.session_state["logged_in_user_name"] = demo_user.display_name
                st.success("Logged in as Demo User!")
                st.rerun()


# ==========================================
# TAB 2: CREATE ACCOUNT (SIGN UP + PASSWORD EVALUATOR)
# ==========================================
with tabs[1]:
    st.markdown("### Create Your Free Account")
    st.caption("Track what you read, discover new authors, and connect with fellow book lovers.")

    # Password Policy Preference
    st.markdown("**Password Security Mode:**")
    password_mode = st.radio(
        "Password enforcement option:",
        options=[
            "Strong Password (Recommended - minimum 8 chars, uppercase, number, symbol)",
            "Permit Weak Passwords (Allows any password with warning)"
        ],
        index=0,
        label_visibility="collapsed"
    )
    enforce_strong = "Recommended" in password_mode

    # Strong Password Generator Utility
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    with st.expander("🎲 Need a Strong Password? Click to Generate"):
        gen_cols = st.columns([2, 1])
        with gen_cols[0]:
            pwd_len = st.slider("Password Length:", min_value=10, max_value=24, value=14)
        with gen_cols[1]:
            st.markdown("<div style='padding-top: 26px;'></div>", unsafe_allow_html=True)
            if st.button("Generate Now", key="btn_gen_pwd", use_container_width=True):
                st.session_state["generated_password"] = generate_strong_password(pwd_len)

        if "generated_password" in st.session_state:
            st.code(st.session_state["generated_password"], language="text")
            st.caption("Copy this generated password into the field below!")

    # Live Password Input & Evaluator
    su_name = st.text_input("Full Name / Display Name", placeholder="e.g. Jane Austen", key="su_name")
    su_username = st.text_input("Choose Username", placeholder="e.g. jane_reads", key="su_user")
    su_email = st.text_input("Email Address", placeholder="e.g. jane@books.com", key="su_email")

    # Real-time password input
    default_pwd_val = st.session_state.get("generated_password", "")
    su_password = st.text_input(
        "Choose Password",
        value=default_pwd_val,
        type="password",
        placeholder="Enter your password",
        key="su_password_input"
    )

    # Dynamic Password Strength Evaluation Display
    if su_password:
        eval_data = evaluate_password_strength(su_password)
        score = eval_data["score"]
        level = eval_data["level"]
        color = eval_data["color"]
        checks = eval_data["checks"]

        # Visual Strength Meter Bar
        st.markdown(f"""
        <div style="margin: 8px 0 12px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px; font-weight: 600; margin-bottom: 4px;">
                <span>Password Strength:</span>
                <span style="color: {color};">{level} ({score}%)</span>
            </div>
            <div class="strength-meter-bg">
                <div class="strength-meter-fill" style="width: {score}%; background-color: {color};"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Real-time Checklist Columns
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"{'✅' if checks['length_8'] else '❌'} At least 8 characters")
            st.markdown(f"{'✅' if checks['has_upper'] else '❌'} Uppercase letter (A-Z)")
            st.markdown(f"{'✅' if checks['has_lower'] else '❌'} Lowercase letter (a-z)")
        with c2:
            st.markdown(f"{'✅' if checks['has_digit'] else '❌'} Numeric number (0-9)")
            st.markdown(f"{'✅' if checks['has_special'] else '❌'} Special character (!@#$...)")

        # Tips
        if eval_data["tips"]:
            for tip in eval_data["tips"]:
                st.caption(f"💡 *{tip}*")

    su_confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="su_confirm")

    if st.button("Create Account & Sign In →", type="primary", use_container_width=True, key="btn_signup"):
        if not su_username or not su_email or not su_password:
            st.warning("Please fill in all required fields.")
        elif su_password != su_confirm_password:
            st.error("Passwords do not match. Please re-enter carefully.")
        else:
            allow_weak = not enforce_strong
            success, msg, new_user = register_user(
                username=su_username,
                display_name=su_name or su_username,
                email=su_email,
                password=su_password,
                allow_weak=allow_weak
            )
            if success:
                st.session_state["logged_in_user_id"] = new_user.id
                st.session_state["logged_in_user_name"] = new_user.display_name
                st.success(msg)
                st.balloons()
                st.rerun()
            else:
                st.error(msg)


# ==========================================
# TAB 3: SSO (SINGLE SIGN-ON)
# ==========================================
with tabs[2]:
    st.markdown("### Single Sign-On (SSO)")
    st.caption("Sign in instantly using your Google, GitHub, Apple, or Corporate identity provider.")

    st.markdown("""
    <div style="background: #F8F9FA; border: 1px solid #E9ECEF; border-radius: 8px; padding: 14px 18px; margin-bottom: 20px;">
        <div style="font-size: 13px; color: #495057;">
            🔒 <strong>SSO Enabled:</strong> Authenticate securely with zero password friction, or supply an SSO Token / Password below.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1-Click Fast SSO Providers
    st.markdown("**Fast 1-Click SSO Access:**")
    
    col_g, col_gh, col_ap = st.columns(3)
    
    with col_g:
        if st.button("🔴 Google SSO", use_container_width=True):
            success, msg, user = sso_authenticate(
                provider="Google",
                email="tanush.reader@gmail.com",
                display_name="Tanush (Google Reader)"
            )
            if success:
                st.session_state["logged_in_user_id"] = user.id
                st.session_state["logged_in_user_name"] = user.display_name
                st.success(msg)
                st.rerun()

    with col_gh:
        if st.button("⚫ GitHub SSO", use_container_width=True):
            success, msg, user = sso_authenticate(
                provider="GitHub",
                email="tanush.dev@github.com",
                display_name="Tanush (GitHub Reader)"
            )
            if success:
                st.session_state["logged_in_user_id"] = user.id
                st.session_state["logged_in_user_name"] = user.display_name
                st.success(msg)
                st.rerun()

    with col_ap:
        if st.button("⚪ Apple SSO", use_container_width=True):
            success, msg, user = sso_authenticate(
                provider="Apple",
                email="tanush.apple@icloud.com",
                display_name="Tanush (Apple Reader)"
            )
            if success:
                st.session_state["logged_in_user_id"] = user.id
                st.session_state["logged_in_user_name"] = user.display_name
                st.success(msg)
                st.rerun()

    # Enterprise / Custom SSO with SSO Password Option
    st.markdown("<hr style='border: none; border-top: 1px solid #ECEAE4; margin: 25px 0 15px 0;'>", unsafe_allow_html=True)
    st.markdown("#### Enterprise / Custom SSO Login")
    st.caption("Authenticate with an enterprise domain and SSO token/password.")

    with st.form("custom_sso_form"):
        sso_email = st.text_input("Work / University Email", placeholder="e.g. yourname@university.edu or @company.com")
        sso_name = st.text_input("Full Name", placeholder="e.g. Tanush")
        sso_pwd_token = st.text_input("SSO Password / Auth Token", type="password", placeholder="Enter your corporate SSO password / token")
        sso_provider_choice = st.selectbox("Identity Provider", ["Okta / SAML SSO", "Google Workspace", "Microsoft Azure AD", "Custom SSO"])

        sso_submit = st.form_submit_button("Authenticate with SSO →", type="primary", use_container_width=True)

        if sso_submit:
            if not sso_email or "@" not in sso_email:
                st.warning("Please provide a valid enterprise or institutional email.")
            else:
                provider_tag = sso_provider_choice.split()[0]
                success, msg, user = sso_authenticate(
                    provider=provider_tag,
                    email=sso_email,
                    display_name=sso_name or sso_email.split("@")[0].title(),
                    sso_password_token=sso_pwd_token
                )
                if success:
                    st.session_state["logged_in_user_id"] = user.id
                    st.session_state["logged_in_user_name"] = user.display_name
                    st.success(msg)
                    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
