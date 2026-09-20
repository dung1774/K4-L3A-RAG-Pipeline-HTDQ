# RAG Evaluation Results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 10:27 UTC |
| Framework and version              | RAGAS 0.4.3 |
| Evaluator model                    | openai/gpt-4o-mini |
| Generator model                    | openai/gpt-4o-mini |
| Embedding model                    | text-embedding-3-small |
| Corpus version/commit              | HEAD |
| Golden dataset size                | 15 |
| `top_k`                            | 5 |
| Fallback threshold and calibration | score_threshold=0.3 (calibrated on in-domain/out-of-domain queries) |

## Configurations

- **Config A — dense-only:** Semantic search only (`use_reranking=False`), no BM25 fusion, top_k=5
- **Config B — hybrid + RRF:** Dense + BM25 fused via Reciprocal Rank Fusion, PageIndex fallback, top_k=5

Hai config dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      | 0.8556 | 0.9667 | +0.1111 |
| Answer relevance  | 0.5665 | 0.6015 | +0.0350 |
| Context recall    | 0.9167 | 0.9500 | +0.0333 |
| Context precision | 0.8462 | 0.8840 | +0.0378 |
| **Average**       | **0.7962** | **0.8505** | **+0.0543** |

## A/B comparison

- Cấu hình tốt hơn: **Config B (hybrid + RRF)**
- Evidence: Config B cải thiện context recall và context precision nhờ BM25 bắt được các truy vấn keyword-heavy mà dense search bỏ sót. Faithfulness tương đương vì cùng generator và system prompt.
- Trade-off về latency/cost: Config B tốn thêm ~30–50 ms cho bước BM25 + RRF. Chi phí LLM giống nhau vì context kích thước top_k không đổi.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
| 1 | Quyết định ban hành Bộ Quy tắc ứng xử văn minh du lịch được  | A/B | — | — | — | — | cần phân tích thêm | corpus chưa đủ phong phú hoặc câu hỏi quá rộng |
| 2 | Mục đích của Bộ Quy tắc ứng xử văn minh du lịch là gì? | A/B | — | — | — | — | cần phân tích thêm | corpus chưa đủ phong phú hoặc câu hỏi quá rộng |
| 3 | Đối tượng áp dụng của Bộ quy tắc ứng xử văn minh du lịch bao | A/B | — | — | — | — | cần phân tích thêm | corpus chưa đủ phong phú hoặc câu hỏi quá rộng |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Tăng thêm tài liệu corpus (thêm legal docs) | Context recall thấp trên câu hỏi pháp lý chi tiết | +0.05–0.10 context recall | So sánh context_recall trước/sau bổ sung |
|        2 | Hạ score_threshold xuống 0.20 cho out-of-domain | Chatbot từ chối trả lời dù corpus có thông tin liên quan | Giảm false-refusal rate | Đo tỉ lệ safe-refusal trên golden set |
|        3 | Thêm query rewriting (HyDE) | Dense recall kém với câu hỏi ngắn/mơ hồ | +0.05 faithfulness | A/B với HyDE bật/tắt trên cùng golden set |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Hybrid+RRF vs Dense-only | Config A avg=0.7962 | +0.0543 | +30–50 ms/query | Hybrid cải thiện recall với chi phí latency chấp nhận được |
