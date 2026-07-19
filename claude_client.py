"""
claude_client.py
-----------------
Anthropic Claude API ilə əlaqə qurmaq üçün əsas modul.

Checkpoint 1: API inteqrasiyası
- API açarı environment variable-dan (.env) oxunur, kodda HARDCODE edilmir.
- Request/response düzgün formalaşdırılır və idarə olunur.
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic

# .env faylındakı dəyişənləri yükləyirik (ANTHROPIC_API_KEY və s.)
load_dotenv()


class ClaudeClient:
    """Anthropic Claude API ilə işləmək üçün nazik (thin) wrapper sinif."""

    def __init__(self, model: str | None = None):
        # API açarını environment variable-dan oxuyuruq (heç vaxt kodda yazılmır!)
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY tapılmadı. Zəhmət olmasa layihə kökündə "
                "'.env' faylı yaradın və içinə ANTHROPIC_API_KEY=... əlavə edin "
                "(nümunə üçün .env.example faylına baxın)."
            )

        # Model adını da environment-dən oxumaq mümkündür, ya default veririk
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

        # Anthropic SDK klienti - API key ayrıca dəyişəndə saxlanılır, koda yazılmır
        self.client = Anthropic(api_key=api_key)

    def send_message(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> dict:
        """
        Claude API-yə sorğu göndərir və cavabı strukturlaşdırılmış şəkildə qaytarır.

        Return dəyəri (dict):
            {
                "text": str,          # modelin mətn cavabı
                "stop_reason": str,   # sorğunun niyə bitdiyi (end_turn, max_tokens, s.)
                "usage": {            # token istifadəsi (cost hesablamaq üçün lazımdır)
                    "input_tokens": int,
                    "output_tokens": int
                },
                "raw_response": object  # SDK-nın orijinal cavab obyekti
            }
        """
        messages = [{"role": "user", "content": user_prompt}]

        request_kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        # System prompt yalnız verilibsə əlavə olunur
        if system_prompt:
            request_kwargs["system"] = system_prompt

        # --- Request ---
        response = self.client.messages.create(**request_kwargs)

        # --- Response idarəetməsi ---
        # response.content bir siyahıdır (text blokları ola bilər)
        text_parts = [
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ]
        full_text = "\n".join(text_parts)

        return {
            "text": full_text,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            "raw_response": response,
        }


if __name__ == "__main__":
    # Sadə manual test - modulun düzgün işlədiyini yoxlamaq üçün
    client = ClaudeClient()

    result = client.send_message(
        system_prompt="Sən qısa və dəqiq cavab verən köməkçisən.",
        user_prompt="Salam! Bu sadəcə API inteqrasiyasını yoxlamaq üçün test sorğusudur. Bir cümləylə özünü tanıt.",
    )

    print("=== CAVAB ===")
    print(result["text"])
    print("\n=== METADATA ===")
    print(f"Stop reason: {result['stop_reason']}")
    print(f"Token istifadəsi: {result['usage']}")
