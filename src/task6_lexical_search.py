"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""


import math
import numpy as np
from rank_bm25 import BM25Okapi

CORPUS: list[dict] = []


class BM25WithPositiveIDF(BM25Okapi):
    def _calc_idf(self, nd):
        # Dùng công thức Lucene BM25: log(1 + (N - n + 0.5)/(n + 0.5)) để IDF luôn > 0
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


if __name__ == "__main__":
    for res in lexical_search("du lịch", top_k=3):
        print(res)