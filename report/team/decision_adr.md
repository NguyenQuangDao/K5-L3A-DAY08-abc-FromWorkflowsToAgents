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

(Mục của TV3 — cập nhật đầy đủ sau khi rà trace cả 3 shape. Hiện tại với `workflow`, trace chỉ ghi các event đã qua allowlist: `claim` (chỉ `found`, `claim_id`, `has_order_id`), `lookup_order` (chỉ `ORDER_FIELDS`), `quote`, `decision`, `host`, `crash`; cố ý loại bỏ `ticket`, `parent_secret`, `raw_headers_json`, `phone`, `address`, `item_name`, `internal_note`.)

## Giới hạn

MockLLM không phải model sản xuất. Latency để `unavailable`. Không sửa JSON cho đủ 0.75.
