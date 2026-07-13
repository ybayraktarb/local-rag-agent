# Katkı Sağlama Rehberi (Contributing Guide)

Bu projeye katkıda bulunmak istediğiniz için teşekkür ederiz! Projeyi geliştirmek ve sorunsuz çalışmasını sağlamak için lütfen aşağıdaki yönergeleri takip edin.

## 🐛 Hata Bildirimi (Issue Açma)

Eğer bir hata bulduysanız veya yeni bir özellik öneriniz varsa, lütfen [GitHub Issues](https://github.com/kullanici/repo/issues) sekmesini kullanarak yeni bir konu açın:
- Hatayı açıkça tanımlayın.
- Hatayı yeniden üretme (reproduce) adımlarını ekleyin.
- Beklenen davranış ile gerçekleşen davranışı netleştirin.

## 🚀 Pull Request (PR) Gönderme

Yeni bir katkıda bulunmak istiyorsanız:
1. Bu depoyu kendi hesabınıza fork edin.
2. Anlamlı bir branch adı oluşturun (örn: `feat/yeni-ozellik` veya `fix/hata-duzeltme`).
3. Değişikliklerinizi yapın ve kodun PEP 8 standartlarına uygun olduğundan emin olun.
4. Mevcut birim testleri çalıştırmak için `python -m pytest` komutunu çalıştırın ve tüm testlerin geçtiğini doğrulayın.
5. Değişikliklerinizi fork ettiğiniz repoya commit edip push edin.
6. Bu depoya yönelik net bir Pull Request açın.

## 🎨 Kodlama Standartları

- Python kodlarında **PEP 8** standartlarına uyun.
- Kodunuzu anlaşılır hale getirmek için gerekli yerlerde açıklayıcı docstring ve yorumlar yazın.
- Her yeni özellik veya hata düzeltmesi için uygun birim testleri (unit tests) yazmaya özen gösterin.
