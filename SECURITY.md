# Güvenlik politikası

Bu eğitim projesi yerel model ve yerel depolama kullanacak şekilde yapılandırılabilir. Bu mimari tek başına BDDK/MASAK veya başka bir mevzuata uyumluluk, mutlak çevrimdışılık ya da veri gizliliği garantisi değildir. Üretim kullanımı için tehdit modeli, erişim kontrolleri, işletim sistemi firewall'u, yedekleme ve kurum politikaları ayrıca değerlendirilmelidir.

## Hassas veri

- Gerçek PDF, `.env`, audit veritabanı/export'u, model ağırlığı ve kişisel/kurumsal veri commit edilmemelidir.
- Audit varsayılan olarak kapalıdır. Açıldığında SQLCipher kullanır ve anahtar yalnızca çalışma zamanı ortamından alınır. `.env` dosyasının kendisi açık metindir; uygun dosya izinleri ve bir secret manager tercih edin.
- Audit export'u soru, cevap ve kaynak adlarını içerir. Hassas veri olarak sınıflandırın.
- NetworkGuard yalnızca Python socket katmanında yardımcı kontroldür; sistem veya container ağ izolasyonu değildir.

## Zafiyet bildirimi

Hassas ayrıntıları herkese açık issue içinde paylaşmayın. Repository sahibine özel kanaldan etki, yeniden üretim adımları ve önerilen düzeltmeyle bildirin. Açığa çıkmış bir anahtarı koddan silmek yeterli değildir; anahtarı döndürün ve gerekiyorsa Git geçmişini koordineli biçimde temizleyin.
