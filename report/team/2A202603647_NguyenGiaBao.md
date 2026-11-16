# Báo cáo cá nhân — 2A202603647_NguyenGiaBao

## 1. Thông tin thành viên

- Họ tên: Nguyễn Gia Bảo
- MSSV: 2A202603647
- Email: 26ai.baong5@vinuni.edu.vn
- GitHub: Billy3005

## 2. Phần việc phụ trách

- **Vai trò:** TV3 — Orchestrator + Handoff + Rà trace/secret + Bonus B7.
- **Code shape:** `src/lab8/shapes/orchestrator.py` (Shape C — orchestrator + investigator chỉ đọc).
- **Test:** `src/tests/test_orchestrator_handoff.py`, `src/tests/test_trace_audit_all_shapes.py`, `src/tests/test_bonus_grader_audit.py`.
- **Bonus B7:** `src/bonus/grader_audit.py`, `src/reports/bonus_grader_audit.json`, `report/team/bonus_report.md`.
- **Báo cáo:** mục "Trace và bằng chứng" trong `report/team/decision_adr.md`; `report/team/group_report.md` §3 orchestrator, dòng orchestrator ở §4, §5 (lỗi B7, lỗi chạy sai thư mục), §8.

## 3. Đóng góp cụ thể

- **Orchestrator:**
  - Handoff `handoff.v1` dựng bằng `make_handoff` với `facts = {}` và đúng 3 tool đọc (`lookup_order`, `lookup_refund_history`, `compute_compensation`). Cố ý không giao `get_claim_view` cho investigator, vì kết quả của nó chứa chữ ticket.
  - Orchestrator là bên duy nhất gọi `issue_refund`, truyền **quote đầy đủ**.
  - `InjectedCrash` được flush trace rồi ném lại. Lỗi bất ngờ khác trả `failed` với `internal_error:<TênLớp>`, không ghi thông điệp lỗi.
  - Khóa handoff được sắp xếp để trace tái lập từng byte.
- **Quyết định kỹ thuật:**
  - Không đưa lời khai trong ticket vào `facts`, vì đó không phải dữ kiện đã xác minh.
  - Trace chỉ ghi payload đã qua allowlist. Ghi số đã commit (`committed_vnd`) thay vì `effect` thô.
- **Rà trace cả nhóm:** `test_trace_audit_all_shapes.py` quét trace + `RunResult` của workflow, single, orchestrator (seed 11 và 55) với mọi giá trị nhạy cảm trong world public, rộng hơn `forbid_substrings` của nhãn.
- **Bonus B7:**
  - Kiểm 3 bản grader bằng 3 quan hệ của README, cộng 2 quan hệ mới: R4 đảo thứ tự, R5 cost của trial fail.
  - Kết quả: `grader_a` tính cost trial đầu mỗi claim hai lần, `grader_c` coi trial hạ tầng là fail, và cả 3 bản kế thừa lỗi `pass_5` của `lab8.metrics.summarize` khi trial bị lặp.
  - Dùng 2 mutant để đo sức bắt lỗi của các quan hệ, và chạy thêm đối chiếu trên `reports/benchmark.json`.

## 4. Bằng chứng

- Commit: `139fb1a` (orchestrator + test), `d9f04c7` (bonus B7), `ddf4471` (ADR trace), cùng commit tích hợp sau khi merge `main`.
- `python -m pytest -q -m student -o addopts= -k orchestrator`: 62 passed.
- `python -m bonus.grader_audit --out reports/bonus_grader_audit.json`: run id `B7-grader-audit-5fd46fdca677`. Tự chạy lại trong `src/` (đã activate `.venv`), `git status --short` không báo thay đổi, tức là file sinh lại giống file đã commit.
- Số liệu orchestrator trong `src/reports/benchmark.json` (run id dạng `R-orchestrator-<claim>-s<seed>`): pass rate 1.000, pass^5 1.000, seed variance 0.000000, cost/success 48.06 VND.

## 5. Công cụ AI đã dùng

- **Công cụ:** Claude Code (Anthropic).
- **Dùng vào việc:** đọc đề và lập kế hoạch chia việc (`PLAN.md`); viết `orchestrator.py`, các file test, script `bonus/grader_audit.py`; nháp `bonus_report.md`, mục ADR và các phần group report của TV3.
- **Cách tự kiểm tra:**
  - Chạy lại `python -m pytest -q` và ma trận student `-k orchestrator`.
  - Chạy lại script B7 rồi dùng `git status` để xác nhận report khớp file đã commit.
  - Đối chiếu số trong báo cáo với `src/reports/*.json`.
  - Mọi số liệu, run id và commit trong báo cáo đều chép từ output của lệnh hoặc từ `src/reports/*.json` do công cụ sinh ra, không do AI tự đặt.

## 6. Tự đánh giá

Tôi đã hoàn thành các phần việc chính được giao: Orchestrator đạt toàn bộ student test; đã rà soát cả `workflow`, `single` và `orchestrator`, không phát hiện rò rỉ dữ liệu nhạy cảm trong trace và kết quả; Bonus B7 đã kiểm tra grader, đối chiếu benchmark và phân tích giới hạn của bộ test.

Qua bài lab, tôi hiểu rõ hơn một số vấn đề. Với C-014, phải truyền quote đầy đủ 150.000 VND vào `issue_refund`; nếu tự trừ trước, host sẽ trừ hai lần và ledger chỉ còn 90.000 VND. Với handoff, tôi để `facts` rỗng vì ticket chỉ là lời khai chưa xác minh. Metamorphic testing chỉ kiểm tra tính nhất quán: mutant dùng N−1 vẫn qua R2–R5, chỉ oracle O1 phát hiện được.

**Điểm cần cải thiện:** Tôi đã dùng Claude Code để viết phần lớn code và test, chưa thể tự triển khai toàn bộ nếu không có AI hỗ trợ.
