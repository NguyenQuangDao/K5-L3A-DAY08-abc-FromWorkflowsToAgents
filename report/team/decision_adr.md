# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 79b112a (cập nhật lại sau khi TV2, TV3 merge)
- Run id dẫn chứng: R-workflow-C-001-s11, R-workflow-C-002-s55 (src/reports/benchmark.json)
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000-1.000 / 0.000000
- Cost per success (mô phỏng, VND): 28.66
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0 (test_safety_all_shapes.py, 70/70 workflow trials)

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Trên cùng bộ 14 claim public × 5 seed (`11, 22, 33, 44, 55`, tổng 70 trial mỗi shape, dữ liệu trong `src/reports/benchmark.json`), `workflow` đạt `pass_rate = 1.000`, `pass_5 = 1.000`, `seed_min = 1.000`, `seed_max = 1.000`, `seed_variance = 0.000000` và `cost_per_success_vnd = 28.66` VND (`mean_steps = 3.79`, `p95_steps = 4.0`). Trong khi đó, `swarm` đạt `pass_rate = 0.986` (`69/70`), `pass_5 = 0.929`, `seed_variance = 0.000816`, `cost_per_success_vnd = 49.57` VND (đắt hơn khoảng 73%) và sai ở `C-002` tại seed `55` vì model tin số ngày trễ ghi trong ticket thay vì dòng DB `orders`. Vì quy trình xử lý claim có đường đi cố định và luật tiền/chính sách hoàn toàn tất định, `workflow` là kiến trúc ít tự chủ nhất mà vẫn giải quyết đúng 100% yêu cầu, không cho model cơ hội đọc nhầm hoặc bị prompt injection từ ticket.

## Có đáng đổi lấy multi-agent không

Không đáng đổi trong bài toán hoàn phí LogiX-VN. Ngay cả khi một kiến trúc multi-agent (`orchestrator` hoặc `swarm`) có pass rate cao tương đương hoặc nhỉnh hơn trên các tình huống phức tạp, chi phí mô phỏng trên mỗi lần thành công cao hơn đáng kể (như `swarm` tốn `49.57` VND/success so với `28.66` VND/success của `workflow`) và tồn tại rủi ro dao động theo seed (`seed_variance > 0` khi để model diễn giải ticket). Nhóm giữ `workflow` và chỉ cân nhắc đảo quyết định nếu trên bộ dữ liệu mở rộng xuất hiện nhóm claim đòi hỏi suy luận đa bước hoặc điều phối tool động ngoài phạm vi luồng cố định, khiến `workflow` tụt pass rate xuống dưới ngưỡng `0.75` trong khi một kiến trúc agentic đạt pass rate cao hơn rõ rệt mà không vi phạm 3 điều kiện must-pass.

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

Single: *TV2 bổ sung danh sách event sau khi merge `single.py`.*

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

MockLLM không phải model sản xuất. Latency để `unavailable`. Không sửa JSON cho đủ 0.75.
