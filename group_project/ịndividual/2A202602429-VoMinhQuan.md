# Individual contribution report

## Thông tin

- Họ và tên: Võ Minh Quân
- Mã học viên: 2A202602429
- Nhóm: HTDQ
- Repository/branch: vminhquan

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 6 | Cài đặt lexical search bằng BM25 | `src/task6_lexical_search.py` | Done |
| Task 7 | Cài đặt Reciprocal Rank Fusion để gộp dense và BM25 | `src/task7_reranking.py` | Done |
| Task 8 | Xử lý fallback khi retrieval confidence thấp | `src/task8_pageindex_vectorless.py` | Done / Partial |
| Task 9 | Ghép semantic search, BM25, RRF và fallback thành một retrieval pipeline | `src/task9_retrieval_pipeline.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng RRF để fuse Dense và BM25 thay vì cộng trực tiếp score.  
   **Lý do/evidence:** Cosine similarity và BM25 score nằm trên hai thang điểm khác nhau nên không nên cộng trực tiếp.  
   **Trade-off:** RRF chỉ dùng thứ hạng nên bỏ qua độ lớn tuyệt đối của score.

2. **Quyết định:** Dùng raw dense cosine score để quyết định fallback.  
   **Lý do/evidence:** RRF score thường rất nhỏ và không phù hợp làm confidence threshold.  
   **Trade-off:** Threshold cần hiệu chỉnh theo corpus thực tế.

## Kiểm thử và kết quả

- BM25 trả về kết quả đúng SearchResult contract.
- RRF loại trùng chunk và sắp xếp lại kết quả hybrid.
- Retrieval pipeline đã kết hợp được dense và sparse retrieval để đưa Top-K chunk cho generation.
- Trong quá trình tích hợp phát hiện việc dùng RRF score để kiểm tra relevance gây false refusal và đã chuyển logic threshold về dense score.

## Điều còn hạn chế

- Fallback hiện phụ thuộc dịch vụ bên ngoài nên chưa phải lúc nào cũng sử dụng được.
- Nếu có thêm thời gian, tôi sẽ hiệu chỉnh threshold trên nhiều câu in-domain và out-of-domain hơn.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc tôi đã thực hiện và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Võ Minh Quân