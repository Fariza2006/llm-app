"""
hf_client.py
-------------
Hugging Face Inference API (router / Inference Providers) ilə əlaqə qurmaq üçün əsas modul.
(Anthropic/OpenAI-dan fərqli olaraq PULSUZDUR - kredit kartı tələb etmir.)

Checkpoint 1: API inteqrasiyası
- API açarı (HF token) environment variable-dan (.env) oxunur, kodda HARDCODE edilmir.
- Request/response düzgün formalaşdırılır və idarə olunur.

QEYD: Hugging Face köhnə "api-inference.huggingface.co" ünvanını 2026-cı ildə
bağlayıb (410 Gone). Yeni, OpenAI-uyğun (OpenAI-compatible) endpoint istifadə olunur:
https://router.huggingface.co/v1/chat/completions

Hugging Face-də pulsuz hesab və token necə alınır:
1. https://huggingface.co/join -> pulsuz qeydiyyat (kart lazım deyil)
2. https://huggingface.co/settings/tokens -> "Create new token" (Read icazəsi kifayətdir)
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Checkpoint 4: hansı xətalarda yenidən cəhd (retry) edilməli
# 429 = Rate limit (həddindən çox sorğu), 500/502/503/504 = server tərəfli müvəqqəti xətalar
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 2  # hər cəhddə ikiqat artır: 2s, 4s, 8s


class HFClient:
    """Hugging Face router (Inference Providers) API ilə işləmək üçün nazik wrapper sinif."""

    # Pulsuz "Inference Providers" tier-i üzərindən əlçatan açıq model
    DEFAULT_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
    API_URL = "https://router.huggingface.co/v1/chat/completions"

    def __init__(self, model: str | None = None):
        # API tokenini environment variable-dan oxuyuruq (heç vaxt kodda yazılmır!)
        self.api_token = os.getenv("HF_API_TOKEN")

        if not self.api_token:
            raise EnvironmentError(
                "HF_API_TOKEN tapılmadı. Zəhmət olmasa layihə kökündə '.env' faylı "
                "yaradın və içinə HF_API_TOKEN=... əlavə edin. Pulsuz token almaq üçün: "
                "https://huggingface.co/settings/tokens"
            )

        self.model = model or os.getenv("HF_MODEL", self.DEFAULT_MODEL)
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def send_message(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 256,
        temperature: float = 0.7,
        timeout: int = 30,
        max_retries: int = MAX_RETRIES,
    ) -> dict:
        """
        Hugging Face router API-yə (OpenAI-uyğun format) sorğu göndərir və
        cavabı strukturlaşdırılmış şəkildə qaytarır.

        Checkpoint 4: Xəta idarəetməsi
        - Rate limit (429) və müvəqqəti server xətaları (500/502/503/504) üçün
          exponential backoff ilə avtomatik yenidən cəhd (retry) edilir.
        - Timeout (vaxt aşımı) və şəbəkə xətaları da retry olunur.
        - Qalıcı xətalar (401 - səhv token, 400 - səhv sorğu) DƏRHAL, retry
          olunmadan aydın mesajla bildirilir (çünki yenidən cəhd onları düzəltməz).

        Return dəyəri (dict):
            {
                "text": str,             # modelin mətn cavabı
                "model": str,             # istifadə olunan model adı
                "elapsed_seconds": float, # sorğunun cavab müddəti
                "usage": dict | None,     # token istifadəsi (varsa)
                "raw_response": object    # API-dan gələn xam JSON
            }
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                start = time.time()
                response = requests.post(
                    self.API_URL, headers=self.headers, json=payload, timeout=timeout
                )
                elapsed = time.time() - start

                # --- Qalıcı (retry etməli olmayan) xətalar ---
                if response.status_code == 401:
                    raise PermissionError(
                        "API tokeni etibarsızdır və ya vaxtı bitib (401). "
                        "Zəhmət olmasa .env faylındakı HF_API_TOKEN-i yoxlayın."
                    )
                if response.status_code == 400:
                    raise ValueError(
                        f"Sorğu formatı səhvdir (400 Bad Request): {response.text}"
                    )

                # --- Müvəqqəti (retry oluna bilən) xətalar ---
                if response.status_code in RETRYABLE_STATUS_CODES:
                    last_error = RuntimeError(
                        f"Müvəqqəti API xətası (status {response.status_code}): "
                        f"{response.text}"
                    )
                    raise last_error

                # --- Digər gözlənilməz xətalar ---
                if response.status_code != 200:
                    raise RuntimeError(
                        f"Hugging Face API xətası (status {response.status_code}): "
                        f"{response.text}"
                    )

                # --- Uğurlu cavab ---
                data = response.json()

                if "error" in data:
                    raise RuntimeError(f"Hugging Face API cavab xətası: {data['error']}")

                generated_text = data["choices"][0]["message"]["content"]

                return {
                    "text": generated_text.strip(),
                    "model": self.model,
                    "elapsed_seconds": round(elapsed, 2),
                    "usage": data.get("usage"),
                    "raw_response": data,
                }

            except (PermissionError, ValueError):
                # Qalıcı xətalar - retry etmədən dərhal yuxarı ötür
                raise

            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                RuntimeError,
            ) as e:
                last_error = e
                if attempt < max_retries:
                    backoff = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
                    print(
                        f"[Xəbərdarlıq] Cəhd {attempt}/{max_retries} uğursuz oldu "
                        f"({type(e).__name__}: {e}). {backoff}s sonra yenidən cəhd olunur..."
                    )
                    time.sleep(backoff)
                else:
                    # Bütün cəhdlər bitdi - son xətanı aydın mesajla bildir
                    raise RuntimeError(
                        f"{max_retries} cəhddən sonra da API-dən cavab alınmadı. "
                        f"Son xəta: {e}"
                    ) from e

        # Nəzəri olaraq bura çatmamalıdır, amma təhlükəsizlik üçün:
        raise RuntimeError(f"Sorğu uğursuz oldu: {last_error}")

    def send_message_stream(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 256,
        temperature: float = 0.7,
        timeout: int = 30,
        on_chunk=None,
    ):
        """
        Checkpoint 3: Streaming cavab idarəetməsi.

        Hugging Face router API-sinə "stream": true ilə sorğu göndərir və
        cavabı hissə-hissə (token-token) qaytarır — Server-Sent Events (SSE)
        formatında gələn məlumatı emal edir.

        Parametrlər:
            on_chunk: hər yeni mətn hissəsi gələndə çağırılan callback funksiya
                      (verilməzsə, mətn birbaşa terminala yazılır).

        Return: tam yığılmış mətn (str) - stream bitdikdən sonra.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        full_text = ""

        try:
            with requests.post(
                self.API_URL,
                headers=self.headers,
                json=payload,
                timeout=timeout,
                stream=True,
            ) as response:

                if response.status_code != 200:
                    raise RuntimeError(
                        f"Hugging Face API xətası (status {response.status_code}): "
                        f"{response.text}"
                    )

                # SSE formatı: hər sətir "data: {...}" şəklində gəlir,
                # axın sonunda "data: [DONE]" göndərilir.
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    if not line.startswith("data:"):
                        continue

                    chunk_raw = line[len("data:"):].strip()

                    if chunk_raw == "[DONE]":
                        break

                    try:
                        chunk_json = json.loads(chunk_raw)
                    except json.JSONDecodeError:
                        # Korlanmış/natamam JSON chunk-ı sadəcə keç (xəta ilə dayanma)
                        continue

                    delta = (
                        chunk_json.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content", "")
                    )

                    if delta:
                        full_text += delta
                        if on_chunk:
                            on_chunk(delta)
                        else:
                            print(delta, end="", flush=True)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Streaming zamanı şəbəkə xətası: {e}") from e

        if on_chunk is None:
            print()  # son sətri bitirmək üçün

        return full_text.strip()


if __name__ == "__main__":
    # Sadə manual test - modulun düzgün işlədiyini yoxlamaq üçün
    client = HFClient()

    print("=== ADİ (NON-STREAMING) CAVAB ===")
    result = client.send_message(
        system_prompt="Sən qısa və dəqiq cavab verən köməkçisən.",
        user_prompt="Salam! Bu sadəcə API inteqrasiyasını yoxlamaq üçün test sorğusudur. Bir cümləylə özünü tanıt.",
    )
    print(result["text"])
    print("\n=== METADATA ===")
    print(f"Model: {result['model']}")
    print(f"Cavab müddəti: {result['elapsed_seconds']} saniyə")
    print(f"Token istifadəsi: {result['usage']}")

    print("\n\n=== STREAMING CAVAB (Checkpoint 3) ===")
    print("(mətn hissə-hissə real vaxtda görünəcək)\n")
    streamed_text = client.send_message_stream(
        system_prompt="Sən qısa və dəqiq cavab verən köməkçisən.",
        user_prompt="Süni intellektin 3 əsas faydasını sadala.",
    )
    print(f"\n(Tam yığılmış mətnin uzunluğu: {len(streamed_text)} simvol)")

    print("\n\n=== XƏTA İDARƏETMƏSİ TESTİ (Checkpoint 4) ===")
    print("Səhv token ilə sınaq (401 gözlənilir, retry OLUNMAMALIDIR):")
    try:
        bad_client = HFClient()
        bad_client.api_token = "hf_yanlish_token_test_ucun"
        bad_client.headers["Authorization"] = f"Bearer {bad_client.api_token}"
        bad_client.send_message(user_prompt="test", max_retries=3)
    except PermissionError as e:
        print(f"Gözlənilən nəticə alındı (retry edilmədi): {e}")
    except Exception as e:
        print(f"Fərqli xəta növü alındı: {type(e).__name__}: {e}")
