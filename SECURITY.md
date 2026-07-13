# Güvenlik Politikası (Security Policy)

## Offline Çalışma İlkesi

Bu uygulama, bankacılık ve finans sektörü uyum gereksinimleri (BDDK vb.) göz önünde bulundurularak **%100 yerel (offline)** çalışacak şekilde tasarlanmıştır. 

### Veri Gizliliği Güvenceleri:

1. **Ağ Bağlantısı Kısıtlamaları**: Sistem dış sunucularla hiçbir şekilde veri alışverişi yapmaz. Ollama bağlantısı sadece `localhost` üzerinden sağlanır.
2. **Kriptografik Audit Günlükleri**: Kullanıcı sorguları ve sistem yanıtları, SQLCipher kullanılarak yerel olarak şifrelenmiş SQLite veritabanında saklanır. Şifreleme anahtarı çevre değişkenlerinde tanımlanır ve diskte açık metin olarak barındırılmaz.
3. **PDF ve Veri Koruması**: Kurumsal PDF dokümanları veya hassas veriler hiçbir koşulda Git reposuna commit edilmez. Repoda sadece örnek veri/yapılandırmalar barındırılır.

## Bildirimler ve Zafiyet Yönetimi

Uygulamanın offline bütünlüğünü riske atabilecek durumlar için lütfen sistem yöneticiniz ile iletişime geçiniz.
