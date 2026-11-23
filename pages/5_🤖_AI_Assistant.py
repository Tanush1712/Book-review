import streamlit as st
from services.db_operations import ensure_initialized, get_current_user, get_user_shelves_with_counts
from services.ai_chat_service import (
    stream_chat_completion, get_api_key, get_quick_prompts, DEFAULT_MODEL
)
from components.styles import inject_custom_css
from components.auth_widget import render_sidebar_auth_widget

st.set_page_config(
    page_title="AI Book Assistant - BookLover",
    page_icon="🤖",
    layout="wide"
)

inject_custom_css()
ensure_initialized()

# Custom styles for chat chips and assistant banners
st.markdown("""
<style>
.chat-hero-banner {
    background: linear-gradient(135deg, #F3F1EB 0%, #FFFFFF 100%);
    border: 1px solid #E8E5DD;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 24px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.02);
}
.chat-hero-title {
    font-family: 'Merriweather', serif;
    font-size: 20px;
    font-weight: 700;
    color: #212121;
    margin-bottom: 6px;
}
.chat-hero-subtitle {
    font-size: 13.5px;
    color: #666;
    line-height: 1.5;
}
.prompt-chip-btn {
    text-align: left;
    margin-bottom: 8px;
}
.status-pill-active {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #E8F5E9;
    color: #2E7D32;
    border: 1px solid #C8E6C9;
    padding: 3px 10px;
    border-radius: 16px;
    font-size: 11px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# 1. Sidebar Setup
render_sidebar_auth_widget()
current_user = get_current_user()

with st.sidebar:
    st.markdown("### ⚙️ AI Engine Settings")
    st.markdown("""
    <div class="status-pill-active">
        <span>⚡ Groq Cloud Connected</span>
    </div>
    """, unsafe_allow_html=True)
    
    selected_model = st.selectbox(
        "Model",
        options=[DEFAULT_MODEL, "openai/gpt-oss-120b"],
        index=0,
        help="High-throughput reasoning model running on Groq LPU."
    )
    
    temperature = st.slider(
        "Creativity & Style",
        min_value=0.2,
        max_value=1.0,
        value=0.7,
        step=0.05,
        help="Lower values yield more direct facts; higher values give more expressive, literary descriptions."
    )
    
    with st.expander("🔑 Manage API Key", expanded=False):
        current_active_key = get_api_key()
        masked_key = (current_active_key[:7] + "..." + current_active_key[-4:]) if current_active_key else "None"
        st.caption(f"Active Key: `{masked_key}`")
        new_key = st.text_input("Override Groq API Key", type="password", key="custom_groq_api_key_input")
        if st.button("Apply New Key", use_container_width=True):
            if new_key.strip():
                st.session_state["custom_groq_api_key"] = new_key.strip()
                st.success("API Key updated!")
                st.rerun()

    st.markdown("<hr style='margin: 15px 0; border: none; border-top: 1px solid #ECEAE4;'>", unsafe_allow_html=True)
    
    # Reader Profile summary card
    st.markdown("### 📖 Reader Context")
    if current_user:
        st.markdown(f"**Curating for:** {current_user.display_name}")
        shelves = get_user_shelves_with_counts(current_user.id)
        shelf_summary = " · ".join([f"{s['name']}: {s['count']}" for s in shelves])
        st.caption(f"📚 {shelf_summary}")
    else:
        st.caption("Browsing as Guest. Log in to personalize recommendations with your bookshelves!")

    if st.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state["ai_messages"] = []
        st.rerun()

# 2. Main Page Header
st.markdown("""
<div class="brand-header">
    <a href="#" class="brand-logo">📚 BookLover AI</a>
    <span class="brand-tagline">Conversational book discovery, shelf-aware recommendations & spoiler-free discussions</span>
</div>
""", unsafe_allow_html=True)

# 3. Session State Initialization
if "ai_messages" not in st.session_state or not st.session_state["ai_messages"]:
    reader_name = current_user.display_name if current_user else "fellow reader"
    st.session_state["ai_messages"] = [
        {
            "role": "assistant",
            "content": (
                f"Hello **{reader_name}**! 📚 I'm your **BookLover AI** literary companion.\n\n"
                f"I'm tuned to your bookshelves and reading preferences. I can help you discover your next great read, "
                f"dive into book themes, unpack tropes, compare authors, or discuss plot points without spoiling the surprises.\n\n"
                f"What are you in the mood to read today?"
            )
        }
    ]

# 4. Hero Card & Quick Suggestion Chips (shown when few messages)
if len(st.session_state["ai_messages"]) <= 1:
    st.markdown(f"""
    <div class="chat-hero-banner">
        <div class="chat-hero-title">Welcome to your Literary Companion, {current_user.display_name if current_user else 'Reader'} ✨</div>
        <div class="chat-hero-subtitle">
            Powered by high-speed Groq AI and directly connected to your BookLover shelves and ratings. Pick a suggestion below or type any question:
        </div>
    </div>
    """, unsafe_allow_html=True)

    quick_prompts = get_quick_prompts()
    cols = st.columns(len(quick_prompts))
    for idx, qp in enumerate(quick_prompts):
        with cols[idx]:
            if st.button(qp["label"], key=f"chip_btn_{idx}", use_container_width=True):
                st.session_state["queued_prompt"] = qp["prompt"]
                st.rerun()

# 5. Handle Queued Prompts from Chips
user_prompt = None
if "queued_prompt" in st.session_state and st.session_state["queued_prompt"]:
    user_prompt = st.session_state.pop("queued_prompt")

# 6. Render Existing Chat Messages
for msg in st.session_state["ai_messages"]:
    avatar = "👤" if msg["role"] == "user" else "📚"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# 7. Chat Input
typed_prompt = st.chat_input("Ask for recommendations, compare books, analyze themes, or request spoiler-free reviews...")
if typed_prompt:
    user_prompt = typed_prompt

# 8. Processing User Input & Streaming Assistant Response
if user_prompt:
    # Append and display user message
    st.session_state["ai_messages"].append({"role": "user", "content": user_prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)

    # Stream assistant response
    with st.chat_message("assistant", avatar="📚"):
        # Format messages for the API (only user and assistant turns)
        api_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state["ai_messages"]
        ]
        
        generator = stream_chat_completion(
            messages=api_messages,
            user=current_user,
            api_key=get_api_key(),
            model=selected_model,
            temperature=temperature
        )
        
        full_response = st.write_stream(generator)

    # Save assistant response to session
    st.session_state["ai_messages"].append({"role": "assistant", "content": full_response})
