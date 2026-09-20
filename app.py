"""
RAG Chatbot — Streamlit UI cho pipeline hybrid retrieval + generation có citation.

Chạy: streamlit run app.py
"""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="RAG Chatbot — Hỏi đáp tài liệu",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ──────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []  # list[dict]: role, content, sources, retrieval_source

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://placehold.co/280x60/1e293b/e2e8f0?text=RAG+Chatbot", use_container_width=True)
    st.markdown("---")

    st.subheader("⚙️ Cấu hình Retrieval")
    top_k = st.slider("Số chunks (top_k)", min_value=3, max_value=10, value=5, step=1,
                       help="Số lượng chunks được đưa vào context của LLM")
    use_reranking = st.toggle("Hybrid + RRF", value=True,
                               help="Bật: dùng BM25 + Dense + RRF. Tắt: dense-only")

    st.markdown("---")
    st.subheader("🤖 LLM Provider")
    provider_display = os.getenv("LLM_PROVIDER", "openai").upper()
    model_display = os.getenv("LLM_MODEL", "(default)") or "(default)"
    st.info(f"**Provider:** {provider_display}\n\n**Model:** {model_display}")
    st.caption("Thay đổi trong file `.env` rồi restart app.")

    st.markdown("---")
    if st.button("🗑️ Xoá lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.caption("RAG Pipeline — K4 Lab · Task 10 + Streamlit UI")

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style='margin-bottom:0'>📚 RAG Chatbot</h1>
    <p style='color:#94a3b8;margin-top:4px'>
        Đặt câu hỏi — chatbot sẽ trả lời dựa trên tài liệu của nhóm và trích dẫn nguồn cụ thể.
    </p>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

# ── Chat history ─────────────────────────────────────────────────────────────
def _render_sources(sources: list[dict]) -> None:
    """Hiển thị expander chứa các chunk nguồn."""
    if not sources:
        return
    with st.expander(f"📎 {len(sources)} nguồn đã dùng", expanded=False):
        for idx, chunk in enumerate(sources, 1):
            meta = chunk.get("metadata", {}) or {}
            score = chunk.get("score", 0.0)
            method = chunk.get("retrieval_method", "?")
            title = meta.get("title", "Không rõ tiêu đề")
            source = meta.get("source", "Không rõ nguồn")
            url = meta.get("url")
            content_preview = chunk.get("content", "")[:300]

            st.markdown(
                f"**[{idx}] {title}**  \n"
                f"`{source}` &nbsp;·&nbsp; score: `{score:.4f}` &nbsp;·&nbsp; method: `{method}`"
                + (f"  \n🔗 [{url}]({url})" if url else "")
            )
            st.markdown(
                f"> {content_preview}{'…' if len(chunk.get('content','')) > 300 else ''}",
            )
            if idx < len(sources):
                st.markdown("---")


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            _render_sources(msg.get("sources", []))
            if msg.get("retrieval_source") and msg["retrieval_source"] != "none":
                st.caption(f"🔍 Retrieval: **{msg['retrieval_source']}** · top_k={msg.get('top_k', top_k)}")

# ── Input ─────────────────────────────────────────────────────────────────────
query = st.chat_input("Nhập câu hỏi của bạn…")

if query:
    # Hiển thị câu hỏi người dùng
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Gọi RAG pipeline
    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm và tạo câu trả lời…"):
            try:
                from src.task10_generation import generate_with_citation
                from src.task9_retrieval_pipeline import retrieve

                # Gọi retrieval với cấu hình từ sidebar
                chunks = retrieve(query, top_k=top_k, use_reranking=use_reranking)

                # Gọi generation (dùng chunks đã lấy — gọi lại qua generate để nhất quán)
                result = generate_with_citation(query, top_k=top_k)
                answer = result["answer"]
                sources = result["sources"]
                retrieval_source = result["retrieval_source"]

            except NotImplementedError as exc:
                answer = f"⚠️ Chưa implement: `{exc}`"
                sources = []
                retrieval_source = "none"
            except Exception as exc:
                answer = (
                    "❌ Có lỗi xảy ra khi xử lý câu hỏi của bạn. "
                    "Vui lòng kiểm tra API key và thử lại.\n\n"
                    f"Chi tiết: `{exc}`"
                )
                sources = []
                retrieval_source = "none"

        st.markdown(answer)
        _render_sources(sources)
        if retrieval_source and retrieval_source != "none":
            st.caption(f"🔍 Retrieval: **{retrieval_source}** · top_k={top_k} · hybrid={use_reranking}")

    # Lưu vào session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "retrieval_source": retrieval_source,
        "top_k": top_k,
    })
