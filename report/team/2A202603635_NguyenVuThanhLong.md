# Báo cáo cá nhân — Nguyễn Vũ Thành Long

## 1. Thông tin thành viên

- Họ tên: Nguyễn Vũ Thành Long
- MSSV: 2A202603635
- Email: 26ai.longnvt2@vinuni.edu.vn
- GitHub: nvl191

## 2. Phần việc phụ trách

TV2 — Single agent (ReAct) và Research card R4. Phần code chính gồm `src/lab8/shapes/single.py`, `src/tests/test_single_extra.py`, biến thể ablation `src/bonus/workflow_nodraft.py`, cùng các mục TV2 trong `report/team/research_card.md` và `report/team/group_report.md`.

## 3. Đóng góp cụ thể

- Hoàn thiện shape `single`: vòng ReAct giới hạn 8 lượt, chỉ điều phối các tool đọc `lookup_order` và `compute_compensation`; phần Python gọi host để ghi refund bằng quote đầy đủ. Chuyển tiếp `crash_at`, dùng `finish()` cho kết quả và không ghi ticket hoặc dữ liệu claim nhạy cảm vào trace.
- Thêm test cho ticket nói sai số ngày ở C-002 trên năm seed, trace và giới hạn lượt, chặn tool ghi refund, cùng claim không tồn tại.
- Tạo `workflow_nodraft` từ workflow của TV1, chỉ bỏ lời gọi soạn `draft`, rồi benchmark ablation R4 trên cùng public corpus và seeds.
- Điền Research card R4 và các mục được giao trong group report. Phần code single đã có commit `930961c` (`single ReAct shape`); ablation và các cập nhật báo cáo nằm trong commit `241f08d`.

## 4. Bằng chứng

- `python -m pytest -q tests/test_single_extra.py`: **8 passed**.
- `python -m pytest -q -m student -o addopts= -k 'single and not workflow and not orchestrator and not swarm'`: **62 passed, 330 deselected**.
- Ablation: `src/reports/ablation_r4.json`, 70 trial cho mỗi shape. `workflow` và `workflow_nodraft` đều đạt pass rate 1.000, pass^5 1.000, variance 0; cost/success lần lượt 28.6586 và 27.8571 VND mô phỏng.
- Run ID mẫu: `R-workflow-C-001-s11` và `R-workflow_nodraft-C-001-s11`.

## 5. Công cụ AI đã dùng

Đã dùng Codex để đọc hướng dẫn, hỗ trợ triển khai `single`, viết test và soạn phân tích ablation. Tự kiểm bằng test riêng của single, ma trận student lọc shape single và benchmark công cụ của lab; số liệu trong research card lấy từ JSON benchmark được sinh ra.

## 6. Tự đánh giá

Single giữ được ranh giới giữa agent và host: agent chỉ chọn tool đọc; code tính quote từ order có cấu trúc; host kiểm approval, idempotency và cap theo đơn trước khi ghi. Ablation cho thấy trên bộ public nhỏ và MockLLM, bỏ lượt draft không đổi kết quả chấm nhưng giảm chi phí mô phỏng. Kết quả không đo chất lượng câu trả lời hay latency của model sản xuất, nên không đủ để kết luận về topology trên hệ thống thực tế.
