# Individual contribution report

## Thông tin

- Họ và tên: Nguyễn Minh Hiển
- Mã học viên: 2A202602759
- Nhóm: HTDQ
- Repository/branch: `TV2`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 4 | Đọc dữ liệu Markdown, chia chunk và tạo metadata cho từng chunk | `src/task4_chunking_indexing.py` | Done |
| Embedding | Tạo embedding bằng provider cấu hình trong `.env` | `src/task4_chunking_indexing.py` | Done |
| ChromaDB | Upsert các chunk vào ChromaDB với cosine distance | `src/task4_chunking_indexing.py` | Done |
| Task 5 | Cài đặt semantic search và trả kết quả theo SearchResult contract | `src/task5_semantic_search.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng RecursiveCharacterTextSplitter với chunk size 500 và overlap 50.  
   **Lý do/evidence:** Giữ được ngữ cảnh giữa các đoạn nhưng chunk vẫn đủ nhỏ để retrieval chính xác.  
   **Trade-off:** Số chunk tăng lên và có một phần nội dung bị lặp do overlap.

2. **Quyết định:** Dùng cùng hàm `embed_texts()` cho cả indexing và query.  
   **Lý do/evidence:** Query và document bắt buộc phải nằm trong cùng embedding space.  
   **Trade-off:** Nếu đổi embedding model thì phải index lại ChromaDB.

## Kiểm thử và kết quả

- Chạy Task 4 thành công và index được **532 chunks**.
- Semantic search trả về các chunk theo cosine similarity và đúng thứ tự score giảm dần.
- Contract tests liên quan đến Task 4 và Task 5 chạy đạt.

## Điều còn hạn chế

- Model embedding local khá nặng và lần đầu cần tải nhiều dữ liệu.
- Nếu có thêm thời gian, tôi sẽ benchmark thêm một embedding model nhẹ hơn để so sánh tốc độ và chất lượng retrieval.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc tôi đã thực hiện và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Nguyễn Minh Hiển