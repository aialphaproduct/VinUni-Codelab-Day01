# Nhật ký làm Lab 01 theo README

Máy: Windows 11, Python 3.13.4, chạy trong thư mục repo `VinUni_Codelab_Day01_Template`.
Key: `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (đặt trong `.env`). Lúc đầu chỉ có Gemini; key Anthropic và OpenAI được bổ sung sau, kết quả chạy lại ở Bước 6.

Mỗi bước ghi: làm gì → kết quả thật → vấn đề gặp phải (nếu có). Danh sách vấn đề tổng hợp ở cuối file.

## Bước 1 — Môi trường & API key (README mục 1)

| Việc | Lệnh | Kết quả |
|---|---|---|
| Tạo venv | `python -m venv .venv` | OK |
| Kích hoạt (PowerShell) | `.venv\Scripts\Activate.ps1` | OK (ExecutionPolicy của phiên = `Bypass`) |
| Cài thư viện | `pip install -r requirements.txt` | OK: openai 3.46.0, google-genai 2.34.0, google-generativeai 0.8.6, anthropic 2.5.0, pytest 9.2.0, python-dotenv 1.2.4. `pip check` không có xung đột |
| Đặt key | file `.env` với `GEMINI_API_KEY=...`, code gọi `load_dotenv()` | OK. `.env` đã có trong `.gitignore` |

**Vấn đề gặp ở bước này:**
- **[V1] Link trong README bị hỏng**: các link `requirements.txt`, `.env`, `.env.example` trỏ tới `file:///j:/VinUniCodelab/...` (ổ J: trên máy tác giả), bấm trên GitHub không mở được.
- **[V2] Thiếu file `.env.example`**: README bảo copy từ `.env.example` nhưng repo không có file này.
- **[V3] Cài thêm gói đã ngừng hỗ trợ**: `requirements.txt` có `google-generativeai`; import nó hiện `FutureWarning: All support for the google.generativeai package has ended`. Bài chỉ cần `google-genai`.
- **[V4] Code mẫu không tự đọc `.env`**: README gợi ý dùng `python-dotenv` nhưng `template.py` gốc không gọi `load_dotenv()`, nên tạo `.env` xong vẫn báo thiếu key. Đã thêm `load_dotenv()` ở đầu `template.py`.
- **[V5] Có thể bị chặn chạy `Activate.ps1`** trên PowerShell mặc định của Windows (ExecutionPolicy `Restricted`), báo lỗi "running scripts is disabled". Phiên chạy thử được `Bypass` nên không gặp; nếu gặp, có thể dùng `.venv\Scripts\activate.bat` trong CMD hoặc gọi thẳng `.venv\Scripts\python`.

## Bước 2 — Task 1–3: gọi thật từng API (README mục 3)

Prompt dùng chung (lấy từ `template.py`): *"Hãy giải thích sự khác biệt giữa temperature và top_p bằng tiếng Việt ngắn gọn trong 2 câu."*

| Hàm | Lần chạy đầu | Sau khi sửa |
|---|---|---|
| `call_openai` (Task 1) | `OpenAIError: Missing credentials ... set the OPENAI_API_KEY` | Có key `sk-proj`: gpt-4o **3,36s** · in 31 / out 76; gpt-4o-mini **1,67s** · in 31 / out 89 (xem Bước 6) |
| `call_gemini` (Task 2) | 2,16s · in 23 / out **11** / thinking **241** · trả về câu cụt *"Temperature điều chỉnh độ ngẫu nhiên tổng thể của câu"* | 1,80s · in 23 / out **109** / thinking **0** · trả lời đủ 2 câu |
| `call_anthropic` (Task 3) | `TypeError: Messages.create() got an unexpected keyword argument 'temperature'` | Qua được lỗi tham số. Có key: `404 not_found_error: model: claude-3-5-haiku` → đổi sang `claude-haiku-5-5`: **1,82s · in 58 / out 180**, trả lời đủ 2 câu |

**Vấn đề gặp ở bước này:**
- **[V6] Gemini 2.5 Flash trả lời bị cắt với cấu hình mặc định của đề.** Thinking mặc định bật, token thinking tính vào `max_tokens=256` (dùng mất 241), câu trả lời chỉ còn 11 token, `finish_reason=MAX_TOKENS`. README và docstring không nhắc đến thinking. **Đã sửa:** `call_gemini` đặt `thinking_budget=0` cho model Flash (Pro không tắt được nên giữ mặc định); `usage` có thêm `thinking_tokens` và `calc_cost` tính cả phần này vì Google tính tiền như output.
- **[V7] `call_anthropic` theo đề không chạy được với SDK Anthropic mới.** `requirements.txt` ghi `anthropic>=0.5.0` nên pip cài 2.5.0; từ bản 2.x, `messages.create()` **không còn tham số `temperature`/`top_p`**. Test không bắt được lỗi vì dùng mock chấp nhận mọi tham số. **Đã sửa:** chỉ gửi `temperature`/`top_p` khi SDK còn nhận (kiểm tra chữ ký hàm), nếu không thì dùng mặc định của model. Cách khác: ghim `anthropic<2` trong `requirements.txt`.
- **[V8] Tên model Anthropic không hợp lệ (đã kiểm chứng).** Gọi thật với `claude-3-5-haiku` trả về `404 not_found_error`. Danh sách model của key (`client.models.list()`) không còn model Claude 3.5 nào; bản Haiku mới nhất là `claude-haiku-5-5`. **Đã sửa:** `ANTHROPIC_MODEL = "claude-haiku-5-5"`.
- **[V21] `temperature`/`top_p` không có tác dụng với Claude khi dùng SDK 2.x** (hệ quả của V7): hàm vẫn nhận 2 tham số này theo đề nhưng không gửi đi được, model dùng mặc định. Đáng ghi chú khi so sánh tham số giữa các hãng.
- **[V22] Cùng một prompt tiếng Việt, Claude đếm 58 token vào, Gemini đếm 23.** Mỗi hãng dùng tokenizer khác nhau, nên không so được số token giữa hai hãng; chi phí phải tính theo token của chính hãng đó.
- **[V9] Lúc đầu thiếu key OpenAI/Anthropic** nên Task 1, 3 chỉ kiểm tra được đến bước xác thực. Đã chạy thật đủ cả 3 hãng sau khi có key (Bước 6).
- **[V23] Dùng nhầm OpenAI Admin key (`sk-admin-...`).** Gọi `call_openai` trả về `401 You have insufficient permissions for this operation. Missing scopes: model.request`. Admin key chỉ dùng cho API quản trị tổ chức (quản lý key, thành viên, xem usage), **không gọi được model**. README mục 1.2 đúng: cần key dự án `sk-proj-...` tạo ở platform.openai.com/api-keys. Key admin **không** được lưu vào `.env`.

## Bước 3 — Task 4 `compare_models` + chạy `template.py` như README

Lệnh: `.venv\Scripts\python starter-code\template.py` (gõ `quit` để thoát chatbot).

Kết quả thật:
```
=== Model Comparison Test ===
Skipping live API comparison test: Missing credentials. ... set the `OPENAI_API_KEY` ...
Set your API keys to run manual tests.

=== Starting Gemini 2.5 Chatbot (type 'quit' to exit) ===

You: Bye!
```
Chương trình thoát sạch (exit code 0). Công thức chi phí của `compare_models` đã đúng từng số với test (gpt-4o `0.00045`, gpt-4o-mini `0.0000135`, gemini-flash `0.00000675`).

**Vấn đề gặp ở bước này:**
- **[V10] `compare_models` là "được ăn cả, ngã về không".** Hàm gọi OpenAI trước, nên chỉ cần thiếu key OpenAI là cả bảng so sánh bị bỏ qua, kể cả phần Gemini đang chạy được. Giữ nguyên vì đề yêu cầu trả đủ 3 model; muốn xem Gemini riêng thì dùng `benchmark.py`.
- **[V11] Bảng giá trong `template.py` khác giá niêm yết.** `gemini-2.5-flash` ghi `0.075 / 0.300` USD/1M token, trong khi theo bảng giá công bố, giá trả phí của Google là khoảng `0.30 / 2.50` (chưa tính gói miễn phí). Số "chi phí" tính ra chỉ nên xem để so sánh tương đối; nên đối chiếu lại trang giá chính thức.
- **[V12] Lỗi font tiếng Việt khi chạy qua Git Bash/pipe.** Lúc gọi qua Git Bash, chữ tiếng Việt in ra thành `Ch�o`. Trong PowerShell thì hiển thị đúng (console UTF-8). Cách xử lý: đặt `PYTHONIOENCODING=utf-8` hoặc chạy bằng PowerShell.

## Bước 4 — Task 5 `streaming_chatbot`: nhập thử nhiều lượt

### Phiên 1 — trí nhớ ngắn, dòng trống, `EXIT` viết hoa (gọi thật)
```
You: Nhớ giúp tôi: mã số của tôi là 4729. Chỉ trả lời đúng 2 chữ: Đã nhớ.
Gemini: Đã nhớ.
You:                                   ← dòng trống: bỏ qua, không gọi API
You: Thủ đô của Pháp là gì? Trả lời 1 từ.
Gemini: Paris
You: Mã số của tôi là gì? Trả lời ngắn.
Gemini: 4729                           ← nhớ đúng
You: Thủ đô của Nhật là gì? Trả lời 1 từ.
Gemini: Tokyo
You: Mã số của tôi là gì? Nếu không biết thì nói Không biết.
Gemini: 4729                           ← vẫn nhớ vì câu trả lời "4729" ở lượt 3 còn trong lịch sử
You: EXIT
Bye!                                   ← nhận cả chữ hoa
```
Kết quả: **đạt**. 5 lượt hỏi chỉ mất ~6s tổng.

### Phiên 2 — quên sau 3 lượt + hết input (EOF)
Lần chạy đầu: lượt 4 và 5 lỗi `429 RESOURCE_EXHAUSTED` (giới hạn **5 request/phút**), chatbot in nguyên khối JSON lỗi dài ~1.000 ký tự và bỏ mất lượt đó.

Sau khi sửa (xem V13–V15), chạy lại cùng input:
```
You: Nhớ giúp tôi: mã số của tôi là 4729. Chỉ trả lời: Đã nhớ.
Gemini: Đã nhớ.
You: 1+1 bằng mấy? Chỉ trả lời số.
Gemini: 2
You: Màu của bầu trời ban ngày? 1 từ.
Gemini: Xanh
You: Con mèo kêu thế nào? 1 từ.
Gemini: Meo
You: Mã số tôi nhờ nhớ lúc đầu là gì? Nếu không biết thì nói đúng 2 chữ: Không biết.
Gemini: Không biết.                    ← lượt 1 đã ra khỏi cửa sổ 3 lượt: quên đúng thiết kế
Bye!                                   ← hết input (EOF) vẫn thoát sạch, không treo
```
Kết quả: **đạt**, 5s.

### Phiên 3 — nhánh lỗi (dữ liệu giả, không tốn quota)
| Tình huống giả lập | Chatbot xử lý |
|---|---|
| 429 theo phút 2 lần rồi thành công | `[giới hạn tốc độ, thử lại sau 5s...] [... 10s...] Xin chào!` |
| Hết quota theo ngày | `[Lỗi] Hết quota theo ngày của gói Free...`, không thử lại vô ích |
| Lỗi khi đã in được nửa câu | Báo lỗi, **không** thử lại để tránh in trùng câu trả lời |

**Vấn đề gặp ở bước này:**
- **[V13] Gói Free chỉ cho 5 request/phút** với `gemini-2.5-flash`. Chat nhanh tay là dính 429 ngay. **Đã sửa:** chatbot tự chờ rồi thử lại (5s → 10s → 20s, đúng ý tưởng Bonus A), chỉ khi chưa in chữ nào.
- **[V14] Thông báo lỗi khó đọc**: in nguyên JSON lỗi của Google. **Đã sửa:** rút gọn còn 1 dòng tiếng Việt.
- **[V15] Cách cắt lịch sử theo README (`history[-6:]`) chưa đúng "3 lượt"**: nếu cắt sau khi đã thêm câu hỏi mới thì thực chất chỉ giữ 2,5 lượt cũ, và lịch sử có thể **bắt đầu bằng tin của model** thay vì của user. **Đã sửa:** chỉ lưu các lượt đã xong, gửi `3 lượt cũ đầy đủ + câu hỏi mới`, lượt lỗi không lưu vào lịch sử.
- **[V16] Thinking làm chatbot chậm**: chữ đầu tiên ra sau ~3,8s khi bật thinking (benchmark), ~0,6s khi tắt. **Đã sửa:** chatbot tắt thinking.
- **[V17] Hai key gửi sau cùng một project dùng chung quota**: đổi key trong cùng project Google Cloud không reset được giới hạn 20 request/ngày. Phải tạo key ở project mới.

## Bước 5 — Bonus A–C + pytest

**Bonus A `retry_with_backoff`** (hàm lỗi 3 lần rồi thành công, `base_delay=0.1`):
- Kết quả `ok` sau 4 lần gọi; khoảng chờ thực tế đo được **0,1s → 0,2s → 0,4s**, đúng công thức `base_delay * 2^attempt`.
- Lỗi vĩnh viễn với `max_retries=2`: gọi đúng 3 lần rồi ném lại lỗi gốc `RuntimeError`.

**Bonus B + C** (dữ liệu giả vì thiếu key OpenAI): `batch_compare` trả đúng 2 kết quả có kèm `prompt`; bảng Markdown cắt câu dài còn 50 ký tự + `...`, thoát ký tự `|` và gộp xuống dòng nên bảng không bị vỡ.

**pytest** (`.venv\Scripts\python -m pytest tests/ -v`): ban đầu **8 passed, 1 failed**; sau khi sửa mock (V18) → **9 passed**.

| Test | Kết quả |
|---|---|
| call_openai / call_gemini / call_anthropic | PASSED |
| compare_models (chi phí) | PASSED |
| retry_with_backoff ×3 | PASSED |
| streaming_chatbot thoát sạch | PASSED |
| batch_compare + format_comparison_table | Ban đầu **FAILED** (`_get_mock() takes 0 positional arguments but 1 was given`) → sau sửa **PASSED** |

**Vấn đề gặp ở bước này:**
- **[V18] Test `test_batch_runs_and_formats_table` không thể pass với code đúng đề.** Hàm giả `_get_mock()` trong test không nhận tham số, nhưng `batch_compare` phải gọi `compare_models(prompt)`. **Đã sửa:** đổi thành `def _get_mock(prompt):` trong `tests/test_template.py`, chỉ đổi đúng 1 dòng.
- **[V19] Bảng làm tròn chi phí quá thô**: 6 số lẻ khiến `0.0000135` thành `$0.000013`, `0.00000675` thành `$0.000007` (lệch đến ~4%). **Đã sửa:** hiện 8 số lẻ.
- **[V20] Đường dẫn nộp bài không thống nhất**: docstring `template.py` bảo copy sang `solution/solution.py`, nhưng test tìm `solution-code/solution.py`; docstring test còn ghi "Run from the 02-lab/ folder" trong khi repo không có thư mục này.

## Bước 6 — Chạy lại khi đã đủ key (OpenAI `sk-proj` + Anthropic)

### Task 1 `call_openai` (gọi thật)
| Model | Độ trễ | Token in/out | Chi phí (theo bảng giá template) |
|---|---|---|---|
| gpt-4o | 3,36s | 31 / 76 | $0.00167500 |
| gpt-4o-mini | 1,67s | 31 / 89 | $0.00005805 |
Cả hai trả lời đủ 2 câu tiếng Việt, đúng nội dung.

### Task 3 `call_anthropic` (gọi thật, `claude-haiku-5-5`)
1,82s · in 58 / out 180 · trả lời đủ 2 câu. Với `max_tokens=40`: 1,16s, cắt đúng ở 40 token.

### Task 4 — chạy `template.py` như README
```
[GPT4O]        Latency: 2.34s | Cost: $0.001575 | Tokens: 31 in / 71 out
[GPT4O_MINI]   Latency: 1.47s | Cost: $0.000050 | Tokens: 31 in / 75 out
[GEMINI_FLASH] Latency: 1.24s | Cost: $0.000020 | Tokens: 23 in / 61 out
=== Starting Gemini 2.5 Chatbot ... ===  →  quit  →  Bye!
```
Chạy trọn vẹn từ đầu đến cuối, không lỗi.

### Bonus B/C — `batch_compare` + bảng (dữ liệu thật, `benchmark.py --only compare`)
| Model | Độ trễ | Token in/out | Chi phí |
|---|---|---|---|
| GPT-4o | 1,58s | 31 / 72 | $0.00159500 |
| GPT-4o-Mini | 2,00s | 31 / 98 | $0.00006345 |
| Gemini-Flash | 1,16s | 23 / 56 | $0.00001853 |
Bảng đầy đủ ở `benchmark_results.md` (mục "Chạy bổ sung (compare)").

**Nhận xét:** cùng một prompt, GPT-4o đắt hơn GPT-4o-mini khoảng **25 lần** và hơn Gemini Flash khoảng **85 lần** (theo bảng giá trong template). Gemini nhanh nhất ở cả hai lần chạy.

**Vấn đề gặp ở bước này:**
- **[V24] Đoạn chạy thử ở cuối `template.py` cũng làm tròn chi phí 6 số lẻ** (`$0.000020`, `$0.000050`), giống V19. **Đã sửa:** 8 số lẻ.
- **[V25] Độ trễ dao động mạnh giữa các lần chạy**: gpt-4o lần lượt 3,36s → 2,34s → 1,58s; gpt-4o-mini có lần chậm hơn cả gpt-4o (2,00s so với 1,58s). Một lần đo không đủ để kết luận model nào nhanh hơn; nên lặp nhiều lần và xem trung bình/p95 như mục 1 của `benchmark.py`.
- **[V26] Cột Prompt trong bảng Bonus C không được cắt ngắn**: prompt dài làm bảng rất rộng. Đề chỉ yêu cầu cắt cột Response nên giữ nguyên.

---

## Tổng hợp vấn đề

| # | Vấn đề | Mức độ | Trạng thái |
|---|---|---|---|
| V1 | Link trong README trỏ tới `file:///j:/...` | Nhẹ | Ghi nhận |
| V2 | Thiếu `.env.example` | Nhẹ | Ghi nhận |
| V3 | `requirements.txt` có `google-generativeai` đã ngừng hỗ trợ | Nhẹ | Ghi nhận |
| V4 | Template không tự đọc `.env` | Vừa | **Đã sửa** |
| V5 | `Activate.ps1` có thể bị ExecutionPolicy chặn | Nhẹ | Ghi nhận, có cách thay |
| V6 | Gemini trả lời bị cắt do thinking chiếm `max_tokens` | **Nặng** | **Đã sửa** |
| V7 | SDK Anthropic 2.x bỏ `temperature`/`top_p` → `call_anthropic` lỗi | **Nặng** | **Đã sửa** |
| V8 | ID model `claude-3-5-haiku` không hợp lệ (404) | **Nặng** | **Đã sửa** → `claude-haiku-5-5` |
| V9 | Lúc đầu thiếu key OpenAI/Anthropic | — | **Đã có đủ key**, chạy thật xong |
| V10 | `compare_models` hỏng cả bảng khi thiếu 1 key | Nhẹ | Ghi nhận (đúng đề) |
| V11 | Bảng giá Gemini trong template khác giá niêm yết | Vừa | Ghi nhận, nên đối chiếu lại |
| V12 | Lỗi font tiếng Việt khi chạy qua Git Bash | Nhẹ | Ghi nhận, có cách thay |
| V13 | Free tier 5 request/phút → chatbot dính 429 | **Nặng** | **Đã sửa** (tự thử lại) |
| V14 | Thông báo lỗi là cả khối JSON | Vừa | **Đã sửa** |
| V15 | Cắt lịch sử `[-6:]` chưa đúng "3 lượt" | Vừa | **Đã sửa** |
| V16 | Thinking làm chatbot chậm ~6 lần | Vừa | **Đã sửa** |
| V17 | Key cùng project dùng chung quota ngày | Nhẹ | Ghi nhận |
| V18 | Test batch có mock sai, không thể pass | Vừa | **Đã sửa** → 9/9 pass |
| V19 | Làm tròn chi phí lệch đến 4% | Nhẹ | **Đã sửa** |
| V20 | Đường dẫn `solution/` vs `solution-code/` | Nhẹ | Ghi nhận |
| V21 | `temperature`/`top_p` không gửi được cho Claude (SDK 2.x) | Nhẹ | Ghi nhận |
| V22 | Tokenizer khác nhau: cùng prompt Claude 58 token, Gemini 23 | Nhẹ | Ghi nhận |
| V23 | Dùng nhầm OpenAI Admin key → 401 thiếu quyền `model.request` | Vừa | Cần key `sk-proj-...` |
| V24 | Đoạn chạy thử cuối template làm tròn chi phí 6 số lẻ | Nhẹ | **Đã sửa** |
| V25 | Độ trễ dao động mạnh giữa các lần chạy | Nhẹ | Ghi nhận, nên đo lặp |
| V26 | Cột Prompt trong bảng không cắt ngắn | Nhẹ | Ghi nhận (đúng đề) |
