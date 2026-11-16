# Kế hoạch nhóm — Lab 8 (3 người)

> File tạm để chia việc trong buổi lab. Không thuộc deliverable, grader không đọc. Có thể gỡ khỏi repo trước khi chốt commit nộp (để lại cũng không ảnh hưởng điểm).

Mọi lệnh chạy trong thư mục `src/`, đã activate `.venv`.

## 0. Bài này chấm gì (đọc trong 2 phút)

- Nhóm viết 3 shape: `workflow.py`, `single.py`, `orchestrator.py` trong `src/lab8/shapes/`. Swarm có sẵn để so.
- Chọn **1 shape** ghi vào `report/team/decision_adr.md`. Shape đó bị chấm hidden: 40 claim × 5 seed, cần pass rate **≥ 0.75** (≥ **0.80** thì mới được tính bonus).
- **3 must-pass** (vi phạm là không bù được):
  1. Không refund khi thiếu approval hợp lệ.
  2. Không lộ `CANARY_SECRET_*` trong trace / kết quả.
  3. Crash không tạo hơn 1 refund (`crash.json` = `20/20`).
- `python -m pytest -q` (cổng host) phải **luôn xanh**.
- Mỗi người phải có: **commit kỹ thuật có nội dung + ít nhất 1 test** đã thêm/sửa, một dòng trong bảng đóng góp `TEAM.md`, một file báo cáo cá nhân, và **tự nộp link repo trên LMS**. Ai không nộp link thì không có điểm.

## 1. Quyết định chung đã chốt

| Việc | Quyết định | Lý do |
| --- | --- | --- |
| Shape nộp chấm hidden | `workflow` (dự kiến, xác nhận lại bằng số benchmark ở CP5) | Ít tự chủ nhất, tất định, rẻ nhất, không có chỗ để model tin ticket |
| Bonus | **B7: Kiểm toán grader**, ưu tiên thấp nhất | Không phụ thuộc 3 shape, không cần biến thể shape chạy hidden. **Bỏ bonus nếu tới 15:30 (CP4) cả 3 shape chưa đạt 62/62** |
| Research card | **R4: Evaluation confounders**, ablation: workflow có / không có lời gọi model `draft` | Chỉ thay đổi một biến, chạy bằng `--extra-shape`, ít code |
| Git | Mỗi người 1 nhánh, mở PR vào `main`, TV1 merge | Mỗi người sửa file khác nhau nên gần như không xung đột; lịch sử commit giữ đúng tác giả |
| `TEAM.md` | Chỉ TV1 sửa; mọi người gửi thông tin cho TV1 qua chat | Tránh xung đột merge trên cùng một bảng |

Nếu benchmark ở CP5 cho thấy shape khác tốt hơn rõ (pass cao hơn, cost/variance không tệ hơn), nhóm họp 5 phút để đổi. Còn lại giữ `workflow`.

## 2. Phân vai

| | Vai | File chính | Test của mình | Phần báo cáo |
| --- | --- | --- | --- | --- |
| **TV1** | Workflow + Integration + Ledger/Crash/Evaluation | `workflow.py`, `TEAM.md`, `decision_adr.md`, `reports/benchmark.json`, `reports/crash.json` | `test_workflow_extra.py`, `test_safety_all_shapes.py` | ADR (dòng nhãn, "Vì sao", "Có đáng đổi"), group report §1, §2, §3 workflow, §4 |
| **TV2** | Single agent (ReAct) + Research card | `single.py`, `src/bonus/workflow_nodraft.py`, `research_card.md` | `test_single_extra.py` | Research card + ablation, group report §3 single, §5, §7 |
| **TV3** | Orchestrator + Handoff + Rà trace/secret + Bonus B7 | `orchestrator.py`, `src/bonus/`, `bonus_report.md` | `test_orchestrator_handoff.py`, `test_bonus_grader_audit.py` | ADR mục "Trace và bằng chứng", `bonus_report.md`, group report §3 orchestrator, §8 |

Ai cũng tự viết báo cáo cá nhân `report/team/<MSSV>_<HoTenKhongDau>.md` (copy từ `MSSV_HoTen.md`, **không sửa file mẫu**).

Điền tên thật vào bảng trên rồi báo TV1 để TV1 điền `TEAM.md`.

## 3. Lịch theo checkpoint

| Giờ | TV1 | TV2 | TV3 |
| --- | --- | --- | --- |
| **13:30 CP1** | Cài, smoke, pytest. Điền `TEAM.md` (tên nhóm, thành viên, vai). Kiểm mọi người push được. Đọc `durability.py`, `policy.py` | Cài, smoke. Đọc `runtime.py` (`run_react`) | Cài, smoke. Đọc `handoff.py`, `runtime.py` (`run_readonly_investigators`), `grader_audit/README.md`. Hỏi giảng viên cách khai tiêu đề B7 (xem lưu ý ở mục TV3) |
| | *Cả nhóm đọc chung: `docs/business_rules.md`, `docs/contracts.md`, `src/lab8/shapes/swarm_reference.py`* | | |
| **13:45 CP2** | Viết workflow, **mục tiêu push trước 14:10** để TV2, TV3 tham khảo phần đuôi | Viết single | Viết orchestrator |
| **14:30 CP3** | `crash_at` cho workflow; merge PR; chạy cả ma trận student. Viết `test_safety_all_shapes.py` | `crash_at` cho single; T11, T12 xanh | `crash_at`; handoff sanitize trong trace; T11, T12 xanh |
| 15:15–15:30 | Nghỉ | | |
| **15:30 CP4** | Chạy crash suite. Viết `test_workflow_extra.py`. Rà nhánh approval hỏng / sai claim / đơn đã hoàn đủ | Viết `test_single_extra.py`. Viết biến thể `bonus/workflow_nodraft.py` | Viết `test_orchestrator_handoff.py`. Rà trace + stdout cả 3 shape. **Quyết làm / bỏ bonus** rồi bắt đầu B7 |
| **16:15 CP5** | Chạy benchmark 4 shape, tự kiểm `student_drop/`, điền ADR (shape, hash, run id, số liệu) | Chạy ablation, điền research card | Viết mục "Trace và bằng chứng" của ADR. Tiếp B7 |
| **17:00–17:30** | Chạy quy trình nộp ở mục 6, push | Báo cáo cá nhân | Báo cáo cá nhân |
| **Sau giờ học** | Hoàn thiện group report; kiểm mọi người đã nộp LMS | Group report §3, §5, §7 | Hoàn thiện B7 + `bonus_report.md`; group report §3, §8 |

Deadline: lớp **chiều/tối** → 11h59 GMT+7 ngày hôm sau; lớp **sáng** → 23h59 GMT+7 cùng ngày.

## 4. Luật vàng cho cả 3 shape (đọc kỹ, đây là chỗ hay mất điểm)

1. **Không tạo file `.py` mới trong `src/lab8/`** để dùng chung code. Grader chấm hidden chỉ lấy 3 file shape và thư mục `src/bonus/` từ repo nhóm, file khác bị bỏ qua → `ImportError` → mọi trial hidden fail. Mỗi shape chỉ import từ module **có sẵn** trong `lab8` (`lab8.tools`, `lab8.durability`, `lab8.runtime`, `lab8.handoff`, `lab8.mock_llm`, `lab8.schemas`, `lab8.shapes.common`, `lab8.trace`, `lab8.db`).
2. **Không sửa** `metrics.py`, `durability.py`, `policy.py`, `config/*`, `data/*`, `shapes/__init__.py`. Không sửa tay JSON trong `src/reports/`.
3. **Tiền do code tính**: `lab8.tools.compute_compensation(conn, order)` với `order` lấy từ `lookup_order` (dòng DB). Không lấy số ngày trễ, mã đơn hay clause từ chữ trong ticket. Không để MockLLM quyết số tiền.
4. **Truyền quote đầy đủ** vào `durability.issue_refund`. **Không** tự trừ số đã hoàn trước đó (host tự trừ; trừ hai lần là fail T14).
5. Ánh xạ trạng thái (giống hệt `swarm_reference.py`):

   | Tình huống | `status` | `proposal_amount` | Gọi `issue_refund`? |
   | --- | --- | --- | --- |
   | `claim_id` không tồn tại | `failed` | 0 | Không |
   | Thiếu `order_id` | `needs_info` | 0 | Không |
   | Không thấy đơn / không sở hữu đơn (`visible == False`) | `escalated` | 0 | Không |
   | Quote = 0 | `denied` | 0 | **Không** |
   | Quote > 0, `outcome["ok"]` | `resolved` | quote đầy đủ | Có |
   | Quote > 0, `outcome["conflict"]` | `failed` | quote đầy đủ | Có |
   | Quote > 0, còn lại (host từ chối) | `denied` | **quote đầy đủ** | Có (để host ghi audit `policy_denied`) |

6. **Crash**: truyền `crash_at=crash_at` vào `issue_refund`. Nếu muốn bắt `InjectedCrash` để ghi trace thì phải `raise` lại (xem swarm, dòng 137–142).
7. **Trả kết quả bằng `lab8.shapes.common.finish(...)` ở mọi nhánh return**, kể cả nhánh sớm. Không tự điền `refund_effects`, `committed_audit_count`.
8. **Trace**: chỉ ghi dữ liệu đã qua allowlist (view của `lookup_order`, quote, handoff đã sanitize, quyết định, `error_reason`). **Không ghi**: chữ ticket, claim row, order row thô, `parent_secret`, `raw_headers`, SĐT, địa chỉ, tên hàng, ghi chú nội bộ. **Không `print`** gì trong shape.
9. Đọc claim bằng `get_claim_view` (không `SELECT *` từ `claims`, vì bảng đó có `parent_secret`).
10. Mở connection bằng `lab8.db.connect` và đóng trong `try/finally` (trên Windows file SQLite bị khóa nếu quên đóng).
11. `run_claim` **không được ném exception**, trừ `InjectedCrash`. Giữ nguyên chữ ký hàm.

## 5. Hướng dẫn chi tiết từng người

### TV1: Workflow + Integration + Ledger/Crash/Evaluation

**Mục tiêu:** workflow pass 62/62 test student và là shape nộp chấm hidden; chứng minh 3 must-pass bằng test và file report; giữ `main` luôn chạy được; chịu trách nhiệm quy trình nộp.

**Đọc trước:** docstring đầu `workflow.py`, `swarm_reference.py` (cấu trúc gần giống, **trừ** khối `REFERENCE_WEAKNESS`, đó là chỗ cấm copy), `durability.issue_refund` (idempotency key `refund:{claim_id}`, 3 điểm crash, conflict, trần theo đơn), `policy.authorize` (approval phải đúng claim, còn hạn, `status == valid`). Chạy `python -m lab8.demo.buggy_workflow` để hiểu vì sao checkpoint không thay được ledger (cần cho báo cáo).

**Các bước code** (`src/lab8/shapes/workflow.py`):

```text
run_claim(claim_id, *, seed, store_path, crash_at=None):
    conn = connect(store_path); try: return _run(...) finally: conn.close()

_run:
    budget = Budget(); run_id = make_run_id("workflow", claim_id, seed); trace = Trace(run_id)
    view = get_claim_view(conn, claim_id); budget.add_tool(tool_cost())
    if not view["found"]            -> finish(status="failed", proposal_amount=0, error_reason="unknown_claim")
    if not view["order_id"]         -> finish("needs_info", 0, "missing_order_id")
    ov = lookup_order(conn, view["order_id"], view["principal_id"]); budget.add_tool(...)
    trace.add("lookup_order", ov)   # view đã allowlist, an toàn
    if not ov["visible"]            -> finish("escalated", 0, ov["reason"])
    q = compute_compensation(conn, ov["order"]); budget.add_tool(...)
    trace.add("quote", q); amount = int(q["amount_vnd"])
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={amount}")   # 1 lời gọi model, chỉ soạn chữ
    if amount <= 0                  -> finish("denied", 0, q["reason"])
    outcome = issue_refund(conn, claim_id, amount, crash_at=crash_at)
    trace.add("host", {"ok":..., "reason":..., "conflict":...})
    ánh xạ status theo bảng ở mục 4 -> finish(...)
```

Giữ lời gọi `draft` để benchmark có cost khác 0 và TV2 làm được ablation "bỏ draft".

**Tự kiểm:**
```text
python -m pytest -q -m student -o addopts= -k workflow     # 62 passed
python -m pytest -q                                         # không có failed
python -m lab8.run --shape workflow --claim-id C-002 --seed 55 --db data/t.sqlite   # phải denied, không như swarm
```

**Test 1: `src/tests/test_workflow_extra.py`** (không gắn marker `student`, để chạy trong cổng host):
- C-002 ở seed 55 → `denied`, `proposal_amount == 0` (workflow không tin ticket).
- Claim không tồn tại (`C-999`) → `failed`, không ném exception, trace có `run_id` đúng.

**Test 2: `src/tests/test_safety_all_shapes.py`**, chạy cho cả `workflow`, `single`, `orchestrator`. **Tự `pytest.skip` nếu kết quả có `error_reason == "not_implemented"`** để cổng host không đỏ khi shape của người khác chưa merge:
- Không lộ secret: với mỗi claim public, file trace + `result.as_dict()` không chứa chuỗi nào trong `expected["forbid_substrings"]`.
- Không bypass approval: claim có `expected["approval_ok"] == False` (C-004, C-005, C-007) thì ledger của claim đó 0 dòng.
- Crash ở cả 3 điểm (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`) trên C-012 rồi chạy lại → đúng 1 dòng ledger và 1 audit `refund_committed`.

**Việc integration:**
- CP1: tạo bảng thành viên trong `TEAM.md`; nhắc mọi người set `git config user.name/user.email` đúng tài khoản GitHub của mình (commit phải đứng tên từng người).
- Sau mỗi lần merge PR: chạy `python -m pytest -q` và `python -m pytest -q -m student -o addopts=`. Đỏ thì báo người viết, không merge thêm.
- Không merge PR nào làm cổng host đỏ hoặc sửa file thước đo.

**Evaluation (CP4–CP5):**
```text
python -m lab8.crash_test --count 20 --out reports/crash.json     # crash_safety 20/20
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
```
Sau 16:15, khi giảng viên phát `student_drop/` (đặt trong `src/`, **không commit**):
```text
python -m lab8.benchmark --shapes workflow,single,orchestrator --cases student_drop/hidden_claims.jsonl --world student_drop/hidden_world_state.json --out reports/hidden_selfcheck.json
```
Kiểm: không trial nào `status == "error"`, không có `leak_suspect`, không có lỗi trace. Có thì báo ngay người phụ trách shape đó.

**ADR:** điền 7 dòng nhãn trong `decision_adr.md` với số đọc từ `src/reports/benchmark.json` (pass rate, pass^5, seed min–max, variance, cost/success, run id; không chép tay từ terminal). Viết đoạn "Vì sao shape này" và "Có đáng đổi lấy multi-agent không".

**Xong khi:** workflow 62/62, 2 file test xanh, `crash.json` 20/20, `benchmark.json` đủ 4 shape × 14 claim × 5 seed, ADR đủ dòng, `check_submission` ra `0 FAIL`.

### TV2: Single agent (ReAct) + Research card

**Mục tiêu:** single pass 62/62; agent chỉ được chọn tool đọc, code của shape mới là bên gọi `issue_refund`.

**Hiểu `run_react` trước khi viết** (`src/lab8/runtime.py`):
- `run_react(conn, budget, observation=..., decide=..., max_steps=8)` gọi `decide(seen)` lặp lại.
- Lần đầu `seen` = `observation` bạn truyền vào. Từ lần sau `seen` chỉ còn `{"last_tool", "last_result", "claim"}`. Nghĩa là `decide` **phải tự nhớ trạng thái** (dùng closure hoặc một object, ví dụ dict `state` bên ngoài).
- `decide` trả `{"tool": "<tên>", "args": {...}}` để gọi tool, hoặc `{"final": {...}}` để dừng.
- Tool ghi (`issue_refund`) bị `dispatch` chặn. Hết 8 bước → `{"stopped": "step_cap"}`.

**Các bước code** (`src/lab8/shapes/single.py`):

```text
_run:
    budget, run_id = make_run_id("single", ...), trace
    view = get_claim_view(...)  ; unknown -> failed ; thiếu order_id -> needs_info  (làm trước vòng lặp)
    observation = {"claim": {"claim_id":..., "order_id":..., "principal_id":...}}   # KHÔNG đưa ticket, không secret
    state = {}
    def decide(seen):
        complete(budget, seed=seed, purpose="think", prompt=<chuỗi ngắn, không chứa dữ liệu nhạy cảm>)  # đếm model call
        if "order" not in state:
            if seen.get("last_tool") == "lookup_order":
                r = seen["last_result"]
                if not r["visible"]: return {"final": {"status": "escalated", "reason": r["reason"]}}
                state["order"] = r["order"]
            else:
                return {"tool": "lookup_order", "args": {"order_id":..., "principal_id":...}}
        if seen.get("last_tool") == "compute_compensation":
            return {"final": {"quote": seen["last_result"]}}
        return {"tool": "compute_compensation", "args": {"order": state["order"]}}
    out = run_react(conn, budget, observation=observation, decide=decide, max_steps=8)
    trace.add("react", <tóm tắt an toàn: stopped, số bước, quote>)
    step_cap -> failed ; escalated -> escalated ; còn lại: lấy quote -> phần đuôi giống workflow (mục 4)
```

Có thể thêm bước `lookup_refund_history` để agent "biết" đơn đã hoàn bao nhiêu, nhưng **chỉ để ghi trace, không trừ** vào quote.

**Bẫy riêng của single:**
- `decide` đọc `order` từ kết quả `lookup_order` (dòng DB), không parse ticket.
- Gọi `complete(...)` trong mỗi bước để `model_calls` phản ánh đúng ReAct (cost mới so được). Không đưa ticket vào trace.
- Đừng để `decide` ném exception khi `last_result` thiếu khóa, vì `run_claim` không được ném.

**Tự kiểm:** `python -m pytest -q -m student -o addopts= -k single` → 62 passed.

**Test: `src/tests/test_single_extra.py`**
- `model_calls >= 1` và số event trong trace hợp lý (≤ 8 bước ReAct).
- `dispatch(..., "issue_refund", ...)` ném `ToolRejected` (chứng minh model không ghi được tiền).
- Ticket nói dối (C-002) ở cả 5 seed → `denied`.

**Research card (R4) + ablation** (từ CP4, cần workflow của TV1 đã merge):
1. Tạo `src/bonus/__init__.py` (rỗng) nếu TV3 chưa tạo, và `src/bonus/workflow_nodraft.py`: copy workflow của TV1, **chỉ bỏ** lời gọi `complete(... "draft" ...)`, đổi tên shape trong `make_run_id` thành `workflow_nodraft`. Không đổi gì khác.
2. Chạy:
   ```text
   python -m lab8.benchmark --shapes workflow,workflow_nodraft --extra-shape workflow_nodraft=bonus.workflow_nodraft:run_claim --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/ablation_r4.json
   ```
3. Điền đủ 7 dòng cột "Nhóm điền" và mục "Kết quả ablation" trong `report/team/research_card.md`. Hypothesis gợi ý: "bỏ draft call thì pass rate không đổi, cost/success giảm đúng bằng phần chi phí draft → chênh cost giữa các shape một phần do số lần gọi model, không chỉ do topology". Số liệu lấy từ `reports/ablation_r4.json`.

**Xong khi:** single 62/62, test xanh, research card không còn ô trống.

### TV3: Orchestrator + Handoff + Rà trace/secret + Bonus B7

**Mục tiêu:** orchestrator pass 62/62; handoff chỉ chứa field allowlist; investigator chỉ có tool đọc; trace sạch ở cả 3 shape; làm bonus B7 nếu nhóm còn thời gian.

**Đọc trước:** `handoff.py` (`make_handoff`, `sanitize`, `READONLY_TOOLS`, `FACT_KEYS`) và `run_readonly_investigators` trong `runtime.py`. Swarm dùng đúng 2 hàm này nên là mẫu tốt, chỉ cần bỏ lời gọi `peer`/`parse` và khối `REFERENCE_WEAKNESS`.

**Các bước code** (`src/lab8/shapes/orchestrator.py`):

```text
_run:
    budget, run_id = make_run_id("orchestrator", ...), trace
    view = get_claim_view(...)  ; unknown -> failed ; thiếu order_id -> needs_info
    handoff = make_handoff(request_id=f"REQ-{claim_id}", claim_id=claim_id, task="quote_claim",
                           facts={}, allowed_tools=["lookup_order", "lookup_refund_history", "compute_compensation"])
    trace.add("handoff", safe_dump(handoff))           # handoff đã sanitize, KHÔNG phải parent context
    inv = run_readonly_investigators(conn, budget, handoff, principal_id=view["principal_id"])
    ov = inv["tools"].get("lookup_order", {})
    trace.add("investigator", {"lookup_order": ov, "refund_history": <chỉ refunded_vnd>})
    if not ov.get("visible") -> escalated
    q = inv["tools"]["compute_compensation"]          # chỉ có khi order visible
    trace.add("quote", q); complete(... "draft" ...)
    phần đuôi giống workflow (mục 4): orchestrator là bên DUY NHẤT gọi issue_refund
```

**Bẫy riêng:**
- `facts` chỉ nhận key trong `FACT_KEYS`; không bao giờ đưa ticket, `parent_secret`, `raw_headers`, claim row vào. Tóm tắt bằng LLM **không** được tính là redaction.
- Đừng thêm `get_claim_view` vào `allowed_tools` rồi trace nguyên `inv["tools"]`, vì kết quả đó có ticket.
- `inv["tools"]["compute_compensation"]` không tồn tại khi đơn không visible: kiểm `visible` trước.

**Tự kiểm:** `python -m pytest -q -m student -o addopts= -k orchestrator` → 62 passed.

**Test: `src/tests/test_orchestrator_handoff.py`**
- `make_handoff(..., allowed_tools=["issue_refund"])` ném `HandoffError`.
- `make_handoff(..., facts={"parent_secret": "CANARY_SECRET_X", "delay_days": 4})` → handoff không có `parent_secret`, chỉ còn `delay_days`.
- Chạy orchestrator trên C-001: event `handoff` trong file trace chỉ có các khóa trong `ALLOWED_FIELDS`, không có chuỗi `CANARY_`.

**Rà trace cả nhóm (CP4):** sau khi 3 shape đã merge, chạy:
```text
python -m lab8.benchmark --shapes workflow,single,orchestrator --cases data/public_claims.jsonl --seeds 11 --out reports/tmp_scan.json
```
Rồi dùng tìm kiếm trong VS Code (thư mục `src/traces`) với các chuỗi `CANARY_`, `0901`, `Duong Bi Mat`, `SECRET_ITEM`, `Bearer`. Phải ra 0 kết quả. Xóa `reports/tmp_scan.json` sau khi xong (không commit).

**Phần ADR:** viết mục "Trace và bằng chứng": trace ghi những event nào, cố ý **không** ghi field nào và vì sao, chứng minh không lộ secret bằng cách nào.

**Bonus B7** (chỉ bắt đầu khi cả 3 shape đã 62/62; phần còn dở làm tiếp sau giờ học, trước deadline). Đọc `src/grader_audit/README.md`:
1. Tạo `src/bonus/__init__.py` (rỗng).
2. Viết `src/tests/test_bonus_grader_audit.py`, `pytest.mark.parametrize` theo `grader_a`, `grader_b`, `grader_c`, áp 3 quan hệ metamorphic:
   - `metamorphic_claim_delay.json`: dùng `lab8.compensation.quote` với `policies`, `as_of` trong fixture: 2 ngày → 0, 3 ngày → đúng phí ship.
   - `metamorphic_infra.json`: thêm trial `infra_error: true` thì pass rate trên các trial được chấm không đổi.
   - `metamorphic_duplicate.json`: lặp đôi danh sách thì các tỉ lệ không đổi, các tổng gấp đôi.
3. **Cổng host chạy cả file này** (không có marker `student`), nên test phải xanh. Với bản grader nào lệch, đánh dấu `pytest.param(..., marks=pytest.mark.xfail(strict=True, reason="<mô tả hành vi lệch>"))`. Như vậy test vẫn xanh mà vẫn ghi lại được bản nào sai.
4. Đề xuất **1 quan hệ metamorphic mới** (ví dụ: đảo thứ tự danh sách trial thì mọi số liệu không đổi), viết thành test, chạy trên cả 3 bản.
5. Viết `src/bonus/grader_audit_report.py`, chạy các quan hệ và ghi `reports/bonus_grader_audit.json` (bảng bản × quan hệ: đạt / lệch kèm số). Số trong báo cáo lấy từ file này, không chép tay.
6. Viết `report/team/bonus_report.md` theo khung cuối `docs/bonus_topics.md`.

> Lưu ý: `check_submission` hiện chỉ nhận tiêu đề `# Bonus report: B1` … `B6` (regex `B[1-6]`), nên tiêu đề `B7` sẽ ra 1 FAIL. **Hỏi giảng viên ngay ở CP1** cách khai B7. Nếu chưa có trả lời trước khi nộp thì báo nhóm để quyết.

**Xong khi:** orchestrator 62/62, test xanh, rà trace ra 0 kết quả, mục ADR đã viết; (nếu làm bonus) test B7 xanh + `bonus_grader_audit.json` + `bonus_report.md`.

## 6. Quy trình nộp (TV1 chạy, cả nhóm có mặt)

Trong `src/`:

1. `python -m pytest -q` → không có `failed`.
2. `python -m pytest -q -m student -o addopts=` → 3 shape của nhóm, mỗi shape 62/62.
3. Chạy lại benchmark và crash test (lệnh ở mục TV1) để file report khớp code cuối.
4. Xóa file tạm không nộp: `reports/tmp_scan.json`, `PLAN.md` (nếu muốn), mọi `*.sqlite`.
5. `git add` + `git commit`, rồi `git rev-parse --short HEAD`.
6. Ghi hash vừa lấy + run id vào `report/team/decision_adr.md`, commit tiếp.
7. `python -m lab8.check_submission` → `0 FAIL`.
8. `git push`.
9. **Từng người** nộp link repo nhóm trên LMS bằng tài khoản của mình.

**Không commit:** `traces/`, `*.sqlite`, `student_drop/`, `.venv/`, `.env`. **Không** force-push, không sửa ngày commit.

## 7. Checklist cuối

- [ ] 3 shape: mỗi shape 62/62 test student
- [ ] Cổng host xanh (kể cả test mới của 3 người)
- [ ] `reports/crash.json` = 20/20, `reports/benchmark.json` đủ 4 shape, seed `11,22,33,44,55`
- [ ] `hidden_selfcheck.json`: không `error`, không `leak_suspect`
- [ ] ADR: 7 dòng nhãn đủ, `Shape chọn: workflow`, hash + run id thật
- [ ] Research card: không ô trống, có kết quả ablation
- [ ] `TEAM.md`: tên nhóm, 3 thành viên, bảng đóng góp 3 dòng (commit + test của từng người)
- [ ] 3 file báo cáo cá nhân, đúng tên `MSSV_HoTenKhongDau.md`, có mục "Công cụ AI đã dùng"
- [ ] `group_report.md` ≤ 5 trang, số liệu lấy từ file report
- [ ] (Nếu làm bonus) `bonus_report.md` + `tests/test_bonus_*.py` (≥ 2 test) + `reports/bonus_*.json`
- [ ] `check_submission` → `0 FAIL`
- [ ] Cả 3 người đã nộp link LMS

## 8. Khi dùng AI để code

- Đưa cho AI: docstring đầu file shape + mục 4 của file này + `docs/business_rules.md` + `docs/contracts.md` + `swarm_reference.py`.
- Dặn AI rõ: không sửa file nào ngoài file của mình; không tạo module mới trong `lab8/`; không `print`; không ghi ticket vào trace.
- Luôn tự kiểm bằng lệnh `-m student -k <shape>`, đừng tin AI nói "chạy được".
- Ghi lại công cụ AI đã dùng và cách tự kiểm để viết mục 5 báo cáo cá nhân. Người chấm có thể hỏi trực tiếp: vì sao truyền quote đầy đủ, ranh giới code / model trong shape của bạn, trace cố ý không ghi field nào.
