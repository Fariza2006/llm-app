"""
hf_client.py
-------------
Hugging Face Inference API ilə əlaqə qurmaq üçün əsas modul.
(Anthropic/OpenAI-dan fərqli olaraq PULSUZDUR - kredit kartı tələb etmir.)

Checkpoint 1: API inteqrasiyası
- API açarı (HF token) environment variable-dan (.env) oxunur, kodda HARDCODE edilmir.
- Request/response düzgün formalaşdırılır və idarə olunur.

Hugging Face-də pulsuz hesab və token necə alınır:
1. https://huggingface.co/join -> pulsuz qeydiyyat (kart lazım deyil)
2. https://huggingface.co/settings/tokens -> "Create new token" (Read icazəsi kifayətdir)
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()


class HFClient:
    """Hugging Face Inference API ilə işləmək üçün nazik (thin) wrapper sinif."""

    # Mətn generasiyası üçün pulsuz, geniş yayılmış açıq model
    DEFAULT_MODEL = "HuggingFaceH4/zephyr-7b-beta"

    def __init__(self, model: str | None = None):
        # API açarını (token) environment variable-dan oxuyuruq (heç vaxt kodda yazılmır!)
        self.api_token = os.getenv("HF_API_TOKEN")

        if not self.api_token:
            raise EnvironmentError(
                "HF_API_TOKEN tapılmadı. Zəhmət olmasa layihə kökündə '.env' faylı "
                "yaradın və içinə HF_API_TOKEN=... əlavə edin. Pulsuz token almaq üçün: "
                "https://huggingface.co/settings/tokens"
            )

        self.model = model or os.getenv("HF_MODEL", self.DEFAULT_MODEL)
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model}"
        self.headers = {"Authorization": f"Bearer {self.api_token}"}

    def send_message(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        timeout: int = 30,
    ) -> dict:
        """
        Hugging Face Inference API-yə sorğu göndərir və cavabı
        strukturlaşdırılmış şəkildə qaytarır.

        Return dəyəri (dict):
            {
                "text": str,             # modelin mətn cavabı
                "model": str,             # istifadə olunan model adı
                "elapsed_seconds": float, # sorğunun cavab müddəti
                "raw_response": object    # API-dan gələn xam JSON
            }
        """
        # Chat formatını sadə prompt-a çeviririk (bir çox açıq modellər bu formatı gözləyir)
        full_prompt = ""
        if system_prompt:
            full_prompt += f"<|system|>\n{system_prompt}</s>\n"
        full_prompt += f"<|user|>\n{user_prompt}</s>\n<|assistant|>\n"

        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "return_full_text": False,
            },
        }

        # --- Request ---
        start = time.time()
        response = requests.post(
            self.api_url, headers=self.headers, json=payload, timeout=timeout
        )
        elapsed = time.time() - start

        # --- Response idarəetməsi ---
        if response.status_code != 200:
            raise RuntimeError(
                f"Hugging Face API xətası (status {response.status_code}): {response.text}"
            )

        data = response.json()

        # API bəzən model "yüklənir" mesajı ilə cavab verir (soyuq başlanğıc)
        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(f"Hugging Face API cavab xətası: {data['error']}")

        # Normal halda cavab: [{"generated_text": "..."}]
        generated_text = data[0]["generated_text"] if isinstance(data, list) else str(data)

        return {
            "text": generated_text.strip(),
            "model": self.model,
            "elapsed_seconds": round(elapsed, 2),
            "raw_response": data,
        }


if __name__ == "__main__":
    # Sadə manual test - modulun düzgün işlədiyini yoxlamaq üçün
    client = HFClient()

    result = client.send_message(
        system_prompt="Sən qısa və dəqiq cavab verən köməkçisən.",
        user_prompt="Salam! Bu sadəcə API inteqrasiyasını yoxlamaq üçün test sorğusudur. Bir cümləylə özünü tanıt.",
    )

    print("=== CAVAB ===")
    print(result["text"])
    print("\n=== METADATA ===")
    print(f"Model: {result['model']}")
    print(f"Cavab müddəti: {result['elapsed_seconds']} saniyə")
