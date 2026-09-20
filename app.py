from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


load_dotenv()

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data" / "standardized"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Vietnam Travel RAG",
    page_icon="🇻🇳",
    layout="wide",
)


# ============================================================
# HELPERS
# ============================================================

def count_documents() -> tuple[int, int]:
    """Đếm số tài liệu standardized hiện có."""

    legal_dir = DATA_DIR / "legal"
    news_dir = DATA_DIR / "news"

    legal_count = (
        len(list(legal_dir.glob("*.md")))
        if legal_dir.exists()
        else 0
    )

    news_count = (
        len(list(news_dir.glob("*.md")))
        if news_dir.exists()
        else 0
    )

    return legal_count, news_count


def run_rag(query: str, top_k: int) -> dict:
    """
    Adapter giữa Streamlit UI và RAG backend.

    Sau khi Task 10 hoàn thiện, UI sẽ gọi trực tiếp
    generate_with_citation().
    """

    try:
        from src.task10_generation import generate_with_citation

        return generate_with_citation(
            query=query,
            top_k=top_k,
        )

    except NotImplementedError:
        return {
            "answer": (
                "⚠️ **RAG backend chưa được kết nối hoàn chỉnh.**\n\n"
                "Giao diện đã sẵn sàng. Khi Task 9 và Task 10 "
                "được hoàn thiện, câu hỏi sẽ đi qua toàn bộ pipeline "
                "retrieval → reranking → generation → citation."
            ),
            "sources": [],
            "retrieval_source": "backend_not_ready",
        }

    except Exception as error:
        return {
            "answer": (
                "⚠️ Backend RAG hiện chưa thể xử lý câu hỏi."
            ),
            "sources": [],
            "retrieval_source": "error",
            "error": str(error),
        }


def get_source_title(source: dict, index: int) -> str:
    metadata = source.get("metadata", {}) or {}

    return (
        metadata.get("title")
        or source.get("title")
        or f"Nguồn {index}"
    )


def get_source_url(source: dict) -> str:
    metadata = source.get("metadata", {}) or {}

    return (
        metadata.get("source")
        or metadata.get("url")
        or source.get("source")
        or source.get("url")
        or ""
    )


def get_source_content(source: dict) -> str:
    return (
        source.get("content")
        or source.get("text")
        or source.get("chunk")
        or ""
    )


def display_sources(
    sources: list[dict],
    show_details: bool = True,
) -> None:
    """Hiển thị citation và evidence."""

    if not sources:
        return

    st.markdown("---")
    st.markdown(
        f"### 📚 Nguồn tham khảo ({len(sources)})"
    )

    for index, source in enumerate(sources, 1):

        title = get_source_title(
            source,
            index,
        )

        url = get_source_url(source)

        content = get_source_content(source)

        score = source.get("score")

        retrieval_method = (
            source.get("retrieval_method")
            or source.get("method")
            or "unknown"
        )

        label = f"[{index}] {title}"

        with st.expander(label):

            # -------------------------------
            # Basic source info
            # -------------------------------

            if url:
                if str(url).startswith(
                    ("http://", "https://")
                ):
                    st.markdown(
                        f"🔗 [Mở nguồn gốc]({url})"
                    )
                else:
                    st.markdown(
                        f"📄 **Source:** `{url}`"
                    )

            # -------------------------------
            # Retrieval details
            # -------------------------------

            if show_details:

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(
                        "**Retrieval method**"
                    )
                    st.code(
                        retrieval_method,
                        language=None,
                    )

                with col2:
                    st.markdown(
                        "**Retrieval score**"
                    )

                    if isinstance(
                        score,
                        (int, float),
                    ):
                        st.code(
                            f"{score:.4f}",
                            language=None,
                        )
                    else:
                        st.code(
                            "N/A",
                            language=None,
                        )

            # -------------------------------
            # Retrieved chunk
            # -------------------------------

            if content:
                st.markdown(
                    "#### 🔎 Chunk được truy xuất"
                )

                st.info(content)

            else:
                st.caption(
                    "Không có nội dung chunk để hiển thị."
                )


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================================
# SIDEBAR
# ============================================================

legal_count, news_count = count_documents()

with st.sidebar:

    st.title("🇻🇳 Vietnam Travel RAG")

    st.caption(
        "Trợ lý du lịch Việt Nam sử dụng "
        "Retrieval-Augmented Generation"
    )

    st.divider()

    st.subheader("⚙️ Cấu hình Retrieval")

    top_k = st.slider(
        "Số đoạn ngữ cảnh (Top-K)",
        min_value=3,
        max_value=10,
        value=5,
        step=1,
        help=(
            "Số chunk liên quan nhất được lấy từ "
            "knowledge base để tạo câu trả lời."
        ),
    )

    show_retrieval_details = st.toggle(
        "Hiển thị chi tiết retrieval",
        value=True,
        help=(
            "Hiển thị retrieval method, score "
            "và nội dung chunk mà hệ thống tìm được."
        ),
    )

    st.divider()

    st.subheader("📚 Knowledge Base")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Pháp lý",
            legal_count,
        )

    with col2:
        st.metric(
            "Du lịch",
            news_count,
        )

    st.caption(
        f"Tổng cộng: "
        f"{legal_count + news_count} tài liệu"
    )

    st.divider()

    st.subheader("🔎 RAG Pipeline")

    st.markdown(
        """
        **User Query**

        ↓

        **Semantic Search + BM25**

        ↓

        **RRF Reranking**

        ↓

        **PageIndex Fallback**

        ↓

        **LLM Generation**

        ↓

        **Answer + Citation**
        """
    )

    st.divider()

    if st.button(
        "🗑️ Xóa lịch sử chat",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()


# ============================================================
# MAIN
# ============================================================

st.title("🇻🇳 Vietnam Travel Assistant")

st.caption(
    "Hỏi về lịch trình, địa điểm, ẩm thực "
    "và quy định liên quan đến du lịch Việt Nam."
)


# ============================================================
# SAMPLE QUESTIONS
# ============================================================

if not st.session_state.messages:

    st.markdown("### 💡 Câu hỏi gợi ý")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🏖️ Lịch trình Đà Nẵng 3 ngày",
            use_container_width=True,
        ):
            st.session_state.pending_question = (
                "Gợi ý cho tôi lịch trình du lịch "
                "Đà Nẵng trong 3 ngày."
            )

        if st.button(
            "🍜 Hà Nội có món gì nên thử?",
            use_container_width=True,
        ):
            st.session_state.pending_question = (
                "Những món ăn nào ở Hà Nội "
                "mà khách du lịch nên thử?"
            )

    with col2:

        if st.button(
            "⛰️ Ninh Bình có gì nổi bật?",
            use_container_width=True,
        ):
            st.session_state.pending_question = (
                "Du lịch Ninh Bình có những "
                "trải nghiệm nào nổi bật?"
            )

        if st.button(
            "📜 Nghĩa vụ của khách du lịch",
            use_container_width=True,
        ):
            st.session_state.pending_question = (
                "Theo quy định pháp luật, "
                "khách du lịch có những nghĩa vụ gì?"
            )


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(
            message["content"]
        )

        if message["role"] == "assistant":

            retrieval_source = message.get(
                "retrieval_source"
            )

            if retrieval_source:
                st.caption(
                    "🔎 Retrieval source: "
                    f"{retrieval_source}"
                )

            display_sources(
                message.get("sources", []),
                show_details=show_retrieval_details,
            )


# ============================================================
# INPUT
# ============================================================

pending_question = st.session_state.pop(
    "pending_question",
    None,
)

query = st.chat_input(
    "Ví dụ: Tôi nên đi đâu ở Đà Nẵng trong 3 ngày?"
)

if pending_question:
    query = pending_question


# ============================================================
# RUN CHAT
# ============================================================

if query:

    # ---------------- USER ----------------

    user_message = {
        "role": "user",
        "content": query,
    }

    st.session_state.messages.append(
        user_message
    )

    with st.chat_message("user"):
        st.markdown(query)

    # --------------- ASSISTANT ------------

    with st.chat_message("assistant"):

        with st.spinner(
            "Đang tìm kiếm trong knowledge base..."
        ):

            result = run_rag(
                query=query,
                top_k=top_k,
            )

        answer = result.get(
            "answer",
            "Không tìm thấy câu trả lời.",
        )

        sources = result.get(
            "sources",
            [],
        )

        retrieval_source = result.get(
            "retrieval_source",
            "unknown",
        )

        st.markdown(answer)

        if sources:
            st.caption(
                f"📚 Sử dụng "
                f"{len(sources)} nguồn/chunk"
            )

        st.caption(
            f"🔎 Retrieval source: "
            f"{retrieval_source}"
        )

        display_sources(
            sources,
            show_details=show_retrieval_details,
        )

        if result.get("error"):

            with st.expander(
                "⚠️ Chi tiết lỗi backend"
            ):
                st.code(
                    result["error"]
                )

    # Save assistant result

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "retrieval_source": retrieval_source,
        }
    )