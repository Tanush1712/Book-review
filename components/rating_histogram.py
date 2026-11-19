import streamlit as st


def render_rating_histogram(breakdown: dict, total_ratings: int, avg_rating: float):
    """
    Renders an authentic Goodreads-style rating histogram bar chart.
    breakdown: dict mapping str star ('1' to '5') to integer counts.
    """
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #EAE8E2; border-radius: 8px; padding: 16px 20px; margin: 15px 0;">
        <div style="display: flex; align-items: baseline; gap: 10px; margin-bottom: 12px;">
            <span style="font-size: 28px; font-weight: 700; color: #1e1e1e; font-family: 'Merriweather', serif;">{avg_rating:.2f}</span>
            <span style="color: #EAA83B; font-size: 20px;">{'★' * int(round(avg_rating))}{'☆' * (5 - int(round(avg_rating)))}</span>
            <span style="color: #666; font-size: 14px;">({total_ratings:,} total ratings)</span>
        </div>
    """, unsafe_allow_html=True)

    # Render each star level from 5 down to 1
    for star in [5, 4, 3, 2, 1]:
        count = breakdown.get(str(star), 0)
        pct = (count / total_ratings * 100) if total_ratings > 0 else 0
        
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 6px; font-size: 13px;">
            <span style="width: 50px; font-weight: 600; color: #444;">{star} stars</span>
            <div style="flex-grow: 1; background: #EFEFEA; height: 10px; border-radius: 5px; margin: 0 12px; overflow: hidden;">
                <div style="width: {pct:.1f}%; background-color: #397858; height: 100%; border-radius: 5px;"></div>
            </div>
            <span style="width: 90px; text-align: right; color: #777; font-size: 12px;">{count:,} ({pct:.0f}%)</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
