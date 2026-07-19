# LLM Əsaslı Tətbiq — Checkpoint 1: API İnteqrasiyası

## Quraşdırma

```bash
pip install anthropic python-dotenv
```

## API açarının konfiqurasiyası

1. `.env.example` faylını kopyalayıb `.env` adlandırın:
   ```bash
   cp .env.example .env
   ```
2. `.env` faylını açıb öz Anthropic API açarınızı yazın:
   ```
   ANTHROPIC_API_KEY=sk-ant-sizin-real-acariniz
   ```
3. **DİQQƏT:** `.env` faylı `.gitignore`-dadır və heç vaxt GitHub-a yüklənmir. Repository-də yalnız `.env.example` (real açar olmadan) saxlanılır.

## İşlətmək

```bash
python claude_client.py
```

## Necə işləyir

`claude_client.py` faylı `ClaudeClient` adlı bir sinif təqdim edir:

- API açarı `os.getenv("ANTHROPIC_API_KEY")` ilə environment variable-dan oxunur — **kodun içində heç yerdə hardcode edilməyib**.
- Açar tapılmadıqda proqram aydın izahlı xəta ilə dayanır (səssiz çökmür).
- `send_message()` metodu:
  - Request-i `messages.create()` vasitəsilə düzgün formalaşdırır (model, max_tokens, temperature, system/user promptlar).
  - Response-dan mətn hissəsini, `stop_reason`-u və `usage` (token) məlumatını ayıraraq strukturlaşdırılmış `dict` şəklində qaytarır.

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
Salam! Mən Claude adlı süni intellekt köməkçisiyəm və sorğularınıza
dəqiq, faydalı cavablar verməyə çalışıram.

=== METADATA ===
Stop reason: end_turn
Token istifadəsi: {'input_tokens': 28, 'output_tokens': 24}
```

**API açarı olmadıqda gözlənilən xəta (real test nəticəsi):**
```
OSError: ANTHROPIC_API_KEY tapılmadı. Zəhmət olmasa layihə kökündə
'.env' faylı yaradın və içinə ANTHROPIC_API_KEY=... əlavə edin
(nümunə üçün .env.example faylına baxın).
```

## Fayl strukturu

```
llm-app/
├── claude_client.py   # Əsas API client (Checkpoint 1)
├── .env.example       # API açarı nümunəsi (real açar YOX)
├── .gitignore         # .env faylını repo-dan qoruyur
└── README.md
```
