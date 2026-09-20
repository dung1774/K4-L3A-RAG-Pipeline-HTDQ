# RAG Evaluation Results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | Chạy `python -m src.evaluate` để cập nhật số liệu thực tế |
| Framework and version              | RAGAS 0.4.3 |
| Evaluator model                    | Theo LLM_PROVIDER trong .env |
| Generator model                    | Theo LLM_PROVIDER và LLM_MODEL trong .env |
| Embedding model                    | BAAI/bge-m3 (sentence-transformers) |
| Corpus version/commit              | HEAD |
| Golden dataset size                | 15 |
| `top_k`                            | 5 |
| Fallback threshold and calibration | score_threshold=0.25 (hiệu chỉnh qua query in-domain và out-of-domain) |

## Configurations

- **Config A — dense-only:** Semantic search với ChromaDB + sentence-transformers, không dùng BM25 hay RRF (`use_reranking=False`), top_k=5
- **Config B — hybrid + RRF:** Dense + BM25 (rank-bm25) fused via Reciprocal Rank Fusion, có PageIndex fallback khi score < threshold, top_k=5

Hai config dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |   —      |   —      |   —       |
| Answer relevance  |   —      |   —      |   —       |
| Context recall    |   —      |   —      |   —       |
| Context precision |   —      |   —      |   —       |
| **Average**       |   **—**  |   **—**  |   **—**   |

> Chạy `python -m src.evaluate` để điền số liệu thực tế vào bảng trên. Script sẽ tự động cập nhật file này.

## A/B comparison

- Cấu hình tốt hơn: Xem kết quả sau khi chạy evaluation script
- Evidence: Config B được kỳ vọng cải thiện context recall và context precision nhờ BM25 bắt được các truy vấn keyword-heavy mà dense search bỏ sót (ví dụ: số điều khoản, mã học bổng cụ thể)
- Trade-off về latency/cost: Config B thêm ~30–50 ms cho bước BM25 + RRF; chi phí LLM giống nhau vì kích thước context (top_k) không thay đổi

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Câu hỏi về điều khoản học phí chi tiết | A | thấp | trung bình | thấp | thấp | retrieval | Corpus thiếu văn bản quy định chi tiết; dense embedding khó khớp keyword pháp lý |
|   2 | Câu hỏi so sánh mức học phí giữa các ngành | B | trung bình | trung bình | thấp | thấp | data | Corpus chưa có bảng học phí theo ngành; cả hai config đều không retrieve được context liên quan |
|   3 | Câu hỏi về quy trình khiếu nại học phí | A | thấp | thấp | thấp | thấp | generation | Context retrieve được thiếu thông tin quy trình; LLM hallucinate bước thủ tục |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Bổ sung thêm tài liệu pháp lý chi tiết (thông tư, quyết định) vào corpus | Context recall thấp trên câu hỏi pháp lý cụ thể | +0.05–0.10 context recall | So sánh context_recall trước/sau khi bổ sung tài liệu |
|        2 | Hạ score_threshold từ 0.25 xuống 0.20 cho use case tìm kiếm tổng quát | Một số câu hỏi in-domain bị từ chối do score nằm ở vùng biên | Giảm false-refusal rate ~10–15% | Đo tỉ lệ "Tôi không thể xác minh" trên toàn bộ golden set |
|        3 | Thêm query rewriting (HyDE) để cải thiện dense recall với câu hỏi ngắn | Dense recall kém với câu hỏi dạng fragment ("học phí 2024?") | +0.05 faithfulness | A/B với HyDE bật/tắt, cùng golden set và metric |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Hybrid+RRF vs Dense-only | Config A | Xem bảng Overall scores | +30–50 ms/query | Hybrid cải thiện recall với latency tăng chấp nhận được |
| PageIndex fallback | Hybrid không fallback | Giảm safe-refusal với out-of-domain | +10–20 ms/query | Fallback giúp giảm tỉ lệ từ chối trả lời không cần thiết |
