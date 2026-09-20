# Individual contribution report

## Thông tin

- Họ và tên: Hoàng Văn Tài
- Mã học viên: 2A202602400
- Nhóm: HTDQ
- Repository/branch: HoangVanTai-2A202602400

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 10 | Ghép retrieved chunks thành context và gọi LLM để sinh câu trả lời | `src/task10_generation.py` | Done |
| Citation | Trả answer kèm sources và retrieval source | `src/task10_generation.py` | Done |
| Safe refusal | Xử lý trường hợp không có đủ evidence hoặc provider lỗi | `src/task10_generation.py` | Done |
| Evaluation | Chạy RAGAS với 4 metrics và so sánh dense-only với hybrid + RRF | `src/evaluate.py`, `group_project/evaluation/RESULT.md` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Chỉ cho LLM trả lời từ context được retrieve.  
   **Lý do/evidence:** Giảm hallucination và giúp câu trả lời có thể kiểm chứng bằng citation.  
   **Trade-off:** Nếu corpus không có thông tin thì chatbot sẽ từ chối dù LLM có thể biết câu trả lời từ kiến thức chung.

2. **Quyết định:** Đánh giá hai cấu hình dense-only và hybrid + RRF trên cùng golden dataset.  
   **Lý do/evidence:** Giúp so sánh trực tiếp ảnh hưởng của retrieval strategy.  
   **Trade-off:** Evaluation bằng LLM tốn thêm thời gian và API cost.

## Kiểm thử và kết quả

- Generation chạy end-to-end và trả được answer cùng sources.
- Safe refusal hoạt động khi không có context phù hợp.
- Evaluation chạy đủ 4 metrics: Faithfulness, Answer Relevance, Context Recall và Context Precision.
- Config hybrid + RRF đạt Faithfulness khoảng 0.97, Context Recall khoảng 0.95 và Context Precision khoảng 0.88 trong lần chạy evaluation hiện tại.

## Điều còn hạn chế

- Một số câu trả lời vẫn phụ thuộc chất lượng retrieval và độ phủ của corpus.
- Nếu có thêm thời gian, tôi sẽ phân tích từng case có điểm thấp thay vì chỉ xem điểm trung bình.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc tôi đã thực hiện và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Hoàng Văn Tài