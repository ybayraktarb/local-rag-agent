# Local Belge Asistanı

[Ollama](https://ollama.com/) ve Chroma ile kendi PDF'leriniz üzerinde çalışan, eğitim ve portföy amaçlı yerel bir RAG uygulaması. CLI temel kullanım yoludur; PySide6 masaüstü arayüzü ve SQLCipher audit kaydı isteğe bağlıdır.

![Sentetik belgelerle Local Belge Asistanı ekranı](assets/local-belge-asistani.png)

Masaüstü arayüzünde aranabilir belge çekmecesi, belge ayrıntıları, sayfaya yönlendiren kaynak düğmeleri, yanıt kopyalama, yeni sohbet ve kalıcı açık/koyu tema bulunur. Ayarlar menüsü sistem durumunu; audit etkinse dışa aktarma seçeneğini gösterir.

## Gereksinimler

- Python 3.12 (proje `>=3.12,<3.14` aralığını destekler)
- Yerelde çalışan [Ollama](https://ollama.com/)
- Varsayılan embedding modeli `bge-m3`
- Varsayılan sohbet modeli `qwen2.5:1.5b-instruct`

```bash
ollama pull bge-m3
ollama pull qwen2.5:1.5b-instruct
```

## CLI kurulumu

macOS/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
cp .env.example .env
python -m src.cli.main
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
Copy-Item .env.example .env
python -m src.cli.main
```

PDF dosyalarınızı `docs/` içine kopyalayın. Uygulama yeni dosyaları indeksler, değişen dosyaların eski chunk'larını yenileriyle değiştirir ve silinen dosyaları indeksten kaldırır. `:status`, `:export` ve `:quit` CLI komutlarıdır.

## Masaüstü arayüzü

Aktif sanal ortamda GUI extra'sını kurun:

```bash
python -m pip install -e '.[gui]'
python -m src.ui.main_window
```

Windows PowerShell'de extra ifadesini çift tırnakla da verebilirsiniz: `python -m pip install -e ".[gui]"`.

Kaynak düğmesi PDF'yi varsayılan görüntüleyicide ilgili sayfa fragment'ıyla açmayı dener. Fragment desteği kullanılan PDF görüntüleyicisine bağlıdır. Belge çekmecesinde dosya adına göre arama yapılabilir; bir belge çift tıklanarak açılabilir.

## Yapılandırma

`.env.example` dosyasını `.env` olarak kopyalayın; kod değişikliği gerekmez.

| Değişken | Varsayılan | Açıklama |
|---|---:|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API adresi |
| `CHAT_MODEL` | `qwen2.5:1.5b-instruct` | Yanıt modeli |
| `EMBED_MODEL` | `bge-m3` | Embedding modeli |
| `DOCS_DIR` / `DB_DIR` / `AUDIT_DIR` | `docs` / `db` / `audit` | Veri dizinleri |
| `RETRIEVAL_K` | `3` | Alınacak en yakın chunk sayısı |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `500` / `50` | Chunk ayarları |
| `CONFIDENCE_THRESHOLD` | `0.45` | Minimum cosine benzerliği |
| `CONFIDENCE_HIGH_THRESHOLD` | `0.80` | GUI yüksek güven göstergesi |
| `AUDIT_ENABLED` | `false` | Şifreli sorgu kaydını etkinleştirir |
| `AUDIT_DB_KEY` | boş | Audit açıkken en az 16 karakter olmalı |

Embedding modelini değiştirirseniz mevcut `db/` indeksini yedekleyip kaldırın ve PDF'leri yeniden indeksleyin. Uygulama uyumsuz indeksi sessizce kullanmaz.

## Şifreli audit

```bash
python -m pip install -e '.[audit]'
```

Ardından `.env` içinde `AUDIT_ENABLED=true` ve güçlü, benzersiz bir `AUDIT_DB_KEY` ayarlayın. Audit export'ları soru, yanıt ve kaynak adlarını içerebilir; hassas dosya olarak saklayın. CSV/XLSX hücreleri formül enjeksiyonuna karşı etkisizleştirilir. Audit kapalıyken SQLCipher gerekmez ve arayüzde dışa aktarma gösterilmez.

## Bağımlılıklar

Kurulumun tek kaynak dosyası `pyproject.toml`'dır. Runtime bağımlılıkları ve `gui`, `audit`, `test` extra'ları burada tanımlanır. `requirements.txt`, eski `pip install -r requirements.txt` iş akışları için projeyi yönlendiren ince bir uyumluluk dosyasıdır; bağımsız sürüm listesi değildir.

## Docker ile CLI

Ollama host üzerinde çalışırken:

```bash
docker compose run --rm rag-cli
```

Compose `docs`, `db` ve `audit` dizinlerini kalıcı bağlar. Docker GUI çalıştırma yolu değildir. Linux'ta host Ollama erişimi ortamınıza göre ek yapılandırma gerektirebilir.

## Testler

```bash
python -m pip install -e '.[test,gui]'
python -m pytest
```

Normal test paketi Ollama veya model indirmez. Gerçek servis testi ayrıca `integration` marker'ı ile opt-in tutulur:

```bash
RUN_OLLAMA_INTEGRATION=1 python -m pytest tests/integration
```

GitHub Actions unit testlerini Ubuntu, macOS ve Windows'ta; audit testlerini ayrı bir Ubuntu job'ında çalıştırır. Ollama entegrasyon job'ı manuel `workflow_dispatch` ile başlatılır.

## Güvenlik sınırları

- Yerel modeller ve yerel depolama harici API kullanımını azaltır; tek başına mevzuat uyumluluğu, mutlak çevrimdışılık veya veri sızıntısına karşı garanti sağlamaz.
- `NetworkGuard` uygulama içindeki Python socket bağlantıları için yardımcı bir savunmadır. İşletim sistemi firewall'u, container ağı, erişim kontrolü veya süreç izolasyonunun yerini tutmaz.
- Confidence gate düşük benzerlikli sonuçları reddederek desteklenmeyen yanıt riskini azaltır; hatasız veya “hallucination-free” yanıt garantisi vermez. Kaynakları doğrulayın.
- `<context>` sınırı ve sistem prompt'u dolaylı prompt injection riskini azaltmaya çalışır; eksiksiz izolasyon değildir.
- Gerçek kurum dokümanlarını, audit export'larını, `.env` dosyasını ve model ağırlıklarını Git'e eklemeyin.
- Audit anahtarı kaybolursa kayıtlar kurtarılamaz; açığa çıkarsa anahtarı döndürün ve yeni bir veritabanı oluşturun.

Ayrıntılar ve özel zafiyet bildirim yolu için [SECURITY.md](SECURITY.md) dosyasına bakın.

## Mimari

![Local RAG mimarisi ve güvenlik sınırları](assets/local-rag-agent-arch.png)

`src/loaders` PDF çıkarma, `src/indexing` registry/chunk/index yaşam döngüsü, `src/retrieval` confidence gate ve prompt bağlamı, `src/audit` opsiyonel şifreli kayıt, `src/cli` ve `src/ui` arayüzleri içerir.

## Sorun giderme

- “Yerel dil modeli yanıt üretemedi”: `ollama serve` çalışıyor mu, `OLLAMA_BASE_URL` ve model adları doğru mu kontrol edin.
- “Embedding modeli farklı”: `db/` dizinini yedekleyip temizleyin ve yeniden başlatın.
- SQLCipher bulunamadı: `python -m pip install -e '.[audit]'` kullanın veya audit'i kapalı bırakın.
- PDF indekslenmiyor: dosyanın okunabilir ve metin içeren bir PDF olduğunu doğrulayın; başarısız dosya sonraki açılışta yeniden denenir.
