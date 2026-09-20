# Individual Contribution Report

## Thông tin

- **Họ và tên:** Võ Minh Quân
- **Mã học viên:** 2A202602429
- **Nhóm:** K4-L3A (HTDQ)
- **Vai trò:** Thành viên 3 (TV3) — Phụ trách Hybrid Retrieval, Reranking & Fallback
- **Repository/branch:** `K4-L3A-RAG-Pipeline-HTDQ` / `vminhquan`

---

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| **Task 6: Lexical Search (BM25)** | Xây dựng bộ tìm kiếm từ khóa BM25; cài đặt công thức Lucene Positive IDF; cơ chế tự động nạp corpus 532 chunks từ Task 4 và index caching tối ưu tốc độ. | `src/task6_lexical_search.py` | Done |
| **Task 7: Reranking (RRF)** | Cài đặt thuật toán Reciprocal Rank Fusion ($k=60$) gộp kết quả từ Dense và Sparse; khử trùng lặp (deduplication) theo document ID; chuẩn hóa output về schema `hybrid`. | `src/task7_reranking.py` | Done |
| **Task 8: Vectorless Fallback** | Xây dựng cơ chế tìm kiếm dự phòng PageIndex khi dense search không tự tin; cơ chế bắt lỗi an toàn (graceful fallback) tránh làm sập pipeline. | `src/task8_pageindex_vectorless.py` | Done |
| **Task 9: Retrieval Pipeline** | Ghép nối toàn bộ pipeline tìm kiếm; kiểm tra điều kiện fallback bằng Cosine score gốc của Dense; đảm bảo fuse RRF duy nhất 1 lần; hỗ trợ chuyển đổi linh hoạt Hybrid và Dense-only. | `src/task9_retrieval_pipeline.py` | Done |
| **Tích hợp & Kiểm thử (Integration & Tests)** | Phối hợp TV2 (ChromaDB) và TV4 (Generation/UI); hiệu chỉnh tương thích RRF score với ngưỡng safe refusal; viết và pass toàn bộ contract & acceptance tests. | `tests/test_contracts.py`, `app.py` | Done |

---

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Áp dụng công thức Lucene Positive IDF $\ln\left(1 + \frac{N - n + 0.5}{n + 0.5}\right)$ thay cho công thức Okapi BM25 chuẩn $\ln\left(\frac{N - n + 0.5}{n + 0.5}\right)$.  
   **Lý do/evidence:** Khi kiểm thử trên corpus nhỏ (ví dụ unit test với 2 tài liệu và từ khóa xuất hiện ở cả 2), công thức Okapi trả về IDF $\le 0$, khiến điểm BM25 bị triệt tiêu về 0 và rớt test contract. Công thức Lucene toán học chứng minh luôn đảm bảo IDF $> 0$ với mọi kích thước corpus từ 2 docs đến 532 chunks thực tế.  
   **Trade-off:** Giảm nhẹ độ phân hóa của những từ cực hiếm, nhưng đảm bảo tính ổn định tuyệt đối (100% pass) của BM25 trong mọi điều kiện dữ liệu.

2. **Quyết định:** Dùng Cosine Score gốc của Dense Search để so sánh với `score_threshold = 0.3` kích hoạt Fallback, không so sánh trực tiếp với RRF Score.  
   **Lý do/evidence:** Điểm Cosine nằm trong thang $[0, 1]$, trong khi điểm RRF là tổng nghịch đảo thứ hạng $Score_{RRF} = \sum \frac{1}{60 + rank} \le 0.033$. Nếu áp ngưỡng $0.3$ lên điểm RRF, hệ thống sẽ luôn bị hiểu nhầm là "không tìm thấy dữ liệu" và kích hoạt Fallback vô lý cho 100% truy vấn. Việc so sánh bằng best dense score giúp đo lường đúng độ tin cậy ngữ nghĩa trước khi quyết định fallback.  
   **Trade-off:** Logic pipeline phải tách biệt bước kiểm tra điểm tin cậy dense trước khi thực hiện RRF fusion.

---

## Kiểm thử và kết quả

- **Test suite:**
  - Chạy toàn bộ 20 bài test tự động: `.venv/bin/pytest tests/test_contracts.py tests/test_acceptance.py -v`
  - Kết quả: **20/20 PASSED (100% green)** trong 3.85s.
- **Truy vấn kiểm thử thực tế trên dữ liệu thật (532 chunks Du lịch Việt Nam):**
  - *Query nghiệp vụ:* `"Điều kiện cấp thẻ hướng dẫn viên du lịch quốc tế là gì?"` $\rightarrow$ Retrieval trả về chính xác 3 chunks từ `luat_du_lich_2017.md` với `retrieval_method="hybrid"` và score RRF tối ưu.
  - *Query out-of-domain:* `"Thời tiết ở Tokyo hôm nay thế nào?"` $\rightarrow$ Pipeline kích hoạt Safe Refusal chuẩn xác, không bịa đặt thông tin.
- **Lỗi đã phát hiện và xử lý:**
  - *Lỗi 1:* BM25 bị điểm 0 khi chạy test contract do công thức IDF âm $\rightarrow$ Giải quyết bằng lớp kế thừa `BM25WithPositiveIDF`.
  - *Lỗi 2:* Xung đột thang điểm giữa RRF score (~0.03) và ngưỡng `MIN_RELEVANCE_SCORE = 0.2` của Task 10 $\rightarrow$ Phối hợp xử lý để nhận diện `retrieval_method == "hybrid"` đi qua bình thường.

---

## Điều còn hạn chế

- **Hạn chế cụ thể:** Bộ tách từ (tokenizer) của BM25 hiện tại sử dụng phương thức tách khoảng trắng cơ bản (`lower().split()`). Với tiếng Việt, các từ ghép và cụm từ cố định (ví dụ: *"hướng dẫn viên"*, *"du lịch mạo hiểm"*) có thể bị phân tách thành các từ đơn lẻ làm giảm độ đặc trưng của từ khóa.
- **Hướng cải tiến ưu tiên:** Tích hợp thư viện tách từ tiếng Việt chuyên dụng như `underthesea` hoặc `pyvi` vào bước tiền xử lý của BM25 để lập chỉ mục theo từ ghép (n-gram/compound words), giúp tăng độ chuẩn xác của tìm kiếm từ khóa lên mức tối đa.

---

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- **Ngày:** 20/09/2026
- **Tên thành viên:** Võ Minh Quân
