# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn:
- Commit hash:
- Run id dẫn chứng:
- Pass rate / pass^5 / seed min-max / variance:
- Cost per success (mô phỏng, VND):
- Crash safety:
- Secret leak / approval bypass:

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Viết 1 đoạn. So cùng corpus và cùng seed, không so với một lần chạy lẻ.

## Có đáng đổi lấy multi-agent không

Nếu pass nhỉnh hơn mà cost và variance cao hơn, nhóm giữ hay đổi? Điều kiện nào làm quyết định đảo lại?

## Trace và bằng chứng

Trace của nhóm ghi những event nào? Field nào cố ý **không** ghi, và vì sao? Nếu trace nằm ngoài chỗ scanner quét được, đội security chứng minh thế nào là hệ thống không lộ secret?

**Nguyên tắc chung cho cả 3 shape.** Trace là ranh giới bảo mật, không phải log debug. Mỗi lần chạy ghi đúng một file `traces/<run_id>.json` (`run_id = R-<shape>-<claim>-s<seed>`), kể cả nhánh trả sớm và nhánh crash. Shape không ghi file nào khác, không `print`. Trace chỉ chứa payload đã qua allowlist trong code; không có chỗ nào dump nguyên một row.

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

Workflow (shape chọn) và single: *TV1, TV2 bổ sung danh sách event sau khi merge.*

**Cố ý không ghi, và vì sao:**
- **Chữ ticket.** Đây là dữ liệu người dùng: có thể chứa câu lệnh injection, số ngày trễ bịa, hoặc chính secret. Shape không dùng ticket để quyết định, nên trace không cần nó.
- **Claim row, `parent_secret`, `raw_headers`.** Chứa `CANARY_SECRET_*` và header `Authorization`. Shape đọc claim qua `get_claim_view`, view này không có các cột đó.
- **Order row thô (SĐT, địa chỉ, tên hàng, ghi chú nội bộ).** Chỉ ghi view của `lookup_order` (7 field trong `ORDER_FIELDS`). Đơn của principal khác chỉ trả `visible: false` kèm lý do.
- **Parent context của orchestrator.** Investigator chỉ nhận handoff đã sanitize. Tóm tắt bằng LLM không được dùng thay redaction.
- **Thông điệp exception.** Nhánh lỗi chỉ ghi `internal_error:<TênLớp>`, vì thông điệp có thể chứa dữ liệu.

**Chứng minh không lộ secret.** Có ba lớp bằng chứng:
1. **Chặn trong code:** `sanitize` từ chối mọi handoff còn chứa `CANARY_SECRET_`, `parent_secret`, `raw_headers`, kể cả khi secret nằm trong một fact hợp lệ.
2. **Test máy:** `tests/test_orchestrator_handoff.py` chạy orchestrator trên cả 14 claim public và quét trace + kết quả với mọi `forbid_substrings` của nhãn, cộng `CANARY_`, `Bearer`, `parent_secret`, `raw_headers` và nguyên văn ticket. Có thêm một claim injection chứa secret ngay trong ticket, và một exception có secret trong thông điệp.
3. **Scanner của grader:** grader quét `trace_path` và mọi file `<run_id>*` cùng thư mục. Vì shape không ghi gì ra ngoài chỗ đó, phạm vi quét của scanner trùng với toàn bộ dữ liệu shape để lại.

Nếu trace nằm ngoài chỗ scanner quét được thì không chứng minh được gì. Vì vậy contract fail-closed: thiếu trace, trace cũ, hoặc trace sai `run_id` đều bị tính là fail.

## Giới hạn

MockLLM không phải model sản xuất. Latency để `unavailable`. Không sửa JSON cho đủ 0.75.
