import streamlit as st


def inject_custom_css():
    """Injects high-fidelity custom CSS to transform Streamlit into a Goodreads-like design."""
    st.markdown("""
    <style>
    /* Google Fonts import: Merriweather for classic bookish feel & Inter for UI */
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;1,300&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    h1, h2, h3, .book-title {
        font-family: 'Merriweather', Georgia, serif;
        color: #1e1e1e;
    }

    /* Top navbar brand styling */
    .brand-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0 20px 0;
        border-bottom: 1px solid #E8E5DD;
        margin-bottom: 24px;
    }
    .brand-logo {
        font-family: 'Merriweather', Georgia, serif;
        font-size: 26px;
        font-weight: 700;
        color: #397858;
        letter-spacing: -0.5px;
        text-decoration: none;
    }
    .brand-tagline {
        font-size: 13px;
        color: #767676;
        padding-left: 10px;
        border-left: 1px solid #D5D3CC;
    }

    /* Book Hero Cover Card */
    .book-cover-container {
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15), 0 2px 6px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        background: #fdfdfd;
        display: inline-block;
        max-width: 100%;
    }
    .book-cover-container:hover {
        transform: translateY(-4px);
        box-shadow: 0 14px 30px rgba(0, 0, 0, 0.2);
    }

    /* Genre Badges / Pills */
    .genre-badge {
        display: inline-block;
        background-color: #EFEFEA;
        color: #333333;
        border-radius: 16px;
        padding: 4px 12px;
        font-size: 12px;
        font-weight: 500;
        margin: 2px 6px 6px 0;
        text-decoration: none;
        border: 1px solid #E0DED7;
        transition: background-color 0.15s ease;
    }
    .genre-badge:hover {
        background-color: #E2E0D8;
    }

    /* Star Rating Gold Color */
    .star-gold {
        color: #EAA83B;
        font-size: 18px;
        letter-spacing: 2px;
    }
    .rating-score {
        font-size: 20px;
        font-weight: 700;
        color: #2b2b2b;
        margin-right: 6px;
    }
    .rating-meta {
        font-size: 13px;
        color: #666;
    }

    /* Review Card */
    .review-card {
        background: #FFFFFF;
        border: 1px solid #EAE8E2;
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
    .reviewer-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 10px;
    }
    .reviewer-avatar {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        object-fit: cover;
        border: 1px solid #e0e0e0;
    }
    .reviewer-name {
        font-weight: 600;
        font-size: 14px;
        color: #1e1e1e;
    }
    .review-date {
        font-size: 12px;
        color: #888888;
    }

    /* Recommendation card */
    .rec-card {
        background: #FFFFFF;
        border: 1px solid #EAE8E2;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        transition: transform 0.2s ease;
    }
    .rec-card:hover {
        transform: translateY(-3px);
    }
    .rec-title {
        font-weight: 600;
        font-size: 13px;
        margin-top: 8px;
        line-height: 1.2;
        color: #222;
    }
    .rec-author {
        font-size: 11px;
        color: #777;
        margin-top: 2px;
    }

    /* Custom button styling adjustments */
    div.stButton > button {
        border-radius: 6px;
        font-weight: 500;
    }

    /* Auth & Login Card Styling */
    .auth-container {
        background: #FFFFFF;
        border: 1px solid #EAE8E2;
        border-radius: 12px;
        padding: 28px 32px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        margin: 10px 0 25px 0;
    }

    /* Password Strength Meter */
    .strength-meter-bg {
        background: #EFEFEA;
        height: 8px;
        border-radius: 4px;
        overflow: hidden;
        margin: 8px 0 12px 0;
    }
    .strength-meter-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease, background-color 0.3s ease;
    }

    /* SSO Button Cards */
    .sso-badge {
        display: flex;
        align-items: center;
        gap: 10px;
        background: #FFFFFF;
        border: 1px solid #D5D3CC;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 10px;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s ease, border-color 0.2s ease;
    }
    .sso-badge:hover {
        background: #F7F6F2;
        border-color: #397858;
    }
    </style>
    """, unsafe_allow_html=True)
