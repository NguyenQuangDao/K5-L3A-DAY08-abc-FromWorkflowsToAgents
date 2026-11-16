# Báo cáo cá nhân — 2A202603614_NguyenQuangDao

## 1. Thông tin thành viên

- Họ tên: Nguyễn Quang Đạo
- MSSV: 2A202603614
- Email: anhdao2292003cxz@gmail.com
- GitHub: NguyenQuangDao

## 2. Phần việc phụ trách

- **Vai trò:** TV1 — Workflow + Integration + Ledger/Crash/Evaluation.
- **Code shape:** `src/lab8/shapes/workflow.py` (Shape A — deterministic workflow).
- **Test bổ sung:** `src/tests/test_workflow_extra.py` và `src/tests/test_safety_all_shapes.py`.
- **Evaluation & báo cáo:** Chạy `lab8.demo.buggy_workflow`, `lab8.crash_test`, `lab8.benchmark`, `lab8.check_submission`; điền `TEAM.md`, các mục chính của `report/team/decision_adr.md`, và `report/team/group_report.md` (§1, §2, §3 workflow, §4).

## 3. Đóng góp cụ thể

- Cài đặt đầy đủ `run_claim` trong `src/lab8/shapes/workflow.py` theo luồng tất định:
  - Đọc claim qua `get_claim_view` (không dùng `SELECT *` để tránh đọc `parent_secret` / `raw_headers_json`), xử lý nhánh `unknown_claim` (`failed`) và thiếu `order_id` (`needs_info`).
  - Tra cứu đơn qua `lookup_order` (đã lọc theo `principal_id` và allowlist `ORDER_FIELDS`), không thấy hoặc ngoài phạm vi principal trả `escalated`.
  - Tính tiền bồi thường hoàn toàn bằng code qua `compute_compensation(conn, ov["order"])`, bỏ qua các con số đánh lừa trong nội dung `ticket`.
  - Gọi `MockLLM` (`complete(..., purpose="draft", prompt=f"proposal={amount}")`) duy nhất để soạn chữ phản hồi, tách biệt ranh giới model khỏi logic tiền và policy.
  - Khi `amount > 0`, truyền **full quote** (không tự trừ phần đã hoàn trước) vào `durability.issue_refund(conn, claim_id, amount, crash_at=crash_at)` để host tự kiểm approval, trừ phần đã hoàn theo đơn (`T13`, `T14`), và ghi audit `policy_denied` / `refund_committed` / `amount_conflict`.
  - Truyền `crash_at` và re-raise `InjectedCrash` (ghi event `crash` và flush trace trước khi raise).
  - Mọi nhánh return đều đi qua `lab8.shapes.common.finish(...)` và đóng kết nối SQLite trong `try/finally`.
- Viết `src/tests/test_workflow_extra.py` kiểm tra thêm các nhánh: bỏ qua delay giả trong ticket ở seed 55 (`C-002`), claim không tồn tại (`C-999`), approval hết hạn (`C-007`), approval cấp cho claim khác (`approval_claim_mismatch`), đơn đã hoàn đủ (`C-013`), đơn hoàn phần chênh (`C-014`), và xung đột số tiền khi gọi lại (`amount_conflict`).
- Viết `src/tests/test_safety_all_shapes.py` kiểm tra 3 điều kiện must-pass trên cả `workflow`, `single`, `orchestrator` (tự `pytest.skip` nếu shape trả `error_reason == "not_implemented"`): không lộ `forbid_substrings` trong artifact/trace, không bypass approval, và an toàn crash tại cả 3 điểm (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`).

## 4. Bằng chứng

- `python -m pytest -q -m student -o addopts= -k workflow`: **62 passed** (100% ma trận public T01–T14 × 5 seed + T11 + T12).
- `python -m pytest -q` (cổng host, gồm cả `test_workflow_extra.py` và `test_safety_all_shapes.py`): **64 passed, 10 skipped** (10 test của `single` và `orchestrator` skip do chưa merge PR từ TV2/TV3).
- `python -m lab8.run --shape workflow --claim-id C-002 --seed 55 --db data/t.sqlite`: trả `status: "denied"`, `proposal_amount: 0`, `error_reason: "no_entitlement"`.
- `python -m lab8.crash_test --count 20 --out reports/crash.json`: `crash_safety 20/20`.
- `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`:
  - `workflow`: `pass_rate = 1.000` (`70/70`), `pass_5 = 1.000`, `seed_variance = 0.000000`, `cost_per_success_vnd = 28.66` VND, `mean_steps = 3.79` (run id mẫu: `R-workflow-C-001-s11`, `R-workflow-C-002-s55`).
  - `swarm`: `pass_rate = 0.986` (`69/70`), `pass_5 = 0.929`, `seed_variance = 0.000816`, `cost_per_success_vnd = 49.57` VND, `mean_steps = 2.80`.
- Quét `src/traces/R-workflow-*` với `CANARY_`, `0901`, `Duong Bi Mat`, `SECRET_ITEM`, `Bearer`: 0 kết quả khớp.
- Commit chính: `d6bbefc` (`feat(workflow): implement workflow shape, TV1 tests, reports, and docs`).

## 5. Công cụ AI đã dùng

- **Công cụ:** Antigravity (AI coding assistant).
- **Mục đích sử dụng:** Hỗ trợ đọc đặc tả đề bài (`README.md`, `docs/business_rules.md`, `docs/contracts.md`, `PLAN.md`) và hỗ trợ thực hiện cài đặt `workflow.py`, viết test bổ sung (`test_workflow_extra.py`, `test_safety_all_shapes.py`) và tổng hợp số liệu báo cáo theo dữ liệu và yêu cầu do người làm cung cấp.
- **Cách tự kiểm tra kết quả:**
  - Chạy trực tiếp `python -m lab8.smoke`, `python -m pytest -q`, `python -m pytest -q -m student -o addopts= -k workflow`.
  - Chạy `python -m lab8.crash_test --count 20 --out reports/crash.json` và `python -m lab8.benchmark ... --out reports/benchmark.json` để đối chiếu số liệu thực tế từ JSON.
  - Kiểm tra rò rỉ dữ liệu trên các file `src/traces/R-workflow-*.json` và chạy `python -m lab8.check_submission`.

## 6. Tự đánh giá

- Hoàn thành toàn bộ phần code, test và evaluation của TV1 theo đúng `PLAN.md` và luật nghiệp vụ/contract của Lab 8.
- Workflow đạt `62/62` student test, `0` leak, `0` approval bypass, `20/20` crash safety và `pass_rate = 1.000` với chi phí thấp nhất (`28.66` VND/success).
- Sẵn sàng tích hợp PR từ TV2 (`single.py`, `research_card.md`) và TV3 (`orchestrator.py`, rà trace toàn bộ 3 shape) để chạy lại benchmark cuối cùng trước khi chốt commit nộp bài.
