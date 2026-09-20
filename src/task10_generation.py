"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import logging
import os

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()

logger = logging.getLogger(__name__)

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

# Ngưỡng score tối thiểu để coi context là "đủ bằng chứng". Nếu chunk tốt nhất
# không đạt ngưỡng này, coi như không đủ evidence và trả safe refusal thay vì
# đẩy context yếu vào LLM và trông chờ prompt tự chối.
MIN_RELEVANCE_SCORE = 0.2

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "")

SYSTEM_PROMPT = """Bạn là trợ lý AI chuyên nghiệp về Du lịch Việt Nam.
Nhiệm vụ của bạn là giải đáp thắc mắc của người dùng dựa trên Context tài liệu và ngữ cảnh hội thoại.

Yêu cầu:
1. Trả lời đầy đủ, chi tiết, mạch lạc, có cấu trúc rõ ràng (sử dụng danh sách gạch đầu dòng hoặc đánh số, in đậm các ý chính).
2. Mọi thông tin, điều luật, quy định, số liệu phải có trích dẫn nguồn cụ thể từ Context.
3. Duy trì mạch hội thoại liên tục, hiểu rõ ngữ cảnh của các câu hỏi tiếp nối trong phiên chat dài.
4. Nếu Context không chứa thông tin để trả lời, hãy từ chối lịch sự, không tự suy diễn hoặc bịa đặt thông tin."""

SAFE_REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."


def _safe_refusal_result() -> dict:
    """Kết quả từ chối chuẩn hoá, dùng ở mọi nhánh lỗi/không đủ evidence."""
    return {
        "answer": SAFE_REFUSAL,
        "sources": [],
        "retrieval_source": "none",
    }


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context.

    Không mutate list/dict đầu vào — chỉ trả về list mới với cùng tham chiếu
    tới các dict chunk gốc, thứ tự bị thay đổi để giảm lost-in-the-middle.
    """
    if len(chunks) <= 2:
        return list(chunks)
    front = chunks[::2]
    back = chunks[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label.

    Dùng .get() với fallback để một chunk thiếu metadata (ví dụ đến từ
    fallback PageIndex với schema khác) không làm crash toàn bộ pipeline.
    """
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {}) or {}
        title = metadata.get("title", "Không rõ tiêu đề")
        source = metadata.get("source", "Không rõ nguồn")
        content = chunk.get("content", "")
        parts.append(
            f"[Document {index} | Title: {title} | "
            f"Source: {source}]\n{content}"
        )
    return "\n\n---\n\n".join(parts)


def _extract_anthropic_text(response) -> str:
    """Lấy text block đầu tiên, không giả định content[0] luôn là text."""
    for block in response.content:
        if getattr(block, "type", None) == "text":
            return block.text
    raise ValueError("Anthropic response không chứa text block nào.")


def call_llm(
    system_prompt: str,
    user_message: str,
    chat_history: list[dict] = None,
) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình kèm lịch sử hội thoại."""
    if LLM_PROVIDER == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            for msg in chat_history[-6:]:
                role = msg.get("role")
                content = msg.get("content")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=LLM_MODEL or "gpt-4o-mini",
            messages=messages,
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI trả về nội dung rỗng.")
        return content

    elif LLM_PROVIDER == "gemini":
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        history_text = ""
        if chat_history:
            history_lines = [
                f"{m.get('role', 'user').capitalize()}: {m.get('content', '')}"
                for m in chat_history[-6:]
                if m.get("role") in ("user", "assistant") and m.get("content")
            ]
            if history_lines:
                history_text = "Lịch sử trao đổi trước đó:\n" + "\n".join(history_lines) + "\n\n"

        full_message = history_text + user_message
        response = client.models.generate_content(
            model=LLM_MODEL or "gemini-2.5-flash",
            contents=full_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
                top_p=TOP_P,
            )
        )
        text = response.text
        if not text:
            raise ValueError("Gemini trả về nội dung rỗng (có thể bị chặn bởi safety filter).")
        return text

    elif LLM_PROVIDER == "anthropic":
        from anthropic import Anthropic
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        messages = []
        if chat_history:
            for msg in chat_history[-6:]:
                role = msg.get("role")
                content = msg.get("content")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        response = client.messages.create(
            model=LLM_MODEL or "claude-3-5-sonnet-latest",
            system=system_prompt,
            messages=messages,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=2048,
        )
        text = _extract_anthropic_text(response)
        if not text:
            raise ValueError("Anthropic trả về nội dung rỗng.")
        return text

    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


def _has_sufficient_evidence(chunks: list[dict]) -> bool:
    """Kiểm tra context có đủ bằng chứng hay không dựa trên score cao nhất.

    Lưu ý: Nếu kết quả đến từ 'hybrid' (RRF), điểm số là tổng nghịch đảo thứ hạng
    (thường trong khoảng 0.01 - 0.035), không so sánh trực tiếp với ngưỡng cosine 0.2
    vì việc kiểm định threshold cosine đã được thực hiện ở Task 9.
    """
    if not chunks:
        return False

    first_method = chunks[0].get("retrieval_method")
    if first_method == "hybrid":
        return True

    scores = [c["score"] for c in chunks if isinstance(c.get("score"), (int, float))]
    if not scores:
        return True
    return max(scores) >= MIN_RELEVANCE_SCORE


def generate_from_chunks(
    query: str,
    chunks: list[dict],
    chat_history: list[dict] = None,
) -> dict:
    """Tạo câu trả lời có citation từ danh sách chunks đã retrieve và lịch sử hội thoại."""
    if not chunks:
        return _safe_refusal_result()

    if not _has_sufficient_evidence(chunks):
        logger.info("Không đủ evidence cho query=%r (score dưới ngưỡng).", query)
        return _safe_refusal_result()

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    user_message = f"Context:\n{context}\n\nQuestion: {query}"

    try:
        answer = call_llm(SYSTEM_PROMPT, user_message, chat_history=chat_history)
    except Exception:
        logger.exception("LLM provider (%s) lỗi cho query=%r", LLM_PROVIDER, query)
        return _safe_refusal_result()

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": chunks[0].get("retrieval_method", "unknown"),
    }


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult.

    Ba nhánh dẫn đến safe refusal (answer cố định, sources=[],
    retrieval_source="none"):
      1. Không retrieve được chunk nào.
      2. Chunk tốt nhất không đạt ngưỡng liên quan tối thiểu.
      3. Gọi LLM thất bại (lỗi provider/network/response rỗng).
    """
    try:
        chunks = retrieve(query, top_k=top_k)
    except Exception:
        logger.exception("Retrieval pipeline thất bại cho query=%r", query)
        return _safe_refusal_result()

    return generate_from_chunks(query, chunks)


if __name__ == "__main__":
    print(generate_with_citation("test query"))