# Team

## Thông tin nhóm

- Tên nhóm: abc
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-abc-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: `https://github.com/NguyenQuangDao/K5-L3A-DAY08-abc-FromWorkflowsToAgents`, nhánh `main`, commit chốt `86682f7`

## Thành viên

| STT | Họ tên           | MSSV        | Email                      | GitHub         | Vai trò                                                   |
| --: | ---------------- | ----------- | -------------------------- | -------------- | --------------------------------------------------------- |
|   1 | Nguyễn Quang Đạo | 2A202603614 | 26ai.daonq2@vinuni.edu.vn | NguyenQuangDao | TV1 — Workflow + Integration + Ledger/Crash/Evaluation    |
|   2 | Nguyễn Vũ Thành Long | 2A202603635 | 26ai.longnvt2@vinuni.edu.vn | nvl191     | TV2 — Single agent (ReAct) + Research card                |
|   3 | Nguyễn Gia Bảo   | 2A202603647 | 26ai.baong5@vinuni.edu.vn  | Billy3005      | TV3 — Orchestrator + Handoff + Rà trace/secret + Bonus B7 |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người                          | Vai                                                    | Commit                                                                                                               | Test đã thêm hoặc sửa                                                     |
| ------------------------------ | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Nguyễn Quang Đạo (2A202603614) | TV1 — Workflow + Integration + Ledger/Crash/Evaluation | `79b112a` — Implement `src/lab8/shapes/workflow.py`, chạy crash suite & benchmark, viết ADR và group report phần TV1 | `src/tests/test_workflow_extra.py`, `src/tests/test_safety_all_shapes.py` |
| Nguyễn Vũ Thành Long (2A202603635) | TV2 — Single agent (ReAct) + Research card | `930961c` — Implement `src/lab8/shapes/single.py`; `241f08d` — ablation R4 (`src/bonus/workflow_nodraft.py`, `reports/ablation_r4.json`), research card, group report §3 single, §5, §7 | `src/tests/test_single_extra.py` |
| Nguyễn Gia Bảo (2A202603647) | TV3 — Orchestrator + Handoff + Rà trace/secret + Bonus B7 | `139fb1a` — Implement `src/lab8/shapes/orchestrator.py`; `d9f04c7` — bonus B7 (`src/bonus/grader_audit.py`, `reports/bonus_grader_audit.json`, `bonus_report.md`); mục "Trace và bằng chứng" trong ADR, group report §3 orchestrator, §8 | `src/tests/test_orchestrator_handoff.py`, `src/tests/test_bonus_grader_audit.py`, `src/tests/test_trace_audit_all_shapes.py` |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## MSSV_HoTen

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-
