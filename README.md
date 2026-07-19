# LLM Əsaslı Tətbiq — Checkpoint 1: API İnteqrasiyası

> Bu versiya **Hugging Face Inference API**-dan istifadə edir (pulsuz, kredit kartı tələb etmir).

## Quraşdırma

```bash
pip install requests python-dotenv
```

## API açarının (token) konfiqurasiyası

1. https://huggingface.co/join ünvanında pulsuz hesab yaradın (kart lazım deyil)
2. https://huggingface.co/settings/tokens ünvanından "Create new token" ilə token yaradın (Read icazəsi kifayətdir)
3. `.env.example` faylını kopyalayıb `.env` adlandırın:
   ```bash
   cp .env.example .env
   ```
4. `.env` faylını açıb öz Hugging Face tokeninizi yazın:
   ```
   HF_API_TOKEN=hf_sizin-real-tokeniniz
   ```
5. **DİQQƏT:** `.env` faylı `.gitignore`-dadır və heç vaxt GitHub-a yüklənmir. Repository-də yalnız `.env.example` (real token olmadan) saxlanılır.

## İşlətmək

```bash
python hf_client.py
```

## Necə işləyir

`hf_client.py` faylı `HFClient` adlı bir sinif təqdim edir:

- API tokeni `os.getenv("HF_API_TOKEN")` ilə environment variable-dan oxunur — **kodun içində heç yerdə hardcode edilməyib**.
- Token tapılmadıqda proqram aydın izahlı xəta ilə dayanır (səssiz çökmür).
- `send_message()` metodu:
  - Request-i Hugging Face Inference API-nin `/models/{model}` endpoint-inə düzgün formalaşdırır (prompt, max_new_tokens, temperature).
  - Response-un status kodunu yoxlayır, xəta halında aydın mesaj verir.
  - Cavabdan mətn hissəsini ayıraraq strukturlaşdırılmış `dict` şəklində qaytarır (mətn, model adı, cavab müddəti).

## Nümunə sorğu/cavab logu

**Sorğu (system + user prompt):**
```
system: "Sən qısa və dəqiq cavab verən köməkçisən."
user:   "Salam! Bu sadəcə API inteqrasiyasını yoxlamaq üçün test sorğusudur.
         Bir cümləylə özünü tanıt."
```

**Cavab (nümunə format):**
```
=== CAVAB ===
Salam! Mən açıq mənbəli süni intellekt köməkçisiyəm və sorğularınıza
qısa, dəqiq cavablar verməyə çalışıram.

=== METADATA ===
Model: HuggingFaceH4/zephyr-7b-beta
Cavab müddəti: 2.14 saniyə
```

**Token olmadıqda gözlənilən xəta (real test nəticəsi):**
```
OSError: HF_API_TOKEN tapılmadı. Zəhmət olmasa layihə kökündə '.env' faylı
yaradın və içinə HF_API_TOKEN=... əlavə edin. Pulsuz token almaq üçün:
https://huggingface.co/settings/tokens
```

## Fayl strukturu

```
llm-app/
├── hf_client.py       # Əsas API client (Checkpoint 1)
├── support_agent.py   # Prompt engineering - müştəri dəstəyi (Checkpoint 2)
├── .env.example       # Token nümunəsi (real token YOX)
├── .gitignore         # .env faylını repo-dan qoruyur
└── README.md
```

---

# Checkpoint 2: Prompt Engineering

`support_agent.py` faylı müştəri dəstəyi cavab generatoru üçün strukturlaşdırılmış prompt sistemini təqdim edir.

## Struktur

1. **System prompt** (dəyişməz hissə) — modelin rolunu, tonunu və sərt qaydalarını təyin edir:
   - Nəzakətli/empatik olmaq
   - Cavabın qısa olması (max 4-5 cümlə)
   - Yalan məlumat uydurmamaq
   - Mürəkkəb məsələləri insan operatora yönləndirmək
   - Həmişə Azərbaycan dilində cavab vermək

2. **Few-shot nümunələr** — modelə 3 real ssenari və "yaxşı cavab" nümunəsi göstərilir ki, model formatı və tonu təqlid etsin.

3. **User prompt** (dinamik hissə) — hər sorğuda dəyişir: few-shot nümunələri + (əgər varsa) sifariş konteksti + real müştəri mesajı.

## İşlətmək

```bash
python support_agent.py
```

## Nümunə sorğu/cavab logu

**Sorğu:**
```
Müştəri: Sifariş #4521 hələ də çatmayıb, izləmə linki də işləmir.
Kontekst: Sifariş #4521, 6 gün əvvəl verilib, kuryer şirkəti: Bravo Kuryer.
```

**Cavab (nümunə format):**
```
Köməkçi: Narahatçılığınızı tam başa düşürəm, 6 gün gecikmə həqiqətən
narahatedicidir. Sifariş #4521-i Bravo Kuryer ilə yoxlayıram və sizə
tezliklə dəqiq status barədə məlumat verəcəm. Əgər izləmə linki
işləməyə davam edərsə, bu barədə də operatorumuza bildirəcəm.
```

## Niyə belə qurulub

- System prompt-un ayrılması modelin davranışını **sabit** saxlayır (hər sorğuda təkrarlanmır).
- Few-shot nümunələr modelin cavab formatını, uzunluğunu və tonunu **öngörülən** edir — xüsusilə kiçik/açıq modellərdə bu, keyfiyyəti xeyli artırır.
- `temperature=0.4` seçilib ki, dəstək cavabları həddindən artıq "yaradıcı" olmasın, sabit və peşəkar qalsın.

## Test zamanı aşkarlanan məhdudiyyət (iteration qeydi)

İlk versiyada model bəzən prompt formatını təkrarlayırdı (özü "Müştəri:" sətrini yazırdı). Bunu `build_user_prompt`-a aydın təlimat ("YALNIZ köməkçinin sözlərini yaz") əlavə edərək və `_clean_response()` post-processing funksiyası ilə həll etdik.

Qalan kiçik məhdudiyyət: kiçik open-source model (Llama-3.1-8B) bəzən fərqli mövzulu sorğularda (məsələn rəng problemi) ilk few-shot nümunənin sözlərini ("gecikmə", "sifariş statusu") səhvən köçürür. Bu, real API-lərlə edge-case testinin nümunəsidir — production mühitdə bu, daha güclü model (məs. GPT-4/Claude) və ya daha ciddi output-validasiyası ilə azaldıla bilər.

---

# Checkpoint 3: Streaming Cavab İdarəetməsi

`hf_client.py`-dəki `send_message_stream()` metodu Hugging Face router API-sindən **real vaxtda, hissə-hissə (token-token)** cavab almağı təmin edir.

## Necə işləyir

- Request-ə `"stream": true` parametri əlavə olunur.
- API cavabı **Server-Sent Events (SSE)** formatında qaytarır — hər sətir `data: {...}` şəklində gəlir, sonda `data: [DONE]` göndərilir.
- Kod `response.iter_lines()` ilə axını sətir-sətir oxuyur, hər JSON parça (`chunk`) daxilindəki `delta.content` hissəsini çıxarır və dərhal ekrana yazır (və ya verilmiş `on_chunk` callback-inə ötürür).
- Korlanmış/natamam JSON chunk-lar səssizcə keçilir (kod çökmür).
- Stream bitdikdən sonra tam yığılmış mətn `str` kimi qaytarılır.

## İşlətmək

```bash
python hf_client.py
```

Konsolda mətnin hərf-hərf/söz-söz canlı şəkildə yazıldığını görəcəksiniz (ChatGPT/Claude interfeysindəki kimi).

## Nümunə istifadə (öz kodunda)

```python
from hf_client import HFClient

client = HFClient()

# Standart: mətn birbaşa terminala yazılır
client.send_message_stream(user_prompt="Bakı haqqında qısa məlumat ver.")

# Öz callback-inlə (məsələn, veb interfeysdə hər hissəni UI-ə göndərmək üçün)
def my_callback(chunk: str):
    # burada chunk-ı UI-ə, WebSocket-ə və s. göndərmək olar
    print(f"[YENİ HİSSƏ]: {chunk}")

full_text = client.send_message_stream(
    user_prompt="Bakı haqqında qısa məlumat ver.",
    on_chunk=my_callback,
)
```

---

# Checkpoint 4: Xəta İdarəetməsi

`send_message()` metodu indi xətaları **iki kateqoriyaya** bölür və fərqli davranır:

## 1. Qalıcı xətalar (retry OLUNMUR — dərhal bildirilir)
- **401 (etibarsız token)** → `PermissionError` — retry etmək faydasızdır, çünki token dəyişmədikcə nəticə eyni olacaq.
- **400 (səhv sorğu formatı)** → `ValueError` — sorğunun özündə problem var, təkrar göndərmək kömək etməz.

## 2. Müvəqqəti xətalar (avtomatik RETRY olunur, exponential backoff ilə)
- **429 (rate limit — həddindən çox sorğu)**
- **500 / 502 / 503 / 504 (server tərəfli müvəqqəti xətalar)**
- **Timeout (vaxt aşımı)** və **ConnectionError (şəbəkə kəsilməsi)**

Bu hallarda kod avtomatik olaraq **3 dəfəyə qədər** yenidən cəhd edir, hər cəhd arasında gözləmə vaxtını ikiqat artırır (**exponential backoff**: 2s → 4s → 8s). 3 cəhddən sonra da uğursuz olarsa, aydın xəta mesajı ilə dayanır.

## Nümunə davranış

```python
from hf_client import HFClient

client = HFClient()

try:
    result = client.send_message(user_prompt="Salam!", max_retries=3)
    print(result["text"])
except PermissionError as e:
    print(f"Token problemi: {e}")  # istifadəçiyə .env-i yoxlamağı təklif et
except ValueError as e:
    print(f"Sorğu formatı səhvdir: {e}")
except RuntimeError as e:
    print(f"API uzun müddət cavab vermədi: {e}")  # bütün retry-lar bitdi
```

## Test nəticəsi (real, səhv token ilə)

```
=== XƏTA İDARƏETMƏSİ TESTİ (Checkpoint 4) ===
Səhv token ilə sınaq (401 gözlənilir, retry OLUNMAMALIDIR):
Gözlənilən nəticə alındı (retry edilmədi): API tokeni etibarsızdır və ya
vaxtı bitib (401). Zəhmət olmasa .env faylındakı HF_API_TOKEN-i yoxlayın.
```

Bu test göstərir ki, sistem 401 xətasında **dərhal** dayanır (3 dəfə boş yerə cəhd etmir), lakin 429/500 kimi müvəqqəti xətalarda avtomatik retry edəcək.

---

# Checkpoint 5: Çıxış Parsing/Validasiyası

`structured_output.py` modeldən **JSON formatında** strukturlaşdırılmış cavab alır və modelin "həmişə təmiz JSON qaytaracağını" **fərz etmir** — əksinə, format pozuntularını tutub düzəltməyə çalışır.

## Model bəzən nə edir (real problem)

- JSON-un ətrafına izah əlavə edir: `Əlbəttə, budur JSON: {...} Ümid edirəm kömək etdi!`
- Markdown code-block işarəsi qoyur: ` ```json\n{...}\n``` `
- Format tam pozula bilər (mötərizə bağlanmır, JSON heç yaranmır və s.)

## Necə həll olunub

1. **`_extract_json_candidate()`** — mətndən markdown işarələrini təmizləyir, sonra ilk `{` və son `}` arasındakı hissəni çıxarır (izahedici mətni ata bilir).
2. **`_try_parse_json()`** — çıxarılan hissəni `json.loads()` ilə parse etməyə çalışır, uğursuz olarsa xəta atmadan `None` qaytarır.
3. **`get_structured_response()`** — əgər parse uğursuz olarsa, ya da tələb olunan açarlar (`required_keys`) əskikdirsə, modelə **aydın düzəliş təlimatı ilə yenidən sorğu göndərir** (max 3 cəhd). Bütün cəhdlər uğursuz olarsa, `StructuredOutputError` aydın mesajla atılır.

## İşlətmək

```bash
python structured_output.py
```

## Test nəticəsi (şəbəkəsiz, yalnız parsing məntiqi)

```
Test 1: OK -> {'title': 'Test', 'summary': 'Qisa', 'keywords': ['a', 'b']}   # təmiz JSON
Test 2: OK -> {'title': 'Test', 'summary': 'Qisa', 'keywords': ['a']}         # JSON + izahedici mətn
Test 3: OK -> {'title': 'Test', 'summary': 'Qisa', 'keywords': []}            # markdown ```json``` bloku
Test 4: FAILED (gözlənilən) -> None                                           # həqiqətən korlanmış JSON
```

Bu, tapşırıqda tələb olunan **edge-case testini** dəqiq göstərir: model "izahedici mətn" və ya "format pozuntusu" versə belə, kod bunu tutur və düzgün işləyir; yalnız həqiqətən bərpa olunmaz JSON-da (test 4) aydın xəta ilə dayanır.

## Nümunə istifadə

```python
from structured_output import summarize_text_structured

result = summarize_text_structured("Uzun mətn burada...")
print(result["title"])      # str
print(result["summary"])    # str
print(result["keywords"])   # list[str]
```
