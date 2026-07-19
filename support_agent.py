"""
support_agent.py
------------------
Checkpoint 2: Prompt Engineering

Müştəri dəstəyi cavab generatoru üçün strukturlaşdırılmış system + user prompt,
və few-shot nümunələr istifadə edir.

Prinsip:
- System prompt: modelin ROLUNU, TONUNU və QAYDALARINI müəyyən edir (dəyişməz hissə).
- Few-shot nümunələr: modelə "yaxşı cavab" necə olmalıdır göstərir (nümunə cütlər).
- User prompt: hər sorğuda dəyişən hissədir (müştərinin mesajı + kontekst).
"""

from hf_client import HFClient


# ------------------------------------------------------------------
# 1) SYSTEM PROMPT — modelin rolu, tonu və sərt qaydaları
# ------------------------------------------------------------------
SYSTEM_PROMPT = """Sən bir e-ticarət şirkətinin müştəri dəstəyi köməkçisisən.

QAYDALAR:
1. Həmişə nəzakətli, empatik və peşəkar ol.
2. Cavabların qısa və konkret olsun (maksimum 4-5 cümlə).
3. Heç vaxt yalan məlumat, saxta endirim kodu və ya olmayan tarixlər uydurma.
4. Əgər sualın cavabını bilmirsənsə və ya problem mürəkkəbdirsə (məsələn, ödəniş
   qaytarılması, hüquqi iddia), müştəriyə deyəcəksən ki, bu məsələ insan
   operatora yönləndiriləcək.
5. Cavabı HƏMİŞƏ Azərbaycan dilində ver, müştəri hansı dildə yazsa da.
6. Emosional müştərilərə əvvəlcə anlayış göstər, sonra həll yolu təklif et.
"""


# ------------------------------------------------------------------
# 2) FEW-SHOT NÜMUNƏLƏR — modelə cavabın formatını göstərmək üçün
#    (real sorğudan əvvəl "keçmiş dialoq" kimi əlavə olunur)
# ------------------------------------------------------------------
FEW_SHOT_EXAMPLES = [
    {
        "customer": "Sifarişim 5 gündür gəlmir, artıq bezmişəm!",
        "agent": (
            "Anlayıram, gecikmə narahatçılıq yaradıb və üzr istəyirəm bunun üçün. "
            "Zəhmət olmasa sifariş nömrənizi paylaşın, mən dərhal statusunu yoxlayıb "
            "sizə dəqiq məlumat verəcəm."
        ),
    },
    {
        "customer": "Kartımdan pul çıxıb amma sifariş təsdiqlənməyib, pulumu geri istəyirəm!",
        "agent": (
            "Bu vəziyyəti başa düşürəm və narahatçılığınız tamamilə haqlıdır. "
            "Ödəniş qaytarılması məsələləri üçün sizi mütəxəssis operatorumuza "
            "yönləndirirəm, onlar hesabınızı yoxlayıb 24 saat ərzində sizinlə əlaqə saxlayacaq."
        ),
    },
    {
        "customer": "Endirim kodu işləmir, kömək edərsiniz?",
        "agent": (
            "Əlbəttə, kömək etməkdən məmnun olaram. Zəhmət olmasa istifadə etdiyiniz "
            "kodu və hansı məhsul üçün tətbiq etdiyinizi yazın, mən səbəbini yoxlayım."
        ),
    },
]


def _build_few_shot_block() -> str:
    """Few-shot nümunələrini mətn bloku şəklində formalaşdırır."""
    blocks = []
    for i, ex in enumerate(FEW_SHOT_EXAMPLES, start=1):
        blocks.append(
            f"Nümunə {i}:\nMüştəri: {ex['customer']}\nKöməkçi: {ex['agent']}"
        )
    return "\n\n".join(blocks)


def build_user_prompt(customer_message: str, order_context: str | None = None) -> str:
    """
    Real müştəri sorğusu üçün user prompt-u qurur:
    few-shot nümunələr + (varsa) sifariş konteksti + real müştəri mesajı.
    """
    parts = [
        "Aşağıda yaxşı cavabların nümunələri verilib. Eyni tərzdə, real müştəriyə cavab yaz.",
        _build_few_shot_block(),
    ]

    if order_context:
        parts.append(f"Sifariş konteksti: {order_context}")

    parts.append(f"\nİndi bu müştəriyə cavab yaz:\nMüştəri: {customer_message}\nKöməkçi:")

    return "\n\n".join(parts)


def generate_support_reply(
    customer_message: str,
    order_context: str | None = None,
    client: HFClient | None = None,
) -> dict:
    """
    Müştəri mesajı üçün struktur laşdırılmış prompt qurur, API-yə göndərir
    və cavabı qaytarır.
    """
    client = client or HFClient()
    user_prompt = build_user_prompt(customer_message, order_context)

    result = client.send_message(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.4,  # dəstək cavabları üçün aşağı temperature = sabit, öngörülən ton
    )
    return result


if __name__ == "__main__":
    # Manual test - real müştəri ssenarisi ilə
    test_cases = [
        {
            "customer_message": "Sifariş #4521 hələ də çatmayıb, izləmə linki də işləmir.",
            "order_context": "Sifariş #4521, 6 gün əvvəl verilib, kuryer şirkəti: Bravo Kuryer.",
        },
        {
            "customer_message": "Bu məhsulun rəngi şəkildəkindən fərqlidir, geri qaytarmaq istəyirəm.",
            "order_context": None,
        },
    ]

    for i, case in enumerate(test_cases, start=1):
        print(f"\n--- Test {i} ---")
        print(f"Müştəri: {case['customer_message']}")
        result = generate_support_reply(**case)
        print(f"Köməkçi: {result['text']}")
        print(f"(Token istifadəsi: {result['usage']})")
