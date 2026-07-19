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
