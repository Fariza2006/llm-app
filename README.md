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
├── .env.example       # Token nümunəsi (real token YOX)
├── .gitignore         # .env faylını repo-dan qoruyur
└── README.md
```
