# Kendi PDF'lerinizle Yerel RAG: Ollama, Chroma ve Python

Bu eğitim reposu, PDF'leri yerelde indeksleyen ve yalnızca alınan bağlamla cevap üretmeye çalışan küçük bir RAG uygulamasıdır. Hedef “hatasız yapay zekâ” iddiası değil; veri akışını görebileceğiniz, değiştirebileceğiniz ve test edebileceğiniz bir referans oluşturmaktır.

## 1. Çalışan bir temel kurun

Python 3.12 ortamını oluşturup `python -m pip install -e .` çalıştırın. Ollama'da `bge-m3` ve `qwen2.5:1.5b-instruct` modellerini indirin, `.env.example` dosyasını `.env` olarak kopyalayın ve `python -m src.cli.main` ile başlayın. Bu akışın kod karşılığı `src/cli/main.py`, ayarların tek kaynağı `src/config/settings.py` dosyasıdır.

## 2. PDF'den güvenli indeks yaşam döngüsüne

`src/loaders/pdf_loader.py` metni sayfa bazında çıkarır ve tabloları Markdown'a dönüştürür. `src/indexing/index_lifecycle.py` yeni, değişmiş ve silinmiş dosyaları işler. Registry yalnızca indeksleme başarılı olunca güncellenir; bozuk PDF sonraki başlangıçta yeniden denenir. Değişen veya silinen kaynakların eski chunk'ları temizlenir. Embedding modeli değişirse `src/indexing/vectorstore_manager.py` eski indeksi sessizce kullanmak yerine yeniden indeksleme ister.

## 3. Retrieval başarısı, model başarısı değildir

`src/retrieval/confidence_gate.py` cosine distance değerini benzerliğe çevirir ve düşük skorlu sonuçları reddeder. Eşiği geçmek yalnızca ilgili bir chunk bulunduğunu söyler. `src/retrieval/retriever_middleware.py` LLM çağrısının başarısını ayrıca `success` alanıyla bildirir; servis hatasında exception ayrıntısını kullanıcıya taşımaz. Prompt içindeki `<context>` sınırı bir savunma katmanıdır, prompt injection'a karşı garanti değildir.

## 4. Audit'i gerçekten opsiyonel tutun

Standart kurulum SQLCipher istemez. `AUDIT_ENABLED=false` iken no-op logger kullanılır. Audit gereken ortam `python -m pip install -e '.[audit]'` ile extra'yı kurar, güçlü bir `AUDIT_DB_KEY` tanımlar ve uygulamayı yeniden başlatır. `src/audit` parametrik kayıt sorguları, şifreli okuma ve CSV/XLSX export sağlar. Export dosyaları hassastır; CSV formül başlangıçları etkisizleştirilse bile erişim kontrolü gerekir.

## 5. İddiaları testlerle sınırlayın

`python -m pytest` Ollama indirmeden unit testleri çalıştırır. CI aynı paketi Windows, macOS ve Linux üzerinde dener; SQLCipher testi desteklenen ayrı job'dadır. Docker, `docker compose run --rm rag-cli` komutuyla CLI için alternatif sunar. GUI'nin desteklenen yolu yerel `python -m src.ui.main_window` komutudur.

Bu yapı harici API bağımlılığını azaltabilir ama sistem firewall'u, kimlik doğrulama, mevzuat değerlendirmesi veya insan doğrulamasının yerini tutmaz. Yerel çalışmak bir mimari tercih; mutlak güvenlik sonucu değildir.
