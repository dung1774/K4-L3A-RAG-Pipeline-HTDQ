"""
Task 7 — Reciprocal Rank Fusion.

RRF gộp nhiều bảng xếp hạng mà không cộng trực tiếp cosine score với BM25
score. Công thức: RRF(d) = sum(1 / (k + rank)), rank bắt đầu từ 1.

Lưu ý: RRF score chỉ phản ánh thứ hạng, không dùng để quyết định fallback.

-> Dùng Jina hoặc self host hoặc bất cứ công cụ nào bạn quen
"""


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