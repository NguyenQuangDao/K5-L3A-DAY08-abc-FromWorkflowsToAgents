# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: `abc` (`K5-L3A-DAY08-abc-FromWorkflowsToAgents`)
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): `0c16935`

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

- **ReAct có giới hạn:** `single.py` đọc claim bằng `get_claim_view`, chỉ đưa `claim_id`, `order_id`, `principal_id` vào observation, rồi gọi `run_react` tối đa 8 lượt. Hàm `decide` dùng closure để giữ order giữa các lượt; agent lần lượt chọn `lookup_order` và `compute_compensation`. Mỗi lượt được tính vào `Budget` bằng `MockLLM.complete`.
- **Quyết định và ghi tiền:** Agent chỉ được chọn tool đọc. Quote được tính trên order trả về từ database, không lấy số liệu trong ticket. Sau vòng ReAct, chính code của shape xử lý kết quả: quote 0 thì `denied`; quote dương thì gọi `issue_refund` với quote đầy đủ và chuyển tiếp `crash_at`. Host tiếp tục kiểm approval, cap theo đơn và idempotency trước khi ghi.
- **Trace và kiểm tra:** Trace ghi các event `claim_lookup`, `agent_step`, `react_summary`, `quote`, `host_result` (hoặc nhánh quyết định tương ứng), không ghi ticket hay claim/order row thô. Test riêng xác nhận ticket C-002 nói trễ 5 ngày không làm đổi dữ liệu order 2 ngày, kiểm tra giới hạn ReAct/trace, tool ghi bị chặn và claim không tồn tại trả `failed`. Kết quả tự kiểm TV2: 62 test student và 8 test riêng đã qua.
- **Ablation draft:** Với cùng workflow, public corpus, tool, seed và evaluator, bỏ đúng lời gọi soạn `draft` giữ nguyên 70/70 trial đúng và hạ cost/success mô phỏng từ 28.6586 xuống 27.8571 VND. Chi tiết phương pháp và giới hạn nằm trong research card; kết quả không tự nó chứng minh topology nào tốt hơn.

### Shape C — `orchestrator` (TV3)

- **Đọc claim & định tuyến:** Orchestrator mở SQLite qua `lab8.db.connect` (đóng trong `try/finally`) và đọc claim qua `get_claim_view`. Claim không tồn tại → `failed` (`unknown_claim`); thiếu `order_id` → `needs_info`. Không lấy mã đơn từ chữ trong ticket.
- **Handoff có kiểu, qua allowlist:** Dựng `handoff.v1` bằng `make_handoff` với `facts = {}`, vì orchestrator chưa có dữ kiện đã xác minh và lời khai trong ticket không phải dữ kiện. `allowed_tools` chỉ gồm 3 tool đọc: `lookup_order`, `lookup_refund_history`, `compute_compensation`. Cố ý không giao `get_claim_view`, vì kết quả của nó chứa chữ ticket. `sanitize` bỏ mọi khóa ngoài `ALLOWED_FIELDS`, từ chối tool ghi, và từ chối mọi handoff còn chuỗi `CANARY_SECRET_`/`parent_secret`/`raw_headers`.
- **Investigator chỉ đọc:** `run_readonly_investigators` chạy các tool trong handoff qua `dispatch(worker=True)`, nên tool ngoài `READONLY_TOOLS` bị chặn. Phạm vi đơn theo `principal_id`: đơn của người khác chỉ trả `visible: false` → `escalated`.
- **Tiền do code, một bên ghi duy nhất:** Quote lấy từ `compute_compensation` trên dòng `orders` mà investigator đọc được. Quote = 0 → `denied`, không gọi host. Quote > 0 → orchestrator là bên **duy nhất** gọi `issue_refund(conn, claim_id, <quote đầy đủ>, crash_at=crash_at)`. Ánh xạ kết quả giống workflow (`ok → resolved`, `conflict → failed`, còn lại → `denied`), `proposal_amount` luôn là quote đầy đủ.
- **Ranh giới model:** MockLLM được gọi 2 lần: `plan` (ghi chú định tuyến) và `draft` (câu trả lời). Prompt không chứa ticket, và output không được đọc lại để ra quyết định.
- **Lỗi & crash:** `InjectedCrash` → ghi event `crash`, flush trace rồi ném lại (T12). Lỗi bất ngờ khác → `failed` với `internal_error:<TênLớp>`, không ghi thông điệp lỗi vì có thể chứa dữ liệu. Nhờ vậy `run_claim` không bao giờ ném exception ra grader.
- **Trace:** `claim` (2 cờ boolean), `handoff` (đã sanitize, khóa sắp xếp để trace tái lập từng byte), `investigator` (view allowlist + tổng đã hoàn), `quote`, `host`, `crash`, `decision`. Chi tiết field cố ý không ghi: ADR, mục "Trace và bằng chứng".
- **Test (`src/tests/test_orchestrator_handoff.py`):** biên handoff (từ chối mọi tool ghi, bỏ fact ngoài allowlist, từ chối canary giấu trong fact hợp lệ); một bên ghi duy nhất và quote đầy đủ (dùng spy trên `issue_refund`: C-014 nhận 150.000, không phải 120.000); trace sạch trên cả 14 claim; ticket injection có secret; exception có secret trong thông điệp; crash ở cả 3 điểm rồi resume; trace giống hệt khi cùng seed.

## 4. Kết quả

Số liệu trích trực tiếp từ `src/reports/benchmark.json` (14 claim public × 5 seed `11, 22, 33, 44, 55` = 70 trial/shape) và `src/reports/crash.json`:

| Shape | Pass rate | Pass^5 | Seed min–max | Seed variance | Cost/success (VND) | Mean / p95 steps | Ghi chú |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `workflow` | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 28.66 | 3.79 / 4.00 | 70/70 passed |
| `single` | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 29.23 | 6.21 / 7.00 | 70/70 passed |
| `orchestrator` | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 48.06 | 5.36 / 6.00 | 70/70 passed |
| `swarm` | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3.00 | 69/70 passed (sai `C-002` ở seed 55) |

- **Crash safety (`src/reports/crash.json`):** `20/20` kịch bản an toàn (`before_effect` ×5, `after_effect_before_checkpoint` ×7, `after_checkpoint` ×5, `amount_conflict_on_retry`, `retry_without_approval`, `swarm_after_effect_before_checkpoint`).
- **Demo lỗi checkpoint (`python -m lab8.demo.buggy_workflow`):** cho thấy khi không dùng idempotency + transaction nguyên tử giữa `refund_ledger` và `audit_events`, crash trước checkpoint tạo `unsafe refund rows: 2` (trong khi host ledger luôn giữ ở `1`).
- **Cổng an toàn (`src/tests/test_safety_all_shapes.py`):** `workflow`, `single` và `orchestrator` đạt 0 secret leak trên cả 14 claim public, 0 approval bypass trên `C-004, C-005, C-007`, và resume đúng 1 dòng ledger tại cả 3 điểm crash trên `C-012`.
- **Rà trace mở rộng (`src/tests/test_trace_audit_all_shapes.py`):** ở seed 11 và 55, trace và kết quả của `workflow`, `single` và `orchestrator` không chứa giá trị nhạy cảm nào của world public. Danh sách quét gồm SĐT, địa chỉ, ghi chú nội bộ, tên hàng của mọi đơn, mọi `parent_secret`/header và nguyên văn mọi ticket.
- **Lưu ý khi đọc cột steps:** `steps` là số event trong trace (`docs/metrics.md`), nên nó đo cả độ chi tiết của trace chứ không chỉ khối lượng công việc. `single` (6.21) ghi một event `agent_step` cho mỗi lượt ReAct, còn `orchestrator` (5.36) ghi thêm event `handoff` và `investigator`. Vì vậy so steps giữa các shape chỉ có nghĩa khi các shape ghi trace theo cùng một quy ước. Cost/success không bị ảnh hưởng: nó đếm lời gọi tool và model qua `Budget`.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

Lỗi gặp phải (kèm lệnh, output hoặc ảnh chụp) và cách nhóm xử lý.

- **`check_submission` không nhận tiêu đề bonus B7.** `docs/bonus_topics.md` có topic B7, nhưng `SUBMISSION.md` và `lab8/check_submission.py` (regex `Bonus report:\s*B[1-6]`) chỉ nhận B1–B6. Lệnh `python -m lab8.check_submission` báo: `[FAIL] report/team/bonus_report.md: tiêu đề phải là '# Bonus report: B1' .. 'B6'`. Nhóm đã hỏi lab coach và giữ tiêu đề `# Bonus report: B7` cho đúng topic. Nhóm không sửa `check_submission.py` (file của đề) và không đổi sang B6 để lách kiểm tra.
- **`ModuleNotFoundError: No module named 'bonus'`** khi chạy `python -m bonus.grader_audit` ở gốc repo bằng Python hệ thống. Cách xử lý: chạy trong `src/` sau khi activate `.venv`, như mọi lệnh của lab.
- **Môi trường Python trên macOS:** `python` ban đầu không có trong PATH và `python3` trỏ tới 3.9.6, thấp hơn yêu cầu 3.11–3.13. Cài/khởi tạo Python 3.11.18 trong `.venv311` và chạy lệnh lab sau khi activate môi trường.
- **Git hiển thị hơn 1.000 file sau khi tạo `.venv311`:** `.gitignore` chỉ loại `.venv/`, không loại `.venv311/`. Nhóm thêm `src/.venv311/` vào `.git/info/exclude` trên máy cá nhân; môi trường không bị đưa vào thay đổi cần commit.
- **Lọc test bằng `-k single`:** pytest khớp chữ `single` trong tên hàm `test_public_single_run_cases`, nên vẫn chọn test của workflow/orchestrator. Dùng `-k "single and not workflow and not orchestrator and not swarm"` để lọc shape qua node id; lần chạy đó ra 62 passed, 248 deselected.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM tạo kết quả xác định theo seed, nên các lần gọi `think`/`draft` không mô phỏng chất lượng lập luận, độ hữu ích của câu trả lời khách hàng hay độ trễ model thật; latency được ghi `unavailable`. Bộ public có 14 claim, đủ để kiểm tra luật và tạo đối chứng nhưng nhỏ hơn nhiều so với traffic thực tế. Ablation R4 chỉ cho thấy trên setup này, bỏ một lời gọi soạn câu chữ không đổi quyết định nhưng giảm khoảng 0.80 VND mô phỏng mỗi success; nó không chứng minh lợi thế tổng quát giữa workflow và agent topology khác nhau. Kết luận có thể đổi nếu dùng model thật, đo chất lượng phản hồi/latency, thêm claim đại diện hơn hoặc nếu bước soạn lời nhắn ảnh hưởng đến quyết định (điều mà thiết kế hiện tại cố ý ngăn).

## 8. Tài liệu tham khảo

Tài liệu của lab (trong repo):

- `docs/business_rules.md`: luật nghiệp vụ LogiX-VN (nguồn sự thật cho quote, approval, trần theo đơn).
- `docs/contracts.md`: output contract của `run_claim` và Trace contract v1.
- `docs/metrics.md`: định nghĩa pass rate, pass^5, seed variance, cost/success, steps.
- `docs/architecture.md`: ranh giới code / model giữa các shape.
- `docs/bonus_topics.md` và `src/grader_audit/README.md`: đề bonus B7 và các quan hệ metamorphic.
- `src/lab8/shapes/swarm_reference.py`: shape đối chứng, khối `REFERENCE_WEAKNESS`.

Nguồn nghiên cứu được dẫn trong research card và bonus report (theo thư viện tham khảo của bài lý thuyết N8, slide 68–69):

- *Rethinking Evaluation of MAS Efficiency*, EMNLP 2026 (slide 44, 59): dùng cho bonus B7 và câu R4.
- Google Research 2026, *Towards a Science of Scaling Agent Systems*.
- MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?*
- AgentArch, AACL 2026.

*TV2 bổ sung URL và loại bằng chứng cho nguồn dùng trong research card.*
