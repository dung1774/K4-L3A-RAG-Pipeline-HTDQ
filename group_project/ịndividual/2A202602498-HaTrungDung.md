# Individual contribution report

## Thông tin

- Họ và tên: Hà Trung Dũng
- Mã học viên: 2A202602498
- Nhóm: HTDQ
- Repository/branch: `tv1-data`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 1 | Thu thập 3 tài liệu pháp lý liên quan đến du lịch và kiểm tra dữ liệu đầu vào | `data/landing/legal/`, `src/task1_collect_legal_docs.py` | Done |
| Task 2 | Chọn 10 bài từ Vietnam Tourism và crawl thành JSON | `data/landing/news/`, `src/task2_crawl_news.py` | Done |
| Task 3 | Chuẩn hóa toàn bộ dữ liệu legal và news sang Markdown | `data/standardized/`, `src/task3_convert_markdown.py` | Done |
| Golden dataset | Chuẩn bị bộ câu hỏi đánh giá bám theo corpus du lịch | `group_project/evaluation/golden_dataset.json` | Done |
| UI / Integration | Dựng giao diện Streamlit và hỗ trợ ghép các module để demo end-to-end | `app.py`, branch `demo-integration` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Chuẩn hóa toàn bộ dữ liệu về Markdown trước khi chunk.  
   **Lý do/evidence:** Legal ban đầu là DOCX, còn bài web là JSON nên cần đưa về cùng format để Task 4 xử lý thống nhất.  
   **Trade-off:** Phải thêm một bước chuyển đổi nhưng pipeline rõ ràng và dễ kiểm tra hơn.

2. **Quyết định:** Crawl bài du lịch từ một nguồn chính là Vietnam Tourism.  
   **Lý do/evidence:** Nội dung cùng domain và có nguồn rõ ràng, thuận lợi cho citation.  
   **Trade-off:** Corpus chưa bao phủ hết tất cả địa điểm du lịch tại Việt Nam.

## Kiểm thử và kết quả

- Chạy acceptance test cho legal, news và standardized data.
- Kết quả: đủ 3 legal, 10 bài du lịch và toàn bộ dữ liệu được chuẩn hóa thành Markdown.
- Trong quá trình tích hợp, phát hiện ChromaDB binary gây conflict nên loại `chroma_db/` khỏi Git và sinh lại từ pipeline.

## Điều còn hạn chế

- Corpus hiện còn nhỏ và tập trung vào một số địa điểm tiêu biểu.
- Nếu có thêm thời gian, tôi sẽ bổ sung thêm dữ liệu du lịch ở các khu vực chưa có trong corpus.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc tôi đã thực hiện và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Hà Trung Dũng