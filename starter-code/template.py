"""
Day 1 — LLM API Foundation
AICB-P1: AI Practical Competency Program, Phase 1

Instructions:
    1. Fill in every section marked with TODO.
    2. Do NOT change function signatures.
    3. Copy this file to solution/solution.py when done.
    4. Run: pytest tests/ -v
"""

import os
import time
from typing import Any, Callable

try:  # load API keys from a local .env file if python-dotenv is installed
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Estimated costs per 1M INPUT & OUTPUT tokens (USD) as of March 2026
# Vietnamese text generally consumes ~1.5x - 2.0x more tokens than English due to Unicode/diacritics.
# ---------------------------------------------------------------------------
PRICING_1M_TOKENS = {
    "gpt-4o": {"input": 5.00, "output": 20.00},
    "gpt-4o-mini": {"input": 0.150, "output": 0.600},
    "gemini-2.5-flash": {"input": 0.075, "output": 0.300},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
}

# Standard Model Identifiers
OPENAI_MODEL = "gpt-4o"
OPENAI_MINI_MODEL = "gpt-4o-mini"
GEMINI_MODEL = "gemini-2.5-flash"
# "claude-3-5-haiku" is not a valid model id (API returns 404 not_found_error)
# and the Claude 3.5 family is no longer served; use the current Haiku.
ANTHROPIC_MODEL = "claude-haiku-5-5"


# ---------------------------------------------------------------------------
# Shared helpers (used by the tasks below and by benchmark.py)
# ---------------------------------------------------------------------------
def timed(fn: Callable[[], Any]) -> tuple[Any, float]:
    """Run fn() and return (result, elapsed_seconds)."""
    start = time.perf_counter()
    result = fn()
    return result, float(time.perf_counter() - start)


def make_usage(input_tokens: int | None, output_tokens: int | None,
               thinking_tokens: int | None = 0) -> dict:
    """Normalise token counts from any provider into one dict shape."""
    return {
        "input_tokens": input_tokens or 0,
        "output_tokens": output_tokens or 0,
        "thinking_tokens": thinking_tokens or 0,
    }


def calc_cost(model: str, usage: dict) -> float:
    """
    USD cost of one call. Thinking tokens (Gemini 2.5) are billed at the
    output rate, so they are added to the output side.
    """
    rate = PRICING_1M_TOKENS[model]
    billed_output = usage["output_tokens"] + usage.get("thinking_tokens", 0)
    return (usage["input_tokens"] * rate["input"]
            + billed_output * rate["output"]) / 1_000_000


def gemini_generate(
    prompt: Any,
    model: str = GEMINI_MODEL,
    temperature: float = 0.7,
    top_p: float = 0.9,
    max_tokens: int = 256,
    thinking_budget: int | None = None,
) -> tuple[Any, float]:
    """
    Low-level Gemini call returning (raw_response, latency).
    thinking_budget: None = model default, 0 = thinking off (2.5 Flash).
    Note: thinking tokens count against max_tokens, so a small max_tokens
    with thinking on can truncate the visible answer.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    config = types.GenerateContentConfig(
        temperature=temperature,
        top_p=top_p,
        max_output_tokens=max_tokens,
        thinking_config=(None if thinking_budget is None
                         else types.ThinkingConfig(thinking_budget=thinking_budget)),
    )
    return timed(lambda: client.models.generate_content(
        model=model, contents=prompt, config=config))


def gemini_usage(response: Any) -> dict:
    meta = response.usage_metadata
    thoughts = getattr(meta, "thoughts_token_count", 0)
    return make_usage(meta.prompt_token_count, meta.candidates_token_count,
                      thoughts if isinstance(thoughts, int) else 0)


# ---------------------------------------------------------------------------
# Task 1 — Call OpenAI (GPT-4o)
# ---------------------------------------------------------------------------
def call_openai(
    prompt: str,
    model: str = OPENAI_MODEL,
    temperature: float = 0.7,
    top_p: float = 0.9,
    max_tokens: int = 256,
) -> tuple[str, float, dict]:
    """
    Call the OpenAI Chat Completions API and return the response text, latency,
    and token usage stats.

    Args:
        prompt:      The user message to send.
        model:       The OpenAI model to use (default: gpt-4o).
        temperature: Sampling temperature (0.0 – 2.0).
        top_p:       Nucleus sampling threshold.
        max_tokens:  Maximum number of tokens to generate.

    Returns:
        A tuple of:
            - response_text (str)
            - latency_seconds (float)
            - usage (dict with keys: 'input_tokens', 'output_tokens')

    Hint:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # response.usage contains input_tokens and output_tokens (prompt_tokens/completion_tokens)
    """
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response, latency = timed(lambda: client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    ))
    text = response.choices[0].message.content or ""
    usage = make_usage(response.usage.prompt_tokens, response.usage.completion_tokens)
    return text, latency, usage


# ---------------------------------------------------------------------------
# Task 2 — Call Google Gemini 2.5 (Standard Practical Model)
# ---------------------------------------------------------------------------
def call_gemini(
    prompt: str,
    model: str = GEMINI_MODEL,
    temperature: float = 0.7,
    top_p: float = 0.9,
    max_tokens: int = 256,
) -> tuple[str, float, dict]:
    """
    Call the Google Gemini API (using Gemini 2.5 Flash as standard) and return
    the response text, latency, and token usage stats.

    Args:
        prompt:      The user message to send.
        model:       The Gemini model to use (default: gemini-2.5-flash).
        temperature: Sampling temperature.
        top_p:       Nucleus sampling threshold.
        max_tokens:  Maximum number of tokens to generate.

    Returns:
        A tuple of:
            - response_text (str)
            - latency_seconds (float)
            - usage (dict with keys: 'input_tokens', 'output_tokens')

    Hint:
        Option A (New Google GenAI SDK):
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            # Configure using types.GenerateContentConfig
            
        Option B (Legacy Google GenerativeAI SDK):
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model_inst = genai.GenerativeModel(model)
            # Configure using genai.types.GenerationConfig
            
        Ensure your usage dictionary extracts 'input_tokens' and 'output_tokens' 
        from the response metadata (e.g. response.usage_metadata).
    """
    # Gemini 2.5 Flash "thinks" by default and those tokens count against
    # max_tokens: with max_tokens=256 thinking used ~241 tokens and the answer
    # was cut off (finish_reason=MAX_TOKENS). Turn thinking off for Flash models
    # (Pro cannot disable it, so leave Pro on the model default).
    thinking_budget = 0 if "flash" in model else None
    response, latency = gemini_generate(prompt, model, temperature, top_p, max_tokens,
                                        thinking_budget=thinking_budget)
    return response.text or "", latency, gemini_usage(response)


# ---------------------------------------------------------------------------
# Task 3 — Call Anthropic Claude (Exploratory track)
# ---------------------------------------------------------------------------
def call_anthropic(
    prompt: str,
    model: str = ANTHROPIC_MODEL,
    temperature: float = 0.7,
    top_p: float = 0.9,
    max_tokens: int = 256,
) -> tuple[str, float, dict]:
    """
    Call the Anthropic Claude API (using Claude 3.5 Haiku as default) and return
    the response text, latency, and token usage stats.

    Args:
        prompt:      The user message to send.
        model:       The Claude model to use (default: claude-3-5-haiku).
        temperature: Sampling temperature (0.0 - 1.0).
        top_p:       Nucleus sampling threshold.
        max_tokens:  Maximum output tokens.

    Returns:
        A tuple of:
            - response_text (str)
            - latency_seconds (float)
            - usage (dict with keys: 'input_tokens', 'output_tokens')

    Hint:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        # response.usage contains input_tokens and output_tokens
    """
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    base = {"model": model, "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]}
    # anthropic SDK >= 2.0 removed temperature/top_p from messages.create();
    # only send them when this SDK version still accepts them.
    import inspect
    params = inspect.signature(client.messages.create).parameters
    if "temperature" in params or any(p.kind is p.VAR_KEYWORD for p in params.values()):
        base.update(temperature=temperature, top_p=top_p)
    response, latency = timed(lambda: client.messages.create(**base))
    text = "".join(getattr(part, "text", "") for part in response.content)
    usage = make_usage(response.usage.input_tokens, response.usage.output_tokens)
    return text, latency, usage


# ---------------------------------------------------------------------------
# Task 4 — Compare Models (OpenAI GPT-4o vs OpenAI Mini vs Gemini 2.5 Flash)
# ---------------------------------------------------------------------------
def compare_models(prompt: str) -> dict:
    """
    Call OpenAI (gpt-4o), OpenAI Mini (gpt-4o-mini), and Gemini 2.5 Flash (gemini-2.5-flash)
    with the same prompt and return a structured comparison dictionary.

    Calculate the exact USD token cost for input + output using the prices in PRICING_1M_TOKENS.

    Args:
        prompt: The user message to send to all models.

    Returns:
        A dictionary containing:
            - "gpt4o": { "response": str, "latency": float, "cost": float, "input_tokens": int, "output_tokens": int }
            - "gpt4o_mini": { "response": str, "latency": float, "cost": float, "input_tokens": int, "output_tokens": int }
            - "gemini_flash": { "response": str, "latency": float, "cost": float, "input_tokens": int, "output_tokens": int }
    """
    def _pack(model_name: str, result: tuple) -> dict:
        text, latency, usage = result
        return {
            "response": text,
            "latency": latency,
            "cost": calc_cost(model_name, usage),
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
        }

    return {
        "gpt4o": _pack(OPENAI_MODEL, call_openai(prompt)),
        "gpt4o_mini": _pack(OPENAI_MINI_MODEL, call_openai(prompt, model=OPENAI_MINI_MODEL)),
        "gemini_flash": _pack(GEMINI_MODEL, call_gemini(prompt)),
    }


# ---------------------------------------------------------------------------
# Task 5 — Streaming chatbot with Gemini 2.5 (Focus Model)
# ---------------------------------------------------------------------------
def streaming_chatbot() -> None:
    """
    Run an interactive streaming chatbot in the terminal using Gemini 2.5.

    Behaviour:
        - Streams response tokens from Gemini 2.5 Flash as they arrive.
        - Maintains the last 3 turns of conversation history for context.
        - Typing 'quit' or 'exit' ends the session.

    Hints:
        - Maintain a history list of conversation turns.
        - Check how to stream responses using client.chats or model.generate_content(..., stream=True).
        - Keep history limited to the last 3 turns to optimize context window and costs.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    # Completed turns only: [user, model, user, model, ...]. Keeping the last
    # 6 messages = 3 full turns, so the context always starts with a user turn.
    history: list[dict] = []  # each item: {"role": "user" | "model", "text": str}
    # Thinking off: first token arrives ~0.6s instead of ~3.8s (see benchmark).
    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0))

    def short_error(e: Exception) -> str:
        s = str(e)
        if "PerDay" in s:
            return "Hết quota theo ngày của gói Free. Thử lại vào ngày mai hoặc dùng key project khác."
        if "429" in s:
            return "Đang bị giới hạn tốc độ (429). Đợi ít phút rồi hỏi lại."
        return s.splitlines()[0][:200]

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if user_input.lower() in ("quit", "exit"):
            print("Bye!")
            break
        if not user_input:
            continue

        turn = history[-6:] + [{"role": "user", "text": user_input}]
        contents = [
            types.Content(role=m["role"], parts=[types.Part(text=m["text"])])
            for m in turn
        ]

        print("Gemini: ", end="", flush=True)
        reply_parts: list[str] = []
        failed = None
        for attempt in range(4):
            try:
                for chunk in client.models.generate_content_stream(
                    model=GEMINI_MODEL, contents=contents, config=config
                ):
                    piece = chunk.text or ""
                    reply_parts.append(piece)
                    print(piece, end="", flush=True)
                failed = None
                break
            except Exception as e:
                failed = e
                # Retry only per-minute rate limits, and only if nothing was printed yet
                # (otherwise a retry would print the answer twice).
                if "429" not in str(e) or "PerDay" in str(e) or reply_parts or attempt == 3:
                    break
                wait = 5 * 2 ** attempt  # exponential backoff: 5s, 10s, 20s
                print(f"[giới hạn tốc độ, thử lại sau {wait}s...] ", end="", flush=True)
                time.sleep(wait)
        if failed is not None:
            print(f"\n[Lỗi] {short_error(failed)}")
            continue  # this turn is not saved to history
        print()

        history += [{"role": "user", "text": user_input},
                    {"role": "model", "text": "".join(reply_parts)}]
        history = history[-6:]


# ---------------------------------------------------------------------------
# Bonus Task A — Retry with exponential backoff
# ---------------------------------------------------------------------------
def retry_with_backoff(
    fn: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 0.1,
) -> Any:
    """
    Call fn(). If it raises an exception, retry up to max_retries times
    with exponential backoff (delay = base_delay * 2^attempt).

    Args:
        fn:          Zero-argument callable to execute.
        max_retries: Maximum number of retry attempts.
        base_delay:  Initial delay in seconds before the first retry.

    Returns:
        The return value of fn() on success.

    Raises:
        The last exception raised by fn() after all retries are exhausted.
    """
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception:
            if attempt == max_retries:
                raise
            time.sleep(base_delay * (2 ** attempt))


# ---------------------------------------------------------------------------
# Bonus Task B — Batch compare
# ---------------------------------------------------------------------------
def batch_compare(prompts: list[str]) -> list[dict]:
    """
    Run compare_models on each prompt in the list.

    Args:
        prompts: List of prompt strings.

    Returns:
        List of dicts, each being the compare_models result with an extra
        key "prompt" containing the original prompt string.
    """
    results = []
    for prompt in prompts:
        row = dict(compare_models(prompt))
        row["prompt"] = prompt
        results.append(row)
    return results


# ---------------------------------------------------------------------------
# Bonus Task C — Format comparison table
# ---------------------------------------------------------------------------
def format_comparison_table(results: list[dict]) -> str:
    """
    Format a list of batch compare results as a readable Markdown table string.

    Args:
        results: List of dicts as returned by batch_compare.

    Returns:
        A beautiful Markdown table string with columns:
        | Prompt | Model | Response (truncated) | Latency | Tokens (In/Out) | Cost (USD) |
    """
    labels = {"gpt4o": "GPT-4o", "gpt4o_mini": "GPT-4o-Mini", "gemini_flash": "Gemini-Flash"}

    def _cell(value) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [
        "| Prompt | Model | Response (truncated) | Latency | Tokens (In/Out) | Cost (USD) |",
        "|---|---|---|---|---|---|",
    ]
    for row in results:
        for key, label in labels.items():
            stats = row.get(key)
            if not stats:
                continue
            resp = stats["response"]
            if len(resp) > 50:
                resp = resp[:50] + "..."
            lines.append(
                f"| {_cell(row.get('prompt', ''))} | {label} | {_cell(resp)} | "
                f"{stats['latency']:.2f}s | {stats['input_tokens']}/{stats['output_tokens']} | "
                f"${stats['cost']:.8f} |"
            )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point for manual testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Model Comparison Test ===")
    test_prompt = "Hãy giải thích sự khác biệt giữa temperature và top_p bằng tiếng Việt ngắn gọn trong 2 câu."
    try:
        # Note: Requires valid API keys set in environment variables
        result = compare_models(test_prompt)
        for model_name, stats in result.items():
            print(f"\n[{model_name.upper()}]")
            print(f"Latency: {stats['latency']:.2f}s | Cost: ${stats['cost']:.8f}")
            print(f"Tokens: {stats['input_tokens']} in / {stats['output_tokens']} out")
            print(f"Response: {stats['response']}")
    except Exception as e:
        print(f"Skipping live API comparison test: {e}")
        print("Set your API keys to run manual tests.")

    print("\n=== Starting Gemini 2.5 Chatbot (type 'quit' to exit) ===")
    try:
        streaming_chatbot()
    except Exception as e:
        print(f"Chatbot failed to start: {e}")
