# Hướng Dẫn Kỹ Thuật Cho TV3 — Hybrid Retrieval & Fallback

## 1. Tổng Quan Vai Trò & Nhiệm Vụ

**Thành viên 3 (TV3)** chịu trách nhiệm tầng **Hybrid Retrieval & Fallback (Task 6 đến Task 9)**:
- **Task 6 (`src/task6_lexical_search.py`)**: Tìm kiếm từ khóa BM25 (Lexical Search).
- **Task 7 (`src/task7_reranking.py`)**: Hợp nhất thứ hạng Reciprocal Rank Fusion (RRF).
- **Task 8 (`src/task8_pageindex_vectorless.py`)**: Cơ chế tìm kiếm dự phòng (Vectorless Fallback).
- **Task 9 (`src/task9_retrieval_pipeline.py`)**: Ghép nối pipeline tìm kiếm tổng hợp và hiệu chỉnh threshold.

---

## 2. Chiến Lược Triển Khai (Làm Việc Độc Lập Với TV2)

> [!IMPORTANT]
> **Quy tắc làm việc song song:**
> - **TV2** phụ trách Task 4 (Chunking, Embedding & ChromaDB) và Task 5 (Dense Search).
> - **TV3** có thể **hoàn thành 100% code và chạy pass test contract ngay lập tức** mà không cần đợi TV2, vì `tests/test_contracts.py` đã mock dữ liệu đầu vào.
> - Khi TV2 làm xong, TV3 chỉ cần ghép nối với collection thật và hiệu chỉnh ngưỡng `score_threshold`.

---

## 3. Chi Tiết Từng Task & Code Mẫu Chuẩn Contract

### Task 6: BM25 Lexical Search (`src/task6_lexical_search.py`)

- **Mục tiêu**: Xử lý các truy vấn chứa từ khóa chính xác, thuật ngữ viết tắt, mã văn bản hoặc tên riêng mà dense search có thể bỏ sót.
- **Contract Schema**: Kết quả trả về phải là danh sách `SearchResult` với `retrieval_method="bm25"` và sắp xếp theo score giảm dần.

```python
import math
import numpy as np
from rank_bm25 import BM25Okapi

CORPUS: list[dict] = []


class BM25WithPositiveIDF(BM25Okapi):
    def _calc_idf(self, nd):
        # Dùng công thức Lucene BM25: log(1 + (N - n + 0.5)/(n + 0.5)) để IDF luôn > 0 (tránh IDF = 0 khi test trên corpus nhỏ)
        for word, freq in nd.items():
            self.idf[word] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ corpus chunks."""
    tokenized = [item["content"].lower().split() for item in corpus]
    return BM25WithPositiveIDF(tokenized)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if not CORPUS:
        return []

    bm25 = build_bm25_index(CORPUS)
    query_tokens = query.lower().split()
    scores = bm25.get_scores(query_tokens)

    # Sắp xếp các index có điểm cao nhất
    ranked_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in ranked_indices:
        score = float(scores[idx])
        if score <= 0:
            continue
        item = CORPUS[idx]
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": score,
            "metadata": item["metadata"],
            "retrieval_method": "bm25",
        })
    return results
```

---

### Task 7: Reciprocal Rank Fusion (RRF) (`src/task7_reranking.py`)

- **Mục tiêu**: Gộp danh sách kết quả từ nhiều bộ tìm kiếm (Dense và Sparse) dựa trên thứ hạng (rank) mà không phụ thuộc vào thang điểm khác biệt giữa cosine và BM25.
- **Công thức chuẩn**:
  $$Score_{RRF}(d) = \sum \frac{1}{k + rank}$$
  *(Với $k = 60$, $rank$ bắt đầu từ 1)*.
- **Contract Schema**: `retrieval_method="hybrid"`.

```python
def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse nhiều ranked lists và trả hybrid SearchResult."""
    rrf_scores: dict[str, float] = {}
    items_map: dict[str, dict] = {}

    for r_list in ranked_lists:
        for rank, item in enumerate(r_list, start=1):
            item_id = item["id"]
            rrf_scores[item_id] = rrf_scores.get(item_id, 0.0) + (1.0 / (k + rank))
            if item_id not in items_map:
                items_map[item_id] = item

    # Sắp xếp các item_id theo điểm RRF giảm dần
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

    results = []
    for item_id in sorted_ids[:top_k]:
        res = items_map[item_id].copy()
        res["score"] = rrf_scores[item_id]
        res["retrieval_method"] = "hybrid"
        results.append(res)

    return results


if __name__ == "__main__":
    print("RRF module ready.")
```

---

### Task 8: PageIndex Vectorless Fallback (`src/task8_pageindex_vectorless.py`)

- **Mục tiêu**: Tìm kiếm dự phòng không dùng vector (vectorless) khi vector search không tự tin hoặc câu hỏi ngoài miền dữ liệu vector.
- **Lưu ý quan trọng**: Đây là dịch vụ ngoài; cần có `try...except` để bảo vệ pipeline không bao giờ bị crash kể cả khi không có API key hoặc network timeout.

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    pass


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult với cơ chế xử lý lỗi an toàn."""
    try:
        if not PAGEINDEX_API_KEY:
            return []
        # Tích hợp SDK PageIndex nếu có API Key
        return []
    except Exception as error:
        print(f"PageIndex fallback warning: {error}")
        return []


if __name__ == "__main__":
    upload_documents()
```

---

### Task 9: Retrieval Pipeline Hoàn Chỉnh (`src/task9_retrieval_pipeline.py`)

- **Mục tiêu**: Nhạc trưởng điều phối toàn bộ luồng tìm kiếm:
  1. Lấy kết quả từ Dense và BM25.
  2. So sánh điểm **cosine score gốc của dense search** với `score_threshold`.
  3. Nếu dưới ngưỡng $\rightarrow$ Kích hoạt `pageindex_search` fallback.
  4. Nếu fallback lỗi/rỗng $\rightarrow$ An toàn quay lại trả kết quả Hybrid (không được làm sập chương trình).
  5. **RRF chỉ được fuse đúng 1 lần duy nhất**.

```python
from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search

# Giá trị threshold mặc định (sẽ hiệu chỉnh khi test với dữ liệu thật)
SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 5


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Trả về hybrid hoặc pageindex SearchResult."""
    # 1. Chạy dense và sparse search
    dense = semantic_search(query, top_k=top_k * 2)
    sparse = lexical_search(query, top_k=top_k * 2)

    # 2. Kiểm tra fallback bằng cosine score gốc của dense
    best_dense_score = dense[0]["score"] if dense else 0.0
    if best_dense_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback
        except Exception:
            pass  # Nếu fallback lỗi, fallback về hybrid

    # 3. Fuse 2 danh sách bằng RRF duy nhất 1 lần
    if use_reranking:
        hybrid = rerank_rrf([dense, sparse], top_k=top_k)
        return hybrid

    return dense[:top_k]


if __name__ == "__main__":
    for result in retrieve("test query", top_k=3):
        print(result)
```

---

## 4. Các Quy Tắc Sống Còn Để Đạt Điểm Tối Đa (Invariants)

1. **Schema nhất quán**: Tất cả kết quả trả về phải có đủ các trường:
   `id`, `content`, `score` (float), `metadata` (dict), `retrieval_method`.
2. **Quyết định Fallback**: Luôn dùng `dense[0]["score"]` (cosine similarity) để so với `score_threshold`. **Không bao giờ dùng điểm RRF** vì điểm RRF chỉ là tổng nghịch đảo thứ tự xếp hạng.
3. **RRF duy nhất 1 lần**: Không gọi RRF lồng nhau nhiều lần trong pipeline.
4. **Xử lý ngoại lệ**: Khi PageIndex bị mất mạng hoặc hết quota, hàm `retrieve` vẫn phải trả về hybrid kết quả hoặc danh sách rỗng, tuyệt đối không được crash app Streamlit.

---

## 5. Quy Trình Kiểm Thử Của TV3

### Bước 1: Kiểm thử Contract Tests (Chạy offline)
Ngay sau khi viết xong code của Task 6, 7, 8, 9, chạy lệnh sau:
```bash
pytest tests/test_contracts.py -k "lexical or rrf or retrieve" -v
```
**Mục tiêu**: 100% các test sau phải `PASSED`:
- `test_lexical_search_returns_bm25_contract`
- `test_rrf_uses_rank_deduplicates_and_marks_hybrid`
- `test_retrieve_uses_dense_score_for_fallback`
- `test_retrieve_fuses_once_when_dense_is_confident`
- `test_retrieve_survives_fallback_provider_error`

### Bước 2: Ghép nối & Calibrate Threshold (Khi TV2 làm xong)
1. Gán `CORPUS` của Task 6 bằng danh sách chunks đã tạo ở Task 4:
   ```python
   from src.task4_chunking_indexing import load_documents, chunk_documents
   import src.task6_lexical_search as lexical
   lexical.CORPUS = chunk_documents(load_documents())
   ```
2. Thử nghiệm truy vấn thực tế:
   - **Query trong domain** (ví dụ: *"Địa điểm du lịch nổi tiếng ở Đà Nẵng"*): Score dense cao $\rightarrow$ Pipeline trả về `hybrid`.
   - **Query ngoài domain** (ví dụ: *"Cách sửa động cơ máy bay Boeing 777"*): Score dense thấp hơn threshold $\rightarrow$ Pipeline kích hoạt fallback hoặc từ chối an toàn.
3. Điều chỉnh hằng số `SCORE_THRESHOLD` trong `src/task9_retrieval_pipeline.py` (thường trong khoảng `0.35` - `0.55`) sao cho phân tách rõ ràng giữa query đúng chủ đề và câu hỏi ngoài lề.
