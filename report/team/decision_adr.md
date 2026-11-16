# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 86682f7
- Run id dẫn chứng: R-workflow-C-001-s11, R-workflow-C-002-s55 (src/reports/benchmark.json)
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000-1.000 / 0.000000
- Cost per success (mô phỏng, VND): 28.66
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0 (src/reports/benchmark.json: 70/70 trial workflow pass, mỗi trial được chấm forbid_substrings và ledger; tests/test_safety_all_shapes.py, tests/test_trace_audit_all_shapes.py)

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Cả 4 shape chạy cùng 14 claim public × 5 seed (`11, 22, 33, 44, 55`, 70 trial mỗi shape), cùng MockLLM, bảng giá, tool và evaluator. Số liệu lấy từ `src/reports/benchmark.json`:

| Shape | Pass rate | Pass^5 | Variance | Cost/success (VND) | Model call TB | Tool call TB | Steps TB / p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `workflow` (A) | 1.000 | 1.000 | 0.000000 | 28.66 | 0.86 | 2.79 | 3.79 / 4 |
| `single` (B) | 1.000 | 1.000 | 0.000000 | 29.23 | 2.71 | 2.79 | 6.21 / 7 |
| `orchestrator` (C) | 1.000 | 1.000 | 0.000000 | 48.06 | 1.93 | 4.64 | 5.36 / 6 |
| `swarm` (D) | 0.986 | 0.929 | 0.000816 | 49.57 | 3.00 | 4.66 | 2.80 / 3 |

Ba shape của nhóm **ngang nhau về độ đúng**: pass rate 1.000, pass^5 1.000, variance 0. Swarm trượt đúng 1 trial (`R-swarm-C-002-s55`): ở seed 55 nó tin "trễ 5 ngày" trong ticket thay vì `delay_days = 2` của DB. Workflow xử lý đúng chính trial đó (`R-workflow-C-002-s55`, `denied`).

Khi độ đúng ngang nhau, nhóm chọn shape **ít tự chủ nhất**, tức `workflow`. So với `single`, workflow rẻ hơn rất ít (28.66 so với 29.23 VND, khoảng 2%), nhưng khác biệt quan trọng là cấu trúc. Workflow gọi model trung bình 0.86 lần, chỉ để soạn chữ, và đường đi cố định trong code. Single gọi model 2.71 lần và để vòng ReAct chọn tool, tức là thêm một bề mặt có thể sai (chọn sai tool, chạm trần 8 bước) mà không đổi được kết quả nào. So với `orchestrator` và `swarm`, workflow rẻ hơn khoảng 40% (28.66 so với 48.06 và 49.57) vì không có tầng investigator và tool call lặp lại. Mọi quyết định có tiền (quote, approval, trần theo đơn, idempotency) đều nằm trong code và host, nên tự chủ thêm không mang lại lợi ích đo được trên bài toán này.

## Có đáng đổi lấy multi-agent không

Không đáng, trên dữ liệu đo được. Multi-agent ở đây **không nhỉnh hơn về pass rate**: `orchestrator` bằng workflow (1.000), `swarm` thấp hơn (0.986). Trong khi đó cost/success cao hơn khoảng 68–73%. Swarm còn có variance khác 0 (0.000816, seed min 0.929), vì để model diễn giải ticket. Kể cả trong giả định multi-agent nhỉnh hơn 1–2 điểm pass rate, nhóm vẫn giữ workflow nếu chênh lệch đó đi kèm variance > 0. Lý do: ngưỡng hidden tính trên 200 trial, và một shape dao động theo seed khó dự đoán được mức pass trên bộ chưa thấy.

Điều kiện làm quyết định đảo lại:
- Bộ claim mở rộng có loại việc mà luồng cố định không biểu diễn được, ví dụ phải tra nhiều nguồn tùy nội dung claim, khiến workflow tụt pass rate rõ rệt, trong khi một shape agentic đạt cao hơn mà vẫn giữ 0 secret leak, 0 approval bypass và crash 20/20.
- Bước đọc dữ liệu trở thành nút thắt về latency và các investigator đọc song song được (xem B1 trong `docs/bonus_topics.md`). Khi đó orchestrator có thể đáng giá dù đắt hơn. Lab này không đo latency, nên điều kiện này chưa kiểm chứng được.
- Dùng model thật thay MockLLM: nếu model đọc được thông tin hữu ích từ ticket mà dữ liệu có cấu trúc không có, thì phải đo lại.

## Trace và bằng chứng

**Nguyên tắc chung cho cả 3 shape.** Trace là ranh giới bảo mật, không phải log debug. Mỗi lần chạy ghi đúng một file `traces/<run_id>.json` (`run_id = R-<shape>-<claim>-s<seed>`), kể cả nhánh trả sớm và nhánh crash. Shape không ghi file nào khác, không `print`. Trace chỉ chứa payload đã qua allowlist trong code; không có chỗ nào dump nguyên một row.

**Event của workflow** (shape chọn, `src/lab8/shapes/workflow.py`), theo thứ tự:

| Event | Nội dung | Nguồn allowlist |
| --- | --- | --- |
| `claim` | `found`, `claim_id`, `has_order_id` (claim không tồn tại: `found: false`, `reason`) | Chỉ cờ và mã claim, không copy view |
| `lookup_order` | View của `lookup_order`: 7 field `ORDER_FIELDS` nếu đơn thấy được; ngược lại chỉ `visible: false`, `reason`, `order_id` | `lab8.tools.ORDER_FIELDS` |
| `quote` | `amount_vnd`, `reason`, `clause_ids`, `parts` | Kết quả `compute_compensation` |
| `host` | `ok`, `reason`, `conflict` | Không ghi `effect` thô |
| `crash` | `at` (chỉ khi có `crash_at`); trace được flush rồi mới ném lại `InjectedCrash` | |
| `decision` | Chỉ ở nhánh dừng sớm: `needs_info`, `escalated`, `denied` khi quote = 0 | |

**Event của orchestrator** (`src/lab8/shapes/orchestrator.py`), theo thứ tự:

| Event | Nội dung | Nguồn allowlist |
| --- | --- | --- |
| `claim` | `found`, `has_order_id` (hai cờ boolean) | Chỉ cờ, không copy view |
| `handoff` | `handoff.v1` đã sanitize, khóa sắp xếp, `facts = {}`, `allowed_tools` = 3 tool đọc | `make_handoff` → `sanitize` (`ALLOWED_FIELDS`) |
| `investigator` | View của `lookup_order` và tổng `refund_history` (`refund_count`, `refunded_vnd`) | `lab8.tools.ORDER_FIELDS`; khóa history chọn tay |
| `quote` | `amount_vnd`, `reason`, `clause_ids`, `parts` | Kết quả `compute_compensation` |
| `host` | `ok`, `reason`, `conflict`, `committed_vnd` | Không ghi `effect` thô |
| `crash` | `at` (chỉ khi có `crash_at`); trace được flush rồi mới ném lại `InjectedCrash` | |
| `decision` | `status`, `proposal_amount`, `error_reason` | |

**Event của single** (`src/lab8/shapes/single.py`), theo thứ tự:

| Event | Nội dung | Nguồn allowlist |
| --- | --- | --- |
| `claim_lookup` | `found`, `claim_id` | Chỉ cờ và mã claim |
| `decision` | Chỉ ở nhánh thiếu `order_id`: `status: needs_info` | |
| `agent_step` | Mỗi lượt ReAct: `step`, `selected_tool`, `final` | Chỉ tên tool được chọn, không ghi tham số hay kết quả tool |
| `react_summary` | `stopped`, `model_calls`, `tool_calls` | Bộ đếm `Budget` |
| `quote` | `amount_vnd`, `reason`, `clause_ids`, `parts` | Kết quả `compute_compensation` |
| `crash` | `at` (chỉ khi có `crash_at`); trace được flush rồi mới ném lại `InjectedCrash` | |
| `host_result` | `ok`, `reason` | Không ghi `effect` thô |

Observation của agent chỉ gồm `claim_id`, `order_id`, `principal_id`. Ticket không vào observation, không vào prompt của MockLLM, và không vào trace.

**Cố ý không ghi, và vì sao:**
- **Chữ ticket.** Đây là dữ liệu người dùng: có thể chứa câu lệnh injection, số ngày trễ bịa, hoặc chính secret. Shape không dùng ticket để quyết định, nên trace không cần nó.
- **Claim row, `parent_secret`, `raw_headers`.** Chứa `CANARY_SECRET_*` và header `Authorization`. Shape đọc claim qua `get_claim_view`, view này không có các cột đó.
- **Order row thô (SĐT, địa chỉ, tên hàng, ghi chú nội bộ).** Chỉ ghi view của `lookup_order` (7 field trong `ORDER_FIELDS`). Đơn của principal khác chỉ trả `visible: false` kèm lý do.
- **Parent context của orchestrator.** Investigator chỉ nhận handoff đã sanitize. Tóm tắt bằng LLM không được dùng thay redaction.
- **Thông điệp exception.** Nhánh lỗi của orchestrator chỉ ghi `internal_error:<TênLớp>`, vì thông điệp có thể chứa dữ liệu.

**Chứng minh không lộ secret.** Có ba lớp bằng chứng:
1. **Chặn trong code:** `sanitize` từ chối mọi handoff còn chứa `CANARY_SECRET_`, `parent_secret`, `raw_headers`, kể cả khi secret nằm trong một fact hợp lệ.
2. **Test máy (chạy trong cổng host `python -m pytest -q`):**
   - `tests/test_trace_audit_all_shapes.py` chạy workflow, single, orchestrator trên cả 14 claim public ở seed 11 và 55, rồi quét trace + `RunResult` với **mọi** giá trị nhạy cảm có trong world public: SĐT, địa chỉ, ghi chú nội bộ, tên hàng của mọi đơn, mọi `parent_secret` và header, nguyên văn mọi ticket. Phạm vi này rộng hơn `forbid_substrings` của nhãn.
   - `tests/test_safety_all_shapes.py` (TV1) kiểm `forbid_substrings`, approval bypass và crash.
   - `tests/test_orchestrator_handoff.py` thêm một claim injection có secret ngay trong ticket, và một exception có secret trong thông điệp.
3. **Scanner của grader:** grader quét `trace_path` và mọi file `<run_id>*` cùng thư mục. Vì shape không ghi gì ra ngoài chỗ đó, phạm vi quét của scanner trùng với toàn bộ dữ liệu shape để lại.

Nếu trace nằm ngoài chỗ scanner quét được thì không chứng minh được gì. Vì vậy contract fail-closed: thiếu trace, trace cũ, hoặc trace sai `run_id` đều bị tính là fail.

## Giới hạn

- **MockLLM không phải model sản xuất.** Nó tất định theo seed, nên variance bằng 0 của ba shape nhóm phần lớn do thiết kế: không có bước nào để model quyết định. Đó không phải bằng chứng về độ ổn định của một model thật.
- **"Agent" trong single và orchestrator là chính sách viết bằng code.** Hàm `decide` của single và danh sách tool của investigator đều cố định. Vì vậy so A/B/C ở đây đo **chi phí cấu trúc** (số lời gọi, số bước), không đo khả năng lập luận của model.
- **Chi phí là mô phỏng** theo `config/pricing.yaml`, không phải hóa đơn API. Latency là `unavailable`, nên không kết luận gì về tốc độ.
- **`steps` đếm số event trong trace** (`docs/metrics.md`), nên phụ thuộc cách mỗi shape ghi trace. Ví dụ single ghi mỗi lượt ReAct một event. Không dùng steps để so khối lượng việc giữa các shape.
- **Bộ public chỉ có 14 claim.** Pass rate 1.000 trên bộ này không bảo đảm đạt ngưỡng hidden (40 claim × 5 seed). Điểm hidden do grader của giảng viên chấm. Nhóm không sửa JSON trong `src/reports/` để đạt ngưỡng.
