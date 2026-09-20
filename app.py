"""
RAG Chatbot — Streamlit UI cho pipeline hybrid retrieval + generation có citation.
Dự án: Vietnam Tourism RAG Pipeline (K4-L3A)

Chạy: streamlit run app.py
"""

import os
import time

import streamlit as st
from dotenv import load_dotenv

from src.task9_retrieval_pipeline import retrieve
from src.task10_generation import SAFE_REFUSAL, generate_from_chunks

load_dotenv()

# ── Cấu hình trang ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Vietnam Tourism RAG — Chatbot",
    page_icon="🇻🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS cho Giao diện Hiện Đại & Sang Trọng ──────────────────────────
st.markdown(
    """
    <style>
    /* Font & container spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header card */
    .app-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .app-header h1 {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .app-header p {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-top: 6px;
        margin-bottom: 0;
    }

    /* Badges cho Retrieval Method */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-hybrid {
        background-color: #064e3b;
        color: #34d399;
        border: 1px solid #059669;
    }
    .badge-dense {
        background-color: #1e1b4b;
        color: #a5b4fc;
        border: 1px solid #4f46e5;
    }
    .badge-bm25 {
        background-color: #451a03;
        color: #fdba74;
        border: 1px solid #ea580c;
    }
    .badge-pageindex {
        background-color: #3b0764;
        color: #d8b4fe;
        border: 1px solid #9333ea;
    }
    .badge-score {
        background-color: #1e293b;
        color: #cbd5e1;
        border: 1px solid #475569;
        font-family: monospace;
    }

    /* Source item card */
    .source-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }
    .source-title {
        font-weight: 600;
        color: #f1f5f9;
        font-size: 0.95rem;
        margin-bottom: 4px;
    }
    .source-meta {
        font-size: 0.8rem;
        color: #94a3b8;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
        margin-bottom: 8px;
    }
    .source-content {
        font-size: 0.88rem;
        color: #cbd5e1;
        border-left: 3px solid #64748b;
        padding-left: 10px;
        margin: 6px 0;
        line-height: 1.45;
        font-style: italic;
    }

    /* Execution stats bar */
    .stats-bar {
        display: flex;
        gap: 12px;
        font-size: 0.78rem;
        color: #94a3b8;
        margin-top: 6px;
        align-items: center;
    }
    .stats-item {
        background: #1e293b;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #334155;
    }

    /* Safe Refusal Box */
    .safe-refusal-box {
        background-color: #451a03;
        border-left: 4px solid #f97316;
        padding: 10px 14px;
        border-radius: 6px;
        color: #ffedd5;
        font-size: 0.9rem;
        margin-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state defaults ──────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []  # list[dict]: role, content, sources, retrieval_source, latency, top_k

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    # Sidebar Header Card
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                    padding: 16px; border-radius: 10px; border: 1px solid #334155; 
                    margin-bottom: 16px; text-align: center;">
            <div style="font-size: 26px; margin-bottom: 4px;">🇻🇳 🏛️ 🏖️</div>
            <div style="font-weight: 700; font-size: 16px; color: #f8fafc;">Vietnam Tourism RAG</div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">Hybrid Retrieval · Citation · Grounded AI</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("⚙️ Cấu hình Retrieval")
    top_k = st.slider(
        "Số lượng chunks (top_k)",
        min_value=3,
        max_value=15,
        value=6,
        step=1,
        help="Số lượng chunks được đưa vào context của LLM (chọn cao hơn nếu muốn câu trả lời sâu và rộng hơn)",
    )
    use_reranking = st.toggle(
        "Hybrid + RRF Fusion",
        value=True,
        help="Bật: Kết hợp Dense (ChromaDB) + Sparse (BM25) qua RRF. Tắt: Chỉ dùng Dense search.",
    )

    st.markdown("---")
    st.subheader("💬 Phiên Hội Thoại")
    user_turn_count = len([m for m in st.session_state.messages if m["role"] == "user"])
    st.markdown(f"- **Lượt trao đổi:** `{user_turn_count}` lượt")
    st.markdown("- **Bộ nhớ ngữ cảnh:** `Đang bật (Nhớ 6 lượt gần nhất)`")

    if st.session_state.messages:
        # Chuẩn bị file tải xuống lịch sử hội thoại dạng Markdown
        chat_export = "# Lịch Sử Hội Thoại — Vietnam Tourism RAG Chatbot\n\n"
        for m in st.session_state.messages:
            r_name = "👤 **Người dùng:**" if m["role"] == "user" else "🤖 **Trợ lý RAG:**"
            chat_export += f"{r_name}\n\n{m['content']}\n\n"
            if m.get("sources"):
                chat_export += f"> *Nguồn tài liệu ({len(m['sources'])} chunks):*\n"
                for s in m["sources"]:
                    meta = s.get("metadata", {}) or {}
                    title = meta.get("title", "Tài liệu")
                    src = meta.get("source", "")
                    chat_export += f"> - **{title}** (`{src}`)\n"
                chat_export += "\n"
            chat_export += "---\n\n"

        st.download_button(
            "📥 Tải lịch sử chat (.md)",
            data=chat_export,
            file_name="vietnam_tourism_rag_chat.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.markdown("---")
    st.subheader("🤖 Hệ Thống & Mô Hình")
    provider = os.getenv("LLM_PROVIDER", "openai").upper()
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    emb_provider = os.getenv("EMBEDDING_PROVIDER", "openai").upper()
    emb_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    st.markdown(
        f"""
        - **LLM:** `{provider}` ({model})
        - **Embedding:** `{emb_provider}` ({emb_model})
        - **Vector DB:** `ChromaDB` (532 chunks)
        - **Sparse Search:** `BM25Okapi` (Lucene IDF)
        """
    )

    st.markdown("---")
    st.subheader("📚 Dữ Liệu Nạp Sẵn")
    st.caption("3 Văn bản Pháp luật (Luật Du lịch 2017, Nghị định, Quy định) & 10 Bài báo du lịch địa phương.")

    st.markdown("---")
    if st.button("🗑️ Xoá lịch sử hội thoại", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.rerun()

    st.caption("Day 8 RAG Pipeline · Group K4-L3A")

# ── Header Chính ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="app-header">
        <h1><span>📚</span> Trợ Lý Hỏi Đáp Du Lịch Việt Nam</h1>
        <p>Hệ thống RAG thông minh trả lời dựa trên kho văn bản pháp luật & bài báo du lịch chính thức, có bộ nhớ hội thoại xuyên suốt phiên chat.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def _get_method_badge(method: str) -> str:
    """Trả về thẻ HTML badge cho phương thức retrieval."""
    method_lower = (method or "").lower()
    if "hybrid" in method_lower:
        return '<span class="badge badge-hybrid">🟢 Hybrid (Dense + BM25 RRF)</span>'
    elif "dense" in method_lower:
        return '<span class="badge badge-dense">🔵 Dense Search</span>'
    elif "bm25" in method_lower:
        return '<span class="badge badge-bm25">🟠 BM25 Lexical</span>'
    elif "pageindex" in method_lower:
        return '<span class="badge badge-pageindex">🟣 PageIndex Fallback</span>'
    return f'<span class="badge badge-score">{method}</span>'


def _render_sources(sources: list[dict]) -> None:
    """Hiển thị expander chứa các chunk nguồn có định dạng đẹp mắt."""
    if not sources:
        return

    with st.expander(f"📎 Xem {len(sources)} nguồn tài liệu đã sử dụng", expanded=False):
        for idx, chunk in enumerate(sources, 1):
            meta = chunk.get("metadata", {}) or {}
            score = chunk.get("score", 0.0)
            method = chunk.get("retrieval_method", "unknown")
            title = meta.get("title") or meta.get("source") or "Tài liệu không tiêu đề"
            source_file = meta.get("source", "Không rõ nguồn")
            url = meta.get("url")
            content = chunk.get("content", "").strip()
            content_preview = content[:320] + ("…" if len(content) > 320 else "")

            score_str = f"{score:.4f}" if isinstance(score, (int, float)) else str(score)
            method_badge = _get_method_badge(method)
            url_link = f' &nbsp;·&nbsp; 🔗 <a href="{url}" target="_blank" style="color:#38bdf8;">Đường dẫn gốc</a>' if url else ""

            st.markdown(
                f"""
                <div class="source-card">
                    <div class="source-title">[{idx}] {title}</div>
                    <div class="source-meta">
                        {method_badge}
                        <span class="badge badge-score">Score: {score_str}</span>
                        <span>📄 <code>{source_file}</code></span>
                        {url_link}
                    </div>
                    <div class="source-content">"{content_preview}"</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ── Render Lịch Sử Chat ─────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            sources = msg.get("sources", [])
            _render_sources(sources)

            retrieval_source = msg.get("retrieval_source")
            latency = msg.get("latency")
            msg_top_k = msg.get("top_k", top_k)
            is_rerank = msg.get("use_reranking", True)

            if retrieval_source and retrieval_source != "none":
                latency_str = f"⏱️ {latency:.2f}s &nbsp;·&nbsp; " if latency else ""
                method_name = "Hybrid (RRF)" if is_rerank else "Dense-only"
                st.markdown(
                    f"""
                    <div class="stats-bar">
                        <span class="stats-item">{latency_str}🔍 Retrieval: <b>{retrieval_source}</b> ({method_name})</span>
                        <span class="stats-item">📚 {len(sources)} / top_k={msg_top_k}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif retrieval_source == "none":
                st.markdown(
                    """
                    <div class="safe-refusal-box">
                        🛡️ <b>Safe Refusal:</b> Hệ thống từ chối do không tìm thấy đủ dữ kiện xác thực trong tài liệu quy định.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ── Gợi ý Câu Hỏi Mẫu khi chưa chat ──────────────────────────────────────────
if len(st.session_state.messages) == 0:
    st.markdown("#### 💡 Câu hỏi gợi ý để thử nghiệm:")
    col1, col2 = st.columns(2)

    sample_questions = [
        ("🏛️ Pháp luật du lịch", "Điều kiện cấp thẻ hướng dẫn viên du lịch quốc tế là gì?"),
        ("🏖️ Lịch trình thực tế", "Gợi ý lịch trình du lịch Đà Nẵng 3 ngày 2 đêm chi tiết?"),
        ("⚠️ Quy định an toàn", "Quy định an toàn đối với các sản phẩm du lịch mạo hiểm?"),
        ("🛡️ Thử nghiệm Safe Refusal", "Thời tiết ở Tokyo hôm nay thế nào?"),
    ]

    for i, (label, q_text) in enumerate(sample_questions):
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            if st.button(f"{label}\n\n*{q_text}*", key=f"sample_{i}", use_container_width=True):
                st.session_state.pending_query = q_text
                st.rerun()


# ── Xử Lý Input ─────────────────────────────────────────────────────────────
user_input = st.chat_input("Nhập câu hỏi về du lịch hoặc quy chế pháp lý…")

# Kiểm tra nếu người dùng chọn câu hỏi mẫu
active_query = None
if user_input:
    active_query = user_input
elif st.session_state.pending_query:
    active_query = st.session_state.pending_query
    st.session_state.pending_query = None

if active_query:
    # 1. Lưu lại các lượt hội thoại trước đó trước khi thêm câu mới vào
    previous_history = list(st.session_state.messages)

    # 2. Thêm câu hỏi người dùng vào lịch sử hiển thị
    st.session_state.messages.append({"role": "user", "content": active_query})
    with st.chat_message("user"):
        st.markdown(active_query)

    # 3. Xử lý trả lời từ RAG Pipeline kèm ngữ cảnh hội thoại
    with st.chat_message("assistant"):
        with st.spinner("Đang truy vấn tài liệu và sinh câu trả lời có trích dẫn…"):
            start_time = time.time()
            try:
                # Nếu là câu hỏi tiếp nối ngắn trong phiên chat dài, bổ sung từ khoá từ câu hỏi gần nhất
                retrieval_query = active_query
                if previous_history:
                    past_user_qs = [m["content"] for m in previous_history if m["role"] == "user"]
                    if past_user_qs and len(active_query.split()) < 8:
                        retrieval_query = f"{past_user_qs[-1]} {active_query}"

                # Bước 1: Retrieval theo cấu hình sidebar
                chunks = retrieve(retrieval_query, top_k=top_k, use_reranking=use_reranking)

                # Bước 2: Generation từ chunks đã retrieve kèm chat_history
                result = generate_from_chunks(active_query, chunks, chat_history=previous_history)

                answer = result.get("answer", SAFE_REFUSAL)
                sources = result.get("sources", [])
                retrieval_source = result.get("retrieval_source", "none")
                latency = time.time() - start_time

            except NotImplementedError as exc:
                answer = f"⚠️ Chưa triển khai: `{exc}`"
                sources = []
                retrieval_source = "none"
                latency = time.time() - start_time
            except Exception as exc:
                answer = (
                    "❌ Có lỗi xảy ra trong quá trình xử lý câu hỏi. "
                    "Vui lòng kiểm tra lại cấu hình API key trong `.env`.\n\n"
                    f"**Chi tiết:** `{exc}`"
                )
                sources = []
                retrieval_source = "none"
                latency = time.time() - start_time

        # Hiển thị câu trả lời
        st.markdown(answer)
        _render_sources(sources)

        # Hiển thị thông số thực thi
        if retrieval_source and retrieval_source != "none":
            method_name = "Hybrid (RRF)" if use_reranking else "Dense-only"
            st.markdown(
                f"""
                <div class="stats-bar">
                    <span class="stats-item">⏱️ {latency:.2f}s &nbsp;·&nbsp; 🔍 Retrieval: <b>{retrieval_source}</b> ({method_name})</span>
                    <span class="stats-item">📚 {len(sources)} / top_k={top_k}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif retrieval_source == "none":
            st.markdown(
                """
                <div class="safe-refusal-box">
                    🛡️ <b>Safe Refusal:</b> Hệ thống từ chối do không tìm thấy đủ dữ kiện xác thực trong tài liệu quy định.
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 4. Lưu câu trả lời trợ lý vào session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "retrieval_source": retrieval_source,
        "latency": latency,
        "top_k": top_k,
        "use_reranking": use_reranking,
    })
