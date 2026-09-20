# Individual contribution report

Mỗi thành viên copy template này thành:

```text
reports/<student-id>-<short-name>.md
```

Giới hạn khuyến nghị: 1 trang, không chép lại README hoặc mô tả lý thuyết chung. Báo cáo không phải một bài pipeline cá nhân; mục đích là ghi nhận ownership và bằng chứng đóng góp trong sản phẩm nhóm.

---

## Thông tin

- Họ và tên: Nguyễn Minh Hiển
- Mã học viên: 2A202602759
- Nhóm: HTD
- Repository/branch:

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 4 - Chunking, embedding, indexing | Hoàn thiện pipeline đọc Markdown, chia recursive chunks với ID ổn định/`chunk_index`, embed theo provider trong `.env` và upsert ChromaDB persistent dùng cosine distance. Code được chuẩn bị trước bằng mock/sample; khi TV1 bàn giao corpus chuẩn, team dùng data riêng để index thật. | `src/task4_chunking_indexing.py` | Done |
| Task 5 - Dense semantic search | Hoàn thiện dense search dùng chung `embed_texts()` của Task 4, query ChromaDB, đổi cosine distance sang similarity và trả `SearchResult` dense đã sort, không vượt `top_k`. Team kiểm thử retrieval thật sau khi index corpus riêng. | `src/task5_semantic_search.py` | Done |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định:** Dùng `RecursiveCharacterTextSplitter` với `CHUNK_SIZE=500`, `CHUNK_OVERLAP=50` và ID dạng `document-id::chunk-index`.\
   **Lý do/evidence:** Contract yêu cầu chunk không rỗng, giữ metadata, có `chunk_index`, ID duy nhất/ổn định và chạy index lại không tạo dữ liệu trùng.\
   **Trade-off:** Chunk theo ký tự có thể chưa trùng hoàn toàn với ranh giới ngữ nghĩa của văn bản dài, nhưng dễ kiểm soát kích thước context và giữ được ID xác định.

2. **Quyết định:** Dùng chung một hàm embedding cho index và query; ChromaDB cấu hình cosine, sau đó đổi distance thành similarity `max(0, 1 - distance)`.\
   **Lý do/evidence:** Module contract yêu cầu Task 4 và Task 5 dùng chung embedding model/dimension; semantic search phải trả score giảm dần theo `SearchResult`. Metadata có `url=None` được loại khỏi payload Chroma và khôi phục khi trả kết quả để không vi phạm schema.\
   **Trade-off:** Chroma không lưu giá trị `None`, vì vậy URL chưa có từ dữ liệu đầu vào vẫn được biểu diễn là `None` ở output thay vì một giá trị có thể query trong metadata.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: Trước khi có corpus, chạy `test_chunk_documents_preserves_identity_and_metadata`, `test_semantic_search_uses_shared_embedding_and_contract`, `test_public_function_signatures_are_stable` và smoke test Chroma upsert/query với embedding giả lập `[1.0, 0.0]`. Khi TV1 hoàn tất corpus chuẩn, team sẽ chạy index data riêng và test retrieval bằng query trong domain lẫn ngoài domain.
- Kết quả trước/sau nếu có: 3/3 contract test Task 4-5 pass; smoke test trả đúng chunk, score `1.0` và metadata `url=None`. Kết quả retrieval end-to-end sẽ được xác nhận trên data riêng của team, không suy diễn từ mock/sample.
- Lỗi đã phát hiện và cách xử lý: ChromaDB không nhận metadata `None`; loại giá trị `None` trước upsert và bổ sung lại trường `url` khi tạo `SearchResult`. Đây là điểm đã xử lý trước khi index corpus thật.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: TV2 không tự đánh giá chất lượng retrieval độc lập; kết quả end-to-end phụ thuộc corpus do TV1 chuẩn hóa và được team kiểm thử trên data riêng sau khi index.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Dựa trên kết quả test data riêng của team để hiệu chỉnh `CHUNK_SIZE`, overlap và threshold bằng query trong domain, ngoài domain cùng golden dataset.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-20
- Tên thành viên: Nguyễn Minh Hiển
