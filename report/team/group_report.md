# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: `abc` (`K5-L3A-DAY08-abc-FromWorkflowsToAgents`)
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): (cập nhật sau khi commit và tích hợp đủ 3 thành viên)

## 2. Mục tiêu và cách tiếp cận

Bài toán LogiX-VN yêu cầu xây dựng hệ thống xử lý yêu cầu hoàn phí vận chuyển qua bốn kiến trúc với mức độ tự chủ tăng dần (`workflow`, `single`, `orchestrator`, và `swarm` tham chiếu) dưới cùng chữ ký `run_claim(claim_id, *, seed, store_path, crash_at=None)`. Trọng tâm kỹ thuật là giữ ranh giới nghiêm ngặt giữa code và model:

1. **Tiền và policy thuộc về code:** Giá trị bồi thường lấy từ dòng dữ liệu có cấu trúc (`orders`, `policies`) qua `compute_compensation`; chữ trong `ticket` chỉ là dữ liệu người dùng, không được tin làm căn cứ tính tiền hoặc ghi đè chính sách.
2. **Host là cửa ghi duy nhất (`durability.issue_refund`):** Shape truyền **full quote** vào host; host tự kiểm tra approval gắn đúng `claim_id`, trừ phần đã hoàn trước đó trên cùng `order_id` (`T13`, `T14`), đảm bảo idempotency (`refund:{claim_id}`) và ghi cùng transaction với audit `refund_committed`.
3. **An toàn crash & bảo mật trace:** Chuyển tiếp `crash_at` và không nuốt `InjectedCrash` (như bài học từ `lab8.demo.buggy_workflow`: nếu tách rời checkpoint và ledger sẽ gây trả trùng); trace chỉ ghi dữ liệu đã qua allowlist.

Nhóm 3 người chia việc theo module độc lập (`PLAN.md`): TV1 phụ trách `workflow.py`, integration tests cho 3 điều kiện must-pass, crash test và benchmark/ADR; TV2 phụ trách `single.py` và Research Card R4; TV3 phụ trách `orchestrator.py`, rà trace/secret và Bonus B7.

## 3. Giải pháp

### Shape A — `workflow` (TV1)

- **Đọc dữ liệu:** Mở SQLite qua `lab8.db.connect` và đóng trong `try/finally`. Đọc claim qua `get_claim_view` (không dùng `SELECT *` để không chạm `parent_secret` và `raw_headers_json`). Nếu `found == False` trả `failed` (`unknown_claim`); nếu thiếu `order_id` trả `needs_info`.
- **Tra cứu & tính tiền:** Gọi `lookup_order(conn, order_id, principal_id)` (chỉ trả allowlist `ORDER_FIELDS` và kiểm tra quyền sở hữu principal; không hợp lệ trả `escalated`). Tính bồi thường bằng `compute_compensation(conn, ov["order"])`, bỏ qua mọi con số trễ/điều khoản cũ trong `ticket`.
- **Ranh giới model:** Gọi `MockLLM` (`complete(..., purpose="draft", prompt=f"proposal={amount}")`) duy nhất 1 lần để soạn câu chữ phản hồi; model không chọn tool và không quyết định số tiền.
- **Gọi host & ánh xạ trạng thái:** Nếu `amount <= 0` trả `denied` (không gọi `issue_refund`). Ngược lại gọi `issue_refund(conn, claim_id, amount, crash_at=crash_at)` với **quote đầy đủ**; nếu gặp `InjectedCrash` thì ghi event `crash`, flush trace rồi `raise` lại. Ánh xạ kết quả host: `ok -> resolved`, `conflict -> failed`, còn lại -> `denied` (giữ `proposal_amount = amount` để khớp audit `policy_denied`).
- **Trace:** Chỉ ghi các event `claim` (không chứa `ticket`), `lookup_order` (allowlist), `quote`, `decision`, `host`, `crash`.

### Shape B — `single` (TV2)

<!-- TV2 bổ sung sau khi hoàn thành single.py -->

### Shape C — `orchestrator` (TV3)

<!-- TV3 bổ sung sau khi hoàn thành orchestrator.py -->

## 4. Kết quả

Số liệu trích trực tiếp từ `src/reports/benchmark.json` (14 claim public × 5 seed `11, 22, 33, 44, 55` = 70 trial/shape) và `src/reports/crash.json`:

| Shape | Pass rate | Pass^5 | Seed min–max | Seed variance | Cost/success (VND) | Mean / p95 steps | Ghi chú |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `workflow` | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 28.66 | 3.79 / 4.00 | 70/70 passed |
| `single` | 0.000 | 0.000 | 0.000–0.000 | 0.000000 | — | 1.00 / 1.00 | Chờ TV2 merge `single.py` |
| `orchestrator` | 0.000 | 0.000 | 0.000–0.000 | 0.000000 | — | 1.00 / 1.00 | Chờ TV3 merge `orchestrator.py` |
| `swarm` | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3.00 | 69/70 passed (sai `C-002` ở seed 55) |

- **Crash safety (`src/reports/crash.json`):** `20/20` kịch bản an toàn (`before_effect` ×5, `after_effect_before_checkpoint` ×7, `after_checkpoint` ×5, `amount_conflict_on_retry`, `retry_without_approval`, `swarm_after_effect_before_checkpoint`).
- **Demo lỗi checkpoint (`python -m lab8.demo.buggy_workflow`):** cho thấy khi không dùng idempotency + transaction nguyên tử giữa `refund_ledger` và `audit_events`, crash trước checkpoint tạo `unsafe refund rows: 2` (trong khi host ledger luôn giữ ở `1`).
- **Cổng an toàn (`src/tests/test_safety_all_shapes.py`):** `workflow` đạt 0 secret leak trên cả 14 claim public, 0 approval bypass trên `C-004, C-005, C-007`, và resume đúng 1 dòng ledger tại cả 3 điểm crash trên `C-012`.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

Lỗi gặp phải (kèm lệnh, output hoặc ảnh chụp) và cách nhóm xử lý.

...

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Nêu thêm giới hạn của nhóm và điều kiện làm kết luận thay đổi.

...

## 8. Tài liệu tham khảo

...
