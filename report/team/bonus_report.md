# Bonus report: B7

- Topic + nguồn (tên, năm, slide): B7 · Kiểm toán grader. *Rethinking Evaluation of MAS Efficiency*, EMNLP 2026, slide 44, 59.
- CLAIM của nguồn (1 câu): kết luận về hiệu năng của hệ multi-agent có thể đến từ cách đo; thước đo sai thì mọi so sánh kiến trúc sai theo, kể cả khi shape đúng.
- BOUNDARY (model / dataset / setup): nguồn khảo sát benchmark MAS với LLM thật và nhiều task; ở đây chỉ kiểm 3 bản `summarize` do giảng viên cấp, trên 3 fixture nhỏ (12–24 trial, 1 shape, 2 seed) và trên benchmark public của lab (MockLLM, 14 claim × 5 seed).
- HYPOTHESIS trên LogiX: (1) ít nhất một bản grader làm lệch pass rate hoặc cost/success mà không có test host nào kêu; (2) ba quan hệ trong README chưa đủ: tồn tại lỗi thước đo mà chúng không bắt được.
- Biến cố định / biến thay đổi: cố định fixture, `as_of` 2026-11-15, policy, bộ quan hệ, code kiểm (`bonus/grader_audit.py`). Thay đổi duy nhất: bản `summarize` được kiểm (`grader_a`, `grader_b`, `grader_c`, cộng 2 mutant cố ý hỏng để đo sức bắt lỗi của các quan hệ).
- Lệnh tái lập (copy-paste được, chạy trong `src/`):
  - `python -m pytest -q tests/test_bonus_grader_audit.py`
  - `python -m bonus.grader_audit --out reports/bonus_grader_audit.json`
- File report + run id: `src/reports/bonus_grader_audit.json`, run id `B7-grader-audit-5fd46fdca677` (12 ký tự đầu SHA-256 của 3 fixture; chạy lại ra file giống từng byte, có test kiểm).

## Kết quả

Quan hệ dùng để kiểm (R1–R3 từ `grader_audit/README.md`, R4–R5 nhóm thêm, O1 là oracle tuyệt đối):

| Mã | Quan hệ |
| --- | --- |
| R1 | `delay_days` 2 → 3 với `SHIP-LATE-03`: quote đổi từ 0 sang phí ship |
| R2 | Thêm trial `infra_error: true`: mọi metric trên trial được chấm không đổi |
| R3 | Nhân đôi danh sách: các tỉ lệ không đổi, các tổng gấp đôi (trừ `pass_5`) |
| R3p | Nhân đôi danh sách: `pass_5` không đổi |
| R4 (mới) | Đảo ngược / xáo trộn thứ tự trial (seed 20261115): toàn bộ report không đổi |
| R5 (mới) | Cộng Δ = 100 VND vào cost mỗi trial fail: tổng cost tăng đúng Δ × số trial fail |
| O1 | Oracle tính tay trên fixture `a`: seed rate 5/6 và 4/6, phương sai tổng thể 1/144 |

R1 (kiểm trên `lab8.compensation.quote`): **đạt**. 2 ngày → 0 (`no_entitlement`); 3 ngày → 35.000 (`SHIP-LATE-03`).

Bảng summarizer × quan hệ (lấy từ `matrix` trong report):

| Summarizer | R2 | R3 | R3p | R4 | R5 | O1 |
| --- | --- | --- | --- | --- | --- | --- |
| `grader_a` | đạt | **lệch** | lệch¹ | **lệch** | **lệch** | đạt |
| `grader_b` | đạt | đạt | lệch¹ | đạt | đạt | đạt |
| `grader_c` | **lệch** | đạt | lệch¹ | đạt | đạt | đạt |
| `mutant_unsorted_p95` | đạt | đạt | lệch¹ | **lệch** | đạt | đạt |
| `mutant_sample_variance` | đạt | đạt | lệch¹ | đạt | đạt | **lệch** |

¹ Lỗi chung của `lab8.metrics.summarize` mà cả 3 bản kế thừa (xem bên dưới), không phải lỗi riêng của bản nào.

Lỗi gọi tên theo hành vi, số lấy từ report:

1. **`grader_a`: tính tiền trial đầu tiên của mỗi claim hai lần.** Trên fixture `a`, tổng cost 283,5 so với 189,5 của bản chuẩn: dư 94,0, đúng bằng tổng cost trial đầu của 4 claim. Hệ quả:
   - R3: nhân đôi danh sách thì tổng chỉ thành 473,0 thay vì 567,0, và cost/success từ 31,5 xuống 26,28 dù dữ liệu không đổi.
   - R4: chỉ đảo thứ tự, tổng từ 283,5 thành 285,0 (đảo ngược) hoặc 285,5 (xáo trộn).
   - R5: trial fail đứng đầu claim bị tính Δ hai lần, tổng 683,5 thay vì 583,5.
2. **`grader_c`: coi trial chết vì hạ tầng là quyết định sai của shape.** Thêm 4 trial `infra_error`: pass rate 0,75 → 0,5625, `graded_trials` 12 → 16, pass^5 0,667 → 0,5, cost/success 21,06 → 23,72.
3. **Lỗi chung (`lab8.metrics.summarize`): `pass_5` về 0 khi một cặp (claim, seed) xuất hiện hai lần.** Điều kiện `len(claim_rows) == len(seeds)` đếm dòng chứ không đếm seed phân biệt. `pass_5` 0,667 → 0,0 ở cả 3 bản. Benchmark của lab luôn sinh đúng một trial cho mỗi (shape, claim, seed), nên số chính thức chưa bị ảnh hưởng. Lỗi sẽ lộ khi trial bị ghi lặp, ví dụ retry được log hai lần. Nhóm không sửa được file này (thuộc thước đo), nên chỉ báo lại.
4. **`grader_b`** đạt mọi quan hệ trừ lỗi chung ở mục 3. Đây là bản đúng.

Sức bắt lỗi của quan hệ mới (mutation check, tự kiểm bằng test):
- `mutant_unsorted_p95` lấy p95 trên danh sách bước **chưa sắp xếp**. Nó qua cả R2, R3, R3p giống hệt `grader_b`, và **chỉ R4 bắt được** (p95 5,0 → 3,0 khi đảo thứ tự). Lý do: R3 nối thêm bản sao *vào cuối*, nên mọi logic kiểu "lấy phần tử thứ k" hay "lần đầu xuất hiện" vẫn thấy cùng phần tử. Chỉ đổi thứ tự mới lộ ra lỗi phụ thuộc thứ tự.
- R5 bắt được lớp lỗi "chỉ tính cost của trial pass" hoặc "tính trial fail hai lần". R2 và R3 không chạm tới lớp này vì chúng giữ nguyên cost từng trial.

> Đối chiếu trên `reports/benchmark.json` (chạy `python -m bonus.grader_audit --out reports/bonus_grader_audit.json --benchmark reports/benchmark.json`): **điền sau khi nhóm có benchmark 4 shape chính thức.** Số sẽ lấy từ mục `benchmark_crosscheck` của report, không chép tay.

## Kết luận

**Ủng hộ** cả hai hypothesis.
- (1) Hai trên ba bản grader làm lệch số so sánh mà cổng host (`python -m pytest -q` của đề) không có test nào kêu: `grader_a` thổi cost/success, `grader_c` hạ pass rate khi có lỗi hạ tầng. Với ngưỡng hidden 0,75, `grader_c` có thể đánh trượt một shape đúng chỉ vì timeout.
- (2) Ba quan hệ của README chưa đủ: R4 bắt được một lỗi mà chúng bỏ lọt.

Một lỗi thước đo **vẫn có thể lọt qua mọi quan hệ nhóm đã viết**. `mutant_sample_variance` chia N−1 thay vì N: sai số chỉ là một hệ số cố định, không phụ thuộc thứ tự, không đổi khi nhân đôi, không đụng tới infra hay cost. Vì vậy R2–R5 đều đạt, chỉ oracle O1 (đáp án tính tay 1/144) bắt được. Quan hệ metamorphic hữu ích vì không cần đáp án tuyệt đối cho số tiền hay pass rate, nhưng nó chỉ kiểm *tính nhất quán* giữa các lần chạy. Một công thức sai mà sai nhất quán thì vẫn cần ít nhất một oracle nhỏ tính tay.

Điều kiện làm kết luận đảo lại:
- Nếu benchmark không bao giờ có trial `infra_error`, lỗi của `grader_c` không đổi số nào.
- Nếu mỗi claim chỉ có một trial, lỗi của `grader_a` thành một hằng số cộng thêm. Khi đó thứ hạng giữa các shape có cùng số claim có thể không đổi, dù cost/success tuyệt đối vẫn sai.

## Giới hạn

- MockLLM không phải model sản xuất; cost là mô phỏng; latency `unavailable`.
- Fixture nhỏ (1 shape, 2 seed, 4–6 claim), nên số tuyệt đối chỉ minh họa hành vi, không ước lượng mức lệch trên bộ hidden.
- Hai mutant do nhóm tự viết để đo sức bắt lỗi của quan hệ, không phải lỗi quan sát ngoài thực tế.
- Lỗi `pass_5` nằm trong `lab8.metrics` (file thước đo, không được sửa), nên chỉ được ghi nhận, không vá.
- Tiêu đề `B7` chưa được `check_submission` hiện tại nhận (regex `B[1-6]`): nhóm cần hỏi giảng viên cách khai trước khi nộp.
