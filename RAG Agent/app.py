import streamlit as st
from agent import ask_chess_agent


st.set_page_config(
    page_title="ChessKG Analyst",
    page_icon="♞",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Source+Sans+3:wght@400;600&display=swap');

    .stApp {
      background:
        radial-gradient(circle at 20% 20%, rgba(206, 157, 85, 0.18), transparent 35%),
        radial-gradient(circle at 80% 10%, rgba(86, 132, 187, 0.16), transparent 28%),
        linear-gradient(145deg, #10141b 0%, #17202b 45%, #0e1117 100%);
      color: #f3efe4;
      font-family: 'Source Sans 3', sans-serif;
    }

    .hero {
      border: 1px solid rgba(227, 193, 128, 0.35);
      border-radius: 16px;
      padding: 1rem 1.2rem;
      background: linear-gradient(120deg, rgba(20, 26, 35, 0.92), rgba(31, 24, 17, 0.9));
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
      margin-bottom: 1rem;
    }

    .hero h1 {
      font-family: 'Cinzel', serif;
      letter-spacing: 0.6px;
      margin: 0;
      font-size: 1.85rem;
      color: #f6dca8;
    }

    .hero p {
      margin: 0.4rem 0 0 0;
      color: #d8dbe0;
      font-size: 1rem;
    }

    [data-testid="stSidebar"] {
      background: linear-gradient(180deg, rgba(15, 20, 29, 0.98), rgba(27, 19, 12, 0.98));
      border-right: 1px solid rgba(227, 193, 128, 0.3);
    }

    [data-testid="stChatMessage"] {
      border: 1px solid rgba(243, 239, 228, 0.12);
      border-radius: 14px;
      background: rgba(23, 29, 38, 0.7);
      backdrop-filter: blur(2px);
    }

    .mini-board {
      display: grid;
      grid-template-columns: repeat(8, 12px);
      gap: 0;
      width: 96px;
      border: 1px solid rgba(227, 193, 128, 0.45);
      border-radius: 4px;
      overflow: hidden;
      margin-top: 0.4rem;
    }

    .sq-dark { background: #7f5f3a; height: 12px; }
    .sq-light { background: #f0d8b5; height: 12px; }

    .tip-card {
      border: 1px solid rgba(227, 193, 128, 0.35);
      background: rgba(27, 32, 42, 0.65);
      border-radius: 12px;
      padding: 0.75rem;
      margin-top: 0.8rem;
      color: #ece6d6;
    }

    .piece-carousel {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 1rem;
      margin-top: 1.2rem;
      margin-bottom: 0.8rem;
      font-size: 2rem;
    }

    .rotating-piece {
      animation: spin-piece 3s linear infinite;
      filter: drop-shadow(0 0 6px rgba(227, 193, 128, 0.5));
    }

    .piece-pulse {
      animation: piece-fade 2s ease-in-out infinite;
    }

    .piece-pulse:nth-child(1) { animation-delay: 0s; }
    .piece-pulse:nth-child(2) { animation-delay: 0.4s; }
    .piece-pulse:nth-child(3) { animation-delay: 0.8s; }

    @keyframes spin-piece {
      0% { transform: rotateY(0deg) rotateZ(0deg); }
      50% { transform: rotateY(180deg) rotateZ(10deg); }
      100% { transform: rotateY(360deg) rotateZ(0deg); }
    }

    @keyframes piece-fade {
      0%, 100% { opacity: 0.3; }
      50% { opacity: 1; }
    }

    .graph-label {
      font-size: 0.85rem;
      color: #c9bead;
      text-align: center;
      margin-bottom: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>ChessKG Analyst</h1>
      <p>Ask advanced questions about players, openings, ratings, dominance, and style similarity from your knowledge graph.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Opening Book")
    st.markdown(
        "- Try: *Who is most similar to Carlsen and what are their standard ratings?*\n"
        "- Try: *Does X dominate Y in head-to-head games?*\n"
        "- Try: *What is Hikaru's preferred opening as black?*"
    )
    st.markdown(
        "<div class='piece-carousel'>"
        "<span class='rotating-piece'>♞</span>"
        "<span class='piece-pulse'>♗</span>"
        "<span class='piece-pulse'>♕</span>"
        "<span class='piece-pulse'>♖</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="tip-card">
        <b>Grounded Answers</b><br/>
        Responses are tool-backed by the graph and embeddings based on top level major tournaments games in the 21st Century till September 2024. If data is missing, the assistant says so.
        </div>
        """,
        unsafe_allow_html=True,
    )

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Ready. Ask about ChessKG players, openings, ratings, or dominance relationships.",
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_prompt = st.chat_input("Ask a chess graph question...")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking through the position..."):
            prior_turns = [
                f"{m['role']}: {m['content']}" for m in st.session_state.messages[:-1]
            ]
            try:
                answer = ask_chess_agent(user_prompt, chat_history=prior_turns)
            except Exception as exc:
                answer = f"I hit an error while querying the graph: {exc}"
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
