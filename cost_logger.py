"""
cost_logger.py
----------------
Checkpoint 6: Əsas cost/token məlumatlılığı

Hər API sorğusunun token istifadəsini və təxmini xərcini bir log faylına
(JSONL formatında) yazır, həmçinin ümumi xərci hesablamaq üçün funksiya təqdim edir.

JSONL seçilib (JSON Lines) çünki:
- Hər sətir ayrı bir JSON obyektidir — fayl böyüsə də asanlıqla append (əlavə) edilə bilər.
- Fayl korlanma riski minimaldır (bir sətir korlansa belə, digərləri oxunur).
"""

import json
import os
from datetime import datetime, timezone

LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), "logs", "usage_log.jsonl")


def _ensure_log_dir():
    """logs/ qovluğu yoxdursa yaradır."""
    log_dir = os.path.dirname(LOG_FILE_PATH)
    os.makedirs(log_dir, exist_ok=True)


def log_usage(
    prompt_preview: str,
    model: str,
    usage: dict | None,
    elapsed_seconds: float | None = None,
    tag: str | None = None,
) -> dict:
    """
    Bir API sorğusunun token/cost məlumatını logs/usage_log.jsonl faylına əlavə edir.

    Parametrlər:
        prompt_preview: sorğunun qısa təsviri (tam mətn deyil, ilk ~80 simvol kifayətdir)
        model: istifadə olunan model adı
        usage: API-dan gələn usage dict-i (prompt_tokens, completion_tokens, estimated_cost və s.)
        elapsed_seconds: sorğunun cavab müddəti
        tag: sorğunun növü (məsələn "support_reply", "summarization", "test")

    Return: yazılan log qeydinin özü (dict)
    """
    _ensure_log_dir()

    usage = usage or {}

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tag": tag or "general",
        "model": model,
        "prompt_preview": prompt_preview[:80],
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "estimated_cost_usd": usage.get("estimated_cost"),
        "elapsed_seconds": elapsed_seconds,
    }

    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry


def summarize_usage() -> dict:
    """
    logs/usage_log.jsonl faylını oxuyub ümumi statistikanı hesablayır:
    - neçə sorğu edilib
    - cəmi token istifadəsi
    - cəmi təxmini xərc (USD)
    """
    if not os.path.exists(LOG_FILE_PATH):
        return {
            "total_requests": 0,
            "total_tokens": 0,
            "total_estimated_cost_usd": 0.0,
        }

    total_requests = 0
    total_tokens = 0
    total_cost = 0.0

    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                # Korlanmış sətri keç, bütün faylı çökdürmə
                continue

            total_requests += 1
            total_tokens += entry.get("total_tokens") or 0
            total_cost += entry.get("estimated_cost_usd") or 0.0

    return {
        "total_requests": total_requests,
        "total_tokens": total_tokens,
        "total_estimated_cost_usd": round(total_cost, 6),
    }


if __name__ == "__main__":
    # Manual test - real API çağırmadan, sadəcə loglama məntiqini yoxlamaq
    print("=== TEST LOG QEYDLƏRİ YAZILIR ===")

    log_usage(
        prompt_preview="Salam! Bu test sorğusudur.",
        model="meta-llama/Llama-3.1-8B-Instruct",
        usage={
            "prompt_tokens": 79,
            "completion_tokens": 24,
            "total_tokens": 103,
            "estimated_cost": 0.0000023,
        },
        elapsed_seconds=1.34,
        tag="test",
    )

    log_usage(
        prompt_preview="Müştəri dəstəyi sorğusu: sifariş gecikməsi",
        model="meta-llama/Llama-3.1-8B-Instruct",
        usage={
            "prompt_tokens": 905,
            "completion_tokens": 80,
            "total_tokens": 985,
            "estimated_cost": 0.0000205,
        },
        elapsed_seconds=2.1,
        tag="support_reply",
    )

    print(f"Log faylı: {LOG_FILE_PATH}")

    print("\n=== ÜMUMI XƏRC HESABATI ===")
    summary = summarize_usage()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
