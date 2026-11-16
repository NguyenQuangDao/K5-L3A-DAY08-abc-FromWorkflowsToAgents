# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R4 — Evaluation confounders |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Jiamu Zhang et al. (2026), [Rethinking the Evaluation of Efficiency Methods for Multi-Agent Systems](https://aclanthology.org/2026.emnlp-main.798/), EMNLP 2026; controlled diagnostic benchmark. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Trong các phương pháp và benchmark được nghiên cứu, hiệu quả MAS được báo cáo có thể phụ thuộc vào prompt và topology khởi đầu; vì vậy nghiên cứu đề xuất so sánh trong runtime, backbone và agent registry dùng chung, đồng thời kiểm soát thay đổi cấu trúc. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Kết luận nguồn giới hạn ở các phương pháp hiệu quả MAS và setup benchmark mà paper đánh giá. Ablation của nhóm dùng 14 claim public tổng hợp, MockLLM xác định, một workflow và bảng giá mô phỏng; không đại diện cho model hoặc traffic sản xuất. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Bỏ duy nhất lời gọi MockLLM `draft` khỏi workflow sẽ giữ pass rate, pass^5 và seed variance nguyên như cũ; cost/success sẽ giảm khoảng 0.8 VND mô phỏng mỗi trial thành công. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Giữ nguyên MockLLM, tools, 14 claim public, seeds 11/22/33/44/55, dữ liệu world, giá và evaluator. Biến duy nhất: có hoặc không có lời gọi `complete(..., purpose="draft", ...)`; workflow_nodraft đổi tên shape/run_id để benchmark đăng ký biến thể. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Confound dự kiến: bỏ draft vô tình làm đổi quote, trạng thái hoặc trace. Đo pass rate, pass^5, seed variance, cost/success, steps; kết quả đúng hypothesis cần giữ nguyên quyết định và safety, chỉ giảm chi phí mô phỏng. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,workflow_nodraft --extra-shape workflow_nodraft=bonus.workflow_nodraft:run_claim --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/ablation_r4.json`
- Run id / file report: `reports/ablation_r4.json`; cùng claim/seed run-id mẫu: `R-workflow-C-001-s11` và `R-workflow_nodraft-C-001-s11`.
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: 70/70 trial mỗi shape. Cả hai đạt pass rate 1.000, pass^5 1.000, seed min–max 1.000–1.000, variance 0; mean/p95 steps đều 3.786/4.00. Cost/success giảm từ 28.6586 xuống 27.8571 VND mô phỏng, tức giảm 0.8014 mỗi success; mean model calls giảm từ 0.8571 xuống 0. Hypothesis được ủng hộ trên corpus này: quyết định không đổi và chi phí giảm.
- Giới hạn: Chỉ 14 claim × 5 seed trên MockLLM; số VND là giá mô phỏng, không phải hóa đơn API. Thử nghiệm cô lập một lời gọi soạn câu trả lời, không chứng minh topology nào tốt hơn trên model sản xuất. Latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
