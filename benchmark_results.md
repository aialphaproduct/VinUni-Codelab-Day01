# Benchmark Day 01 — gemini-2.5-flash

Ngày chạy: 2026-11-05 22:36

## 1. Độ trễ khi lặp lại cùng prompt (call_gemini mặc định)

| Số lần | Trung bình | p50 | p95 | Min / Max | Thinking TB | Chi phí TB |
|---|---|---|---|---|---|---|
| 5 | 2.18s | 2.15s | 2.33s | 2.09s / 2.36s | 242 | $0.000077 |

## 2. Bật / tắt thinking và giới hạn max_tokens

Token thinking nằm trong max_tokens và được tính tiền như output.

| Cấu hình | max_tokens | Độ trễ | In | Out | Thinking | Kết thúc | Chi phí | Câu trả lời |
|---|---|---|---|---|---|---|---|---|
| Thinking mặc định | 256 | 2.32s | 23 | 11 | 241 | MAX_TOKENS | $0.000077 | ** Temperature điều chỉnh mức độ ngẫu nhiên v… |
| Thinking tắt (budget=0) | 256 | 1.43s | 23 | 101 | 0 | STOP | $0.000032 | **Temperature** kiểm soát tính ngẫu nhiên của… |
| Thinking mặc định | 1024 | 5.68s | 23 | 38 | 982 | MAX_TOKENS | $0.000308 | **Temperature** điều chỉnh độ ngẫu nhiên và s… |
| Thinking tắt (budget=0) | 1024 | 1.23s | 23 | 45 | 0 | STOP | $0.000015 | Temperature kiểm soát sự ngẫu nhiên của câu t… |

## 3. Ảnh hưởng của temperature (3 lần / mức, thinking tắt)

| temperature | Số câu khác nhau / 3 | Các câu trả lời |
|---|---|---|
| 0.0 | 1 | Mộng Mơ · Mộng Mơ · Mộng Mơ |
| 0.7 | 3 | Lặng Quán · Quán Cà Phê Mơ Màng · Quán Cà Phê Mắt Cú Đêm |
| 1.5 | 3 | Góc Nhỏ Của Lắng Yên · Mưa Hạ Cà Phê · Chốn Thanh Bình |

## 4. Tiếng Việt vs tiếng Anh (cùng nội dung, thinking tắt)

| Ngôn ngữ | Ký tự | Token in | Ký tự/token | Token out | Độ trễ | Chi phí |
|---|---|---|---|---|---|---|
| Tiếng Việt | 91 | 23 | 3.96 | 63 | 1.37s | $0.000021 |
| Tiếng Anh | 76 | 17 | 4.47 | 59 | 1.20s | $0.000019 |

Prompt tiếng Việt tốn **1.35x** token đầu vào so với tiếng Anh.

## streaming

Lỗi: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 20, model: gemini-2.5-flash, description: Generate content requests per day limit exceeded on Free Tier. See https://ai.google.dev/gemini-api/docs/rate-limits.\nPlease retry in 16h18m58.087887051s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'description': 'Generate content requests per day limit exceeded on Free Tier. See https://ai.google.dev/gemini-api/docs/rate-limits.', 'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.5-flash'}, 'quotaValue': '20'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '58738s'}]}}

## 6. So sánh GPT-4o / GPT-4o-mini / Gemini

Bỏ qua: chưa có OPENAI_API_KEY.

---
Tổng số lần gọi API: 22 · Thời gian chạy: 297s


# Chạy bổ sung (streaming) — model gemini-2.5-flash-lite — 2026-11-05 22:51

## 5. Streaming: thời gian ra chữ đầu tiên (TTFT) vs tổng thời gian

| Cấu hình | TTFT | Tổng | Số chunk | Ký tự |
|---|---|---|---|---|
| Thinking mặc định | 0.84s | 1.53s | 5 | 635 |
| Thinking tắt | 1.70s | 2.14s | 4 | 362 |

---
Tổng số lần gọi API: 2 · Thời gian chạy: 6s


# Chạy bổ sung (streaming) — model gemini-2.5-flash — 2026-11-05 22:53

## 5. Streaming: thời gian ra chữ đầu tiên (TTFT) vs tổng thời gian

| Cấu hình | TTFT | Tổng | Số chunk | Ký tự |
|---|---|---|---|---|
| Thinking mặc định | 3.79s | 3.80s | 1 | 67 |
| Thinking tắt | 0.61s | 1.54s | 5 | 559 |

---
Tổng số lần gọi API: 2 · Thời gian chạy: 7s


# Chạy bổ sung (compare) — model gemini-2.5-flash — 2026-11-05 23:25

## 6. So sánh GPT-4o / GPT-4o-mini / Gemini

| Prompt | Model | Response (truncated) | Latency | Tokens (In/Out) | Cost (USD) |
|---|---|---|---|---|---|
| Hãy giải thích sự khác biệt giữa temperature và top_p bằng tiếng Việt ngắn gọn trong 2 câu. | GPT-4o | Temperature và top_p đều là các tham số điều chỉnh... | 1.58s | 31/72 | $0.00159500 |
| Hãy giải thích sự khác biệt giữa temperature và top_p bằng tiếng Việt ngắn gọn trong 2 câu. | GPT-4o-Mini | Temperature là tham số điều chỉnh mức độ ngẫu nhiê... | 2.00s | 31/98 | $0.00006345 |
| Hãy giải thích sự khác biệt giữa temperature và top_p bằng tiếng Việt ngắn gọn trong 2 câu. | Gemini-Flash | **Temperature** kiểm soát độ "sáng tạo" của mô hìn... | 1.16s | 23/56 | $0.00001853 |

---
Tổng số lần gọi API: 1 · Thời gian chạy: 7s
