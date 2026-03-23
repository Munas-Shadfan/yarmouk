"""
Agent integration tests — sends real queries to the live server and validates responses.
Run with:  python test_agent.py
"""
from __future__ import annotations
import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from typing import AsyncIterator

import aiohttp

BASE = "http://127.0.0.1:8000"
CHAT_URL = f"{BASE}/api/chat"

# ─────────────────────────────────────────────────────────────────────────────
# Test cases — (description, query, expected_keywords_in_answer)
# ─────────────────────────────────────────────────────────────────────────────
TESTS = [
    {
        "name": "01 — Academic calendar (web page + PDF)",
        "query": "What are the important dates for the 2025/2026 academic year at Yarmouk?",
        "expect": ["2025", "2026"],
        "tools_expected": ["web_page_tool"],
    },
    {
        "name": "02 — Available majors (PDF extraction)",
        "query": "What majors are available at Yarmouk University?",
        "expect": ["majors", "program", "تخصص", "faculty", "college"],
        "tools_expected": ["pdf_extraction_tool"],
    },
    {
        "name": "03 — Registration & admission (admreg page)",
        "query": "How do I register for courses at Yarmouk University?",
        "expect": ["registration", "register", "تسجيل", "semester", "admreg"],
        "tools_expected": ["web_page_tool", "tavily_tool"],
    },
    {
        "name": "04 — Library services",
        "query": "What services does the Yarmouk University library offer?",
        "expect": ["library", "مكتبة", "database", "resources", "Hussein"],
        "tools_expected": ["web_page_tool", "tavily_tool"],
    },
    {
        "name": "05 — Jobs / HR",
        "query": "Are there any job vacancies at Yarmouk University right now?",
        "expect": ["job", "vacanc", "HR", "وظائف", "hr.yu.edu.jo"],
        "tools_expected": ["web_page_tool", "tavily_tool"],
    },
    {
        "name": "06 — Graduation requirements",
        "query": "What are the graduation requirements at Yarmouk University?",
        "expect": ["graduat", "تخرج", "credit", "requirement", "degree"],
        "tools_expected": ["web_page_tool"],
    },
    {
        "name": "07 — Arabic query (calendar)",
        "query": "ما هي مواعيد التسجيل في جامعة اليرموك؟",
        "expect": ["تسجيل", "جدول", "موعد", "فصل", "الدراسي"],
        "tools_expected": ["web_page_tool"],
    },
    {
        "name": "08 — Out-of-scope (must refuse)",
        "query": "What is the capital of France?",
        "expect": ["yarmouk", "university", "اليرموك", "only", "sorry", "unrelated"],
        "tools_expected": [],
        "refuse": True,
    },
    {
        "name": "09 — QRC training courses",
        "query": "What training courses does the Queen Rania Center at Yarmouk offer?",
        "expect": ["Queen Rania", "QRC", "training", "course", "diploma", "دورة"],
        "tools_expected": ["web_page_tool"],
    },
    {
        "name": "10 — Staff contact / phone directory",
        "query": "How can I contact the Admission and Registration office at Yarmouk?",
        "expect": ["phone", "contact", "admreg", "registration", "هاتف", "تواصل"],
        "tools_expected": ["pdf_extraction_tool", "web_page_tool"],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class TestResult:
    name: str
    passed: bool
    answer: str
    tools_used: list[str]
    elapsed: float
    failure_reason: str = ""


async def stream_query(session: aiohttp.ClientSession, query: str, thread_id: str) -> tuple[str, list[str]]:
    """Send query, collect full streamed answer + tool names used."""
    payload = {"query": query, "thread_id": thread_id}
    answer_parts: list[str] = []
    tools_used: list[str] = []

    async with session.post(CHAT_URL, json=payload) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}: {await resp.text()}")
        async for raw_line in resp.content:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if not data_str or data_str == "[DONE]":
                continue
            try:
                evt = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            t = evt.get("type", "")
            if t == "token":
                answer_parts.append(evt.get("text", ""))
            elif t == "status":
                label = evt.get("label", "")
                # Extract tool name from label
                for tool_name in ["web_page_tool", "pdf_extraction_tool",
                                  "tavily_tool", "rag_tool", "save_unanswered_question"]:
                    if tool_name.replace("_", " ").split()[0] in label.lower() or \
                       tool_name in label:
                        if tool_name not in tools_used:
                            tools_used.append(tool_name)
            elif t == "done":
                break

    return "".join(answer_parts), tools_used


async def run_test(session: aiohttp.ClientSession, test: dict, idx: int) -> TestResult:
    t0 = time.monotonic()
    thread_id = f"test-{idx}-{int(time.time())}"
    try:
        answer, tools_used = await stream_query(session, test["query"], thread_id)
    except Exception as e:
        return TestResult(
            name=test["name"], passed=False,
            answer="", tools_used=[], elapsed=time.monotonic() - t0,
            failure_reason=f"Request failed: {e}",
        )

    elapsed = time.monotonic() - t0
    answer_lower = answer.lower()

    # Check expected keywords
    matched = [kw for kw in test["expect"] if kw.lower() in answer_lower]
    keyword_ok = len(matched) >= max(1, len(test["expect"]) // 3)  # need ≥ 1/3 of keywords

    # For refuse tests: answer should be short and not deeply answer the question
    if test.get("refuse"):
        # Should NOT give a factual answer about France/capital etc.
        bad_answers = ["paris", "france", "capital of france"]
        gave_bad_answer = any(b in answer_lower for b in bad_answers)
        passed = not gave_bad_answer
        failure_reason = "Agent answered an out-of-scope question it should have refused" if not passed else ""
    else:
        passed = keyword_ok
        failure_reason = (
            f"Expected keywords not found. Matched {len(matched)}/{len(test['expect'])}: "
            f"{matched} | Answer preview: {answer[:200]!r}"
        ) if not passed else ""

    return TestResult(
        name=test["name"], passed=passed,
        answer=answer, tools_used=tools_used, elapsed=elapsed,
        failure_reason=failure_reason,
    )


async def main():
    print("=" * 70)
    print("  YARMOUK AI AGENT — INTEGRATION TESTS")
    print(f"  Server: {BASE}")
    print("=" * 70)

    # Quick health check
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE}/health", timeout=aiohttp.ClientTimeout(total=5)) as r:
                status = r.status
        except Exception:
            # Try root
            try:
                async with session.get(BASE, timeout=aiohttp.ClientTimeout(total=5)) as r:
                    status = r.status
            except Exception as e:
                print(f"\n❌  Cannot reach server at {BASE}: {e}")
                print("    Make sure `uv run main.py` is running first.")
                sys.exit(1)

    print(f"\n✅  Server reachable (HTTP {status})\n")

    results: list[TestResult] = []

    connector = aiohttp.TCPConnector(limit=1)  # serial — avoid rate limits
    timeout = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for i, test in enumerate(TESTS, 1):
            print(f"[{i:02d}/{len(TESTS)}] {test['name']} ...", end=" ", flush=True)
            result = await run_test(session, test, i)
            results.append(result)
            icon = "✅" if result.passed else "❌"
            tools_str = ", ".join(result.tools_used) if result.tools_used else "none"
            print(f"{icon}  ({result.elapsed:.1f}s)  tools=[{tools_str}]")
            if not result.passed:
                print(f"         ↳ {result.failure_reason}")
            # Small delay between tests
            await asyncio.sleep(1.5)

    # ── Summary ──────────────────────────────────────────────────────────────
    passed = sum(1 for r in results if r.passed)
    total  = len(results)
    print("\n" + "=" * 70)
    print(f"  RESULTS: {passed}/{total} passed")
    print("=" * 70)

    for r in results:
        icon = "✅" if r.passed else "❌"
        print(f"  {icon}  {r.name}")

    if passed == total:
        print("\n🎉  All tests passed — agent is fully operational!\n")
    else:
        failed = [r for r in results if not r.passed]
        print(f"\n⚠️   {len(failed)} test(s) failed. Showing answers for failed tests:\n")
        for r in failed:
            print(f"── {r.name}")
            print(f"   Answer: {r.answer[:500]!r}")
            print(f"   Reason: {r.failure_reason}")
            print()

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
