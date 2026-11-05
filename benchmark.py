"""
Day 1 — Benchmark thực tế cho các hàm trong starter-code/template.py.

Chạy:  .venv/Scripts/python benchmark.py            (mặc định 5 lần lặp)
       .venv/Scripts/python benchmark.py --runs 3

Cần GEMINI_API_KEY (trong .env hoặc biến môi trường). OPENAI_API_KEY là tuỳ chọn:
có thì chạy thêm phần so sánh 3 model bằng compare_models.
Kết quả in ra màn hình và ghi vào benchmark_results.md.
"""

import argparse
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "starter-code"))
import template as t  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROMPT_VI = "Hãy giải thích sự khác biệt giữa temperature và top_p bằng tiếng Việt ngắn gọn trong 2 câu."
PROMPT_EN = "Briefly explain the difference between temperature and top_p in 2 sentences."
CALLS = {"n": 0}
# Models not in template.PRICING_1M_TOKENS (USD per 1M tokens, Google list price)
EXTRA_PRICING = {"gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40}}


def call(fn):
    """Every API call goes through retry_with_backoff (handles free-tier 429s)."""
    CALLS["n"] += 1
    try:
        return fn()
    except Exception as e:
        if "PerDay" in str(e):  # daily quota: retrying today is pointless
            raise RuntimeError(
                "Hết quota theo ngày của gói Free (20 request/ngày/model) cho model này. "
                "Chạy lại vào ngày mai hoặc dùng --model khác.") from None
    # transient error (per-minute 429, network): retry with exponential backoff
    return t.retry_with_backoff(fn, max_retries=3, base_delay=8.0)


def gem(prompt, **kw):
    resp, latency = call(lambda: t.gemini_generate(prompt, **kw))
    usage = t.gemini_usage(resp)
    finish = resp.candidates[0].finish_reason.name if resp.candidates else "?"
    return {
        "text": resp.text or "",
        "latency": latency,
        "usage": usage,
        "cost": t.calc_cost(t.GEMINI_MODEL, usage),
        "finish": finish,
    }


def pct(values, p):
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def short(text, n=60):
    text = " ".join(text.split())
    return text if len(text) <= n else text[:n] + "…"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |" for r in rows]
    return "\n".join(out)


# ---------------------------------------------------------------------------
def bench_latency(runs):
    lat, results = [], []
    for _ in range(runs):
        r = gem(PROMPT_VI)
        lat.append(r["latency"])
        results.append(r)
    rows = [[
        runs,
        f"{statistics.mean(lat):.2f}s",
        f"{pct(lat, 50):.2f}s",
        f"{pct(lat, 95):.2f}s",
        f"{min(lat):.2f}s / {max(lat):.2f}s",
        f"{statistics.mean(r['usage']['thinking_tokens'] for r in results):.0f}",
        f"${statistics.mean(r['cost'] for r in results):.6f}",
    ]]
    return "## 1. Độ trễ khi lặp lại cùng prompt (call_gemini mặc định)\n\n" + table(
        ["Số lần", "Trung bình", "p50", "p95", "Min / Max", "Thinking TB", "Chi phí TB"], rows)


def bench_thinking():
    rows = []
    for label, budget, max_t in [
        ("Thinking mặc định", None, 256),
        ("Thinking tắt (budget=0)", 0, 256),
        ("Thinking mặc định", None, 1024),
        ("Thinking tắt (budget=0)", 0, 1024),
    ]:
        r = gem(PROMPT_VI, thinking_budget=budget, max_tokens=max_t)
        u = r["usage"]
        rows.append([label, max_t, f"{r['latency']:.2f}s", u["input_tokens"], u["output_tokens"],
                     u["thinking_tokens"], r["finish"], f"${r['cost']:.6f}", short(r["text"], 45)])
    return ("## 2. Bật / tắt thinking và giới hạn max_tokens\n\n"
            "Token thinking nằm trong max_tokens và được tính tiền như output.\n\n"
            + table(["Cấu hình", "max_tokens", "Độ trễ", "In", "Out", "Thinking", "Kết thúc",
                     "Chi phí", "Câu trả lời"], rows))


def bench_temperature():
    prompt = "Đặt 1 tên quán cà phê độc đáo, chỉ trả về đúng tên, không giải thích."
    rows = []
    for temp in (0.0, 0.7, 1.5):
        outs = [gem(prompt, temperature=temp, thinking_budget=0, max_tokens=40)["text"].strip()
                for _ in range(3)]
        rows.append([temp, len(set(outs)), " · ".join(short(o, 30) for o in outs)])
    return ("## 3. Ảnh hưởng của temperature (3 lần / mức, thinking tắt)\n\n"
            + table(["temperature", "Số câu khác nhau / 3", "Các câu trả lời"], rows))


def bench_language():
    rows = []
    for label, p in [("Tiếng Việt", PROMPT_VI), ("Tiếng Anh", PROMPT_EN)]:
        r = gem(p, thinking_budget=0)
        u = r["usage"]
        rows.append([label, len(p), u["input_tokens"], f"{len(p) / u['input_tokens']:.2f}",
                     u["output_tokens"], f"{r['latency']:.2f}s", f"${r['cost']:.6f}"])
    ratio = rows[0][2] / rows[1][2]
    return ("## 4. Tiếng Việt vs tiếng Anh (cùng nội dung, thinking tắt)\n\n"
            + table(["Ngôn ngữ", "Ký tự", "Token in", "Ký tự/token", "Token out", "Độ trễ", "Chi phí"],
                    rows)
            + f"\n\nPrompt tiếng Việt tốn **{ratio:.2f}x** token đầu vào so với tiếng Anh.")


def bench_streaming():
    from google import genai
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    rows = []
    for label, budget in [("Thinking mặc định", None), ("Thinking tắt", 0)]:
        from google.genai import types
        cfg = types.GenerateContentConfig(
            max_output_tokens=512,
            thinking_config=None if budget is None else types.ThinkingConfig(thinking_budget=budget))

        def run():
            start = time.perf_counter()
            first, chunks, text = None, 0, ""
            for ch in client.models.generate_content_stream(
                    model=t.GEMINI_MODEL, contents=PROMPT_VI, config=cfg):
                if ch.text:
                    if first is None:
                        first = time.perf_counter() - start
                    chunks += 1
                    text += ch.text
            return first or 0.0, time.perf_counter() - start, chunks, text

        first, total, chunks, text = call(run)
        rows.append([label, f"{first:.2f}s", f"{total:.2f}s", chunks, len(text)])
    return ("## 5. Streaming: thời gian ra chữ đầu tiên (TTFT) vs tổng thời gian\n\n"
            + table(["Cấu hình", "TTFT", "Tổng", "Số chunk", "Ký tự"], rows))


def bench_compare():
    if not os.getenv("OPENAI_API_KEY"):
        return "## 6. So sánh GPT-4o / GPT-4o-mini / Gemini\n\nBỏ qua: chưa có OPENAI_API_KEY."
    res = call(lambda: t.batch_compare([PROMPT_VI]))
    return "## 6. So sánh GPT-4o / GPT-4o-mini / Gemini\n\n" + t.format_comparison_table(res)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--model", default="",
                    help="model Gemini dùng để đo (mặc định gemini-2.5-flash), vd gemini-2.5-flash-lite")
    ap.add_argument("--only", default="",
                    help="chạy riêng vài phần, cách nhau dấu phẩy: "
                         "latency,thinking,temperature,language,streaming,compare. "
                         "Kết quả được nối thêm vào cuối benchmark_results.md")
    args = ap.parse_args()
    only = {s.strip() for s in args.only.split(",") if s.strip()}
    if args.model:
        # every helper in template.py reads GEMINI_MODEL as its default
        t.GEMINI_MODEL = args.model
        for f in (t.gemini_generate, t.call_gemini):
            defaults = list(f.__defaults__)
            defaults[0] = args.model
            f.__defaults__ = tuple(defaults)
    if t.GEMINI_MODEL not in t.PRICING_1M_TOKENS:
        t.PRICING_1M_TOKENS[t.GEMINI_MODEL] = EXTRA_PRICING.get(t.GEMINI_MODEL, {"input": 0, "output": 0})
    if not os.getenv("GEMINI_API_KEY"):
        sys.exit("Thiếu GEMINI_API_KEY (đặt trong .env hoặc biến môi trường).")

    started = time.perf_counter()
    sections = [f"# Benchmark Day 01 — {t.GEMINI_MODEL}\n\nNgày chạy: {time.strftime('%Y-%m-%d %H:%M')}"]
    for name, fn in [("latency", lambda: bench_latency(args.runs)), ("thinking", bench_thinking),
                     ("temperature", bench_temperature), ("language", bench_language),
                     ("streaming", bench_streaming), ("compare", bench_compare)]:
        if only and name not in only:
            continue
        print(f"→ {name} ...", flush=True)
        try:
            sections.append(fn())
        except Exception as e:  # keep going: one failed section shouldn't kill the report
            sections.append(f"## {name}\n\nLỗi: {e}")
        print(sections[-1] + "\n", flush=True)

    sections.append(f"---\nTổng số lần gọi API: {CALLS['n']} · Thời gian chạy: "
                    f"{time.perf_counter() - started:.0f}s")
    out = ROOT / "benchmark_results.md"
    if only and out.exists():
        sections[0] = (f"# Chạy bổ sung ({', '.join(sorted(only))}) — model {t.GEMINI_MODEL} — "
                       f"{time.strftime('%Y-%m-%d %H:%M')}")
        with out.open("a", encoding="utf-8") as f:
            f.write("\n\n" + "\n\n".join(sections) + "\n")
    else:
        out.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"Đã ghi {out}")


if __name__ == "__main__":
    main()
