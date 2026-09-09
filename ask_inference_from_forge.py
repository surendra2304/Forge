import asyncio
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
from app.integrations.ai_universe_client import AIUniverseClient

questions = [
    "What static analysis heuristics best detect memory leaks and unclosed sockets in asynchronous Python applications?",
    "How should autonomous pull request conflict resolution rank AST transformations versus textual diffs?",
    "Evaluate test coverage prioritization techniques for continuous integration pipelines under tight execution budgets.",
    "What architecture pattern best isolates untrusted dynamic code execution in lightweight sandbox environments?",
    "How should automated dependency vulnerability scanners prioritize exploitable call paths over static CVE matches?"
]

async def main():
    print("=" * 80)
    print("AGENT [2/9]: FORGE -> INFERENCE GATEWAY (5 QUESTIONS)")
    print("Client: app.integrations.ai_universe_client.AIUniverseClient")
    print("=" * 80)
    
    client = AIUniverseClient()
    print(f"Target URL: {client.base_url}")
    print(f"API Key:    {client.api_key[:4]}...")
    
    results = []
    for i, q in enumerate(questions, 1):
        t0 = time.perf_counter()
        try:
            res = await client.ask(q)
            lat = (time.perf_counter() - t0) * 1000
            run_id = res.run_id or "N/A"
            ans_snip = res.answer[:120].replace("\n", " ")
            print(f"[FORGE Q{i}/5] HTTP 200 | {lat:>7.1f}ms | Run: {run_id} | Ans: {ans_snip}...")
            results.append({"q_num": i, "status": 200, "latency_ms": round(lat, 1), "run_id": run_id, "answer": ans_snip})
        except Exception as e:
            lat = (time.perf_counter() - t0) * 1000
            print(f"[FORGE Q{i}/5] ERROR | {lat:>7.1f}ms | {e}")
            results.append({"q_num": i, "status": "ERROR", "latency_ms": round(lat, 1), "error": str(e)})
            
    print("-" * 80)
    lats = [r["latency_ms"] for r in results if r["status"] == 200]
    if lats:
        print(f"FORGE Batch Complete: Avg Latency = {sum(lats)/len(lats):.1f}ms (Min: {min(lats):.1f}ms, Max: {max(lats):.1f}ms)")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
