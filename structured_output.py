"""
structured_output.py
----------------------
Checkpoint 5: Çıxış parsing/validasiyası

Modeldən strukturlaşdırılmış (JSON) cavab istəyəndə, model bəzən:
- JSON-un ətrafına izahedici mətn əlavə edir ("Əlbəttə, budur JSON: {...}")
- Markdown code-block işarələri qoyur (```json ... ```)
- Format pozula bilər (əskik mötərizə, vergüldən sonra artıq element və s.)

Bu modul modelin "həmişə təmiz JSON qaytaracağını" FƏRZ ETMİR — əksinə,
bu pozuntuları tutub düzəltməyə çalışır və lazım gələrsə modelə "səhv format,
yenidən cəhd et" deyərək bir daha sorğu göndərir.
"""

import json
import re
from hf_client import HFClient


class StructuredOutputError(Exception):
    """Bütün cəhdlərdən sonra da etibarlı JSON alına bilmədikdə atılır."""
    pass


def _extract_json_candidate(text: str) -> str:
    """
    Mətnin içindən JSON obyektinə bənzəyən hissəni çıxarmağa çalışır.
    Məsələn: 'Əlbəttə budur: {"a": 1} Ümid edirəm kömək etdi!' -> '{"a": 1}'
    """
    text = text.strip()

    # 1) Markdown code-block işarələrini təmizlə (```json ... ``` və ya ``` ... ```)
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # 2) Əgər mətn artıq təmiz JSON-dursa, birbaşa qaytar
    if text.startswith("{") and text.endswith("}"):
        return text

    # 3) Mətnin içindən ilk '{' və son '}' arasındakı hissəni tap
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    # Heç bir JSON-a bənzər struktur tapılmadı
    return text


def _try_parse_json(text: str) -> dict | None:
    """JSON parse etməyə çalışır, uğursuz olarsa None qaytarır (xəta atmır)."""
    candidate = _extract_json_candidate(text)
    try:
        return json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        return None


def get_structured_response(
    user_prompt: str,
    required_keys: list[str],
    system_prompt: str | None = None,
    client: HFClient | None = None,
    max_attempts: int = 3,
) -> dict:
    """
    Modeldən JSON formatında strukturlaşdırılmış cavab alır və validasiya edir.

    Parametrlər:
        user_prompt: modelə göndəriləcək əsas sorğu (JSON tələbi ilə birlikdə)
        required_keys: JSON-da mütləq olmalı açarların siyahısı, məs. ["title", "summary"]
        max_attempts: neçə dəfə cəhd edilsin (korlanmış JSON halında)

    Return: doğrulanmış dict (bütün required_keys mövcuddur)

    Xəta: StructuredOutputError - bütün cəhdlərdən sonra da etibarlı/tam JSON
    alına bilmədikdə.
    """
    client = client or HFClient()

    base_system_prompt = (
        system_prompt
        or "Sən yalnız JSON formatında cavab verən köməkçisən."
    )
    # Modelə JSON formatını AYDIN şəkildə diqtə edirik
    json_instruction = (
        f"\n\nÇOX VACİB: Cavabını YALNIZ etibarlı JSON formatında ver. "
        f"JSON-un ətrafına heç bir izah, salamlama və ya markdown ```kod bloku``` əlavə etmə. "
        f"JSON aşağıdakı açarları mütləq daxil etməlidir: {', '.join(required_keys)}."
    )

    current_user_prompt = user_prompt + json_instruction
    last_raw_response = None
    last_error = None

    for attempt in range(1, max_attempts + 1):
        result = client.send_message(
            system_prompt=base_system_prompt,
            user_prompt=current_user_prompt,
            temperature=0.2,  # JSON strukturunda sabitlik üçün aşağı temperature
        )
        last_raw_response = result["text"]

        parsed = _try_parse_json(last_raw_response)

        if parsed is None:
            last_error = "Cavab etibarlı JSON kimi parse edilə bilmədi."
        else:
            missing = [k for k in required_keys if k not in parsed]
            if missing:
                last_error = f"JSON parse edildi, amma açarlar əskikdir: {missing}"
            else:
                # Uğur! Doğrulanmış JSON qaytarılır
                return parsed

        # Uğursuz olduq - əgər hələ cəhd haqqı varsa, modelə düzəliş üçün yenidən sorğu göndər
        if attempt < max_attempts:
            print(
                f"[Xəbərdarlıq] Cəhd {attempt}/{max_attempts}: {last_error} "
                f"Yenidən cəhd edilir..."
            )
            current_user_prompt = (
                user_prompt
                + f"\n\nDİQQƏT: Əvvəlki cavabın etibarsız idi ({last_error}). "
                f"Bu dəfə YALNIZ düzgün, tam JSON qaytar, heç bir əlavə mətn yazma."
            )

    # Bütün cəhdlər uğursuz oldu
    raise StructuredOutputError(
        f"{max_attempts} cəhddən sonra da etibarlı JSON alına bilmədi. "
        f"Son xəta: {last_error}. Son xam cavab: {last_raw_response!r}"
    )


# ------------------------------------------------------------------
# Nümunə istifadə: mətn xülasələşdirmə - strukturlaşdırılmış JSON çıxış
# ------------------------------------------------------------------
def summarize_text_structured(text: str, client: HFClient | None = None) -> dict:
    """
    Verilmiş mətni JSON formatında xülasələşdirir:
    {"title": str, "summary": str, "keywords": [str, ...]}
    """
    prompt = (
        f"Aşağıdakı mətni xülasələşdir və JSON formatında qaytar "
        f"(açarlar: title, summary, keywords - keywords bir array olmalıdır):\n\n{text}"
    )
    return get_structured_response(
        user_prompt=prompt,
        required_keys=["title", "summary", "keywords"],
        client=client,
    )


if __name__ == "__main__":
    print("=== NORMAL TEST: Mətn xülasələşdirmə (JSON) ===")
    sample_text = (
        "Süni intellekt (AI) son illərdə sürətlə inkişaf edib. Xüsusilə böyük dil "
        "modelləri (LLM) mətn yazma, tərcümə, kod yazma kimi tapşırıqlarda insan "
        "səviyyəsinə yaxınlaşıb. Bununla belə, etik məsələlər və məlumatların "
        "düzgünlüyü hələ də mübahisə mövzusudur."
    )
    try:
        result = summarize_text_structured(sample_text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except StructuredOutputError as e:
        print(f"XƏTA: {e}")

    print("\n=== EDGE-CASE TEST: qəsdən korlanmış JSON simulyasiyası ===")
    print("(_extract_json_candidate funksiyasının özünü sınayaq)")

    test_cases = [
        '{"title": "Test", "summary": "Qısa", "keywords": ["a", "b"]}',
        'Əlbəttə, budur JSON: {"title": "Test", "summary": "Qısa", "keywords": ["a"]} Ümid edirəm kömək etdi!',
        '```json\n{"title": "Test", "summary": "Qısa", "keywords": []}\n```',
        '{"title": "Test", "summary": "Natamam JSON, mötərizə bağlanmayıb',  # korlanmış
    ]

    for i, case in enumerate(test_cases, start=1):
        parsed = _try_parse_json(case)
        status = "✅ UĞURLU" if parsed else "❌ PARSE EDİLƏ BİLMƏDİ (gözlənilən nəticə #4 üçün)"
        print(f"\nTest {i}: {status}")
        print(f"  Xam mətn: {case[:70]}...")
        print(f"  Nəticə: {parsed}")
