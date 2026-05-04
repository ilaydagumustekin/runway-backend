# Requirements Status

Bu dokuman, backend tarafinda bugune kadar gelistirilen endpointlere gore 34 gereksinimin durumunu ozetler.

| No | Gereksinim | Backend Durumu | Backend Karşılığı / Endpointler | Not |
| --- | --- | --- | --- | --- |
| 1 | Ana Sayfa | Tamamlandı | `GET /dashboard/home` | Swift ana sayfa icin birlesik veri doner. |
| 2 | Giriş Yap | Tamamlandı | `POST /auth/login`, `POST /auth/login-json` | Swagger ve JSON istemcileri desteklenir. |
| 3 | Kayıt Ol | Tamamlandı | `POST /auth/register` | Standart kullanici kaydi yapilir. |
| 4 | Çıkış Yap | Kısmen Tamamlandı | `POST /auth/logout` | Placeholder response var, token blacklist yok. |
| 5 | Kullanıcı Profili | Tamamlandı | `GET /users/me`, `PATCH /users/me`, `PATCH /users/me/password` | Profil alanlari ve sifre guncelleme desteklenir. |
| 6 | Konum İzni Al | Mobil/iOS Tarafı | - | Izin isteme tamamen istemci tarafindadir. |
| 7 | Mikrofon İzni Al | Mobil/iOS Tarafı | - | Izin isteme tamamen istemci tarafindadir. |
| 8 | Mevcut Konum Tespiti | Kısmen Tamamlandı | `GET /location/nearest-neighborhood`, `GET /location/nearby-neighborhoods` | Backend, istemciden gelen koordinata gore islem yapar; GPS tespiti mobil tarafta. |
| 9 | Mahalle Seçimi | Tamamlandı | `GET /neighborhoods`, `GET /neighborhoods/{neighborhood_id}`, `GET /location/nearest-neighborhood`, `GET /location/nearby-neighborhoods` | Listeleme ve konuma gore secim desteklenir. |
| 10 | Harita Görüntüleme | Kısmen Tamamlandı | `GET /map/neighborhood-markers`, `GET /map/neighborhood-markers/with-scores` | Backend marker verisi saglar; gercek harita cizimi mobil tarafta. |
| 11 | Hava Kalitesi Görüntüleme | Tamamlandı | `GET /environmental-data/{neighborhood_id}`, `GET /statistics/neighborhood/{neighborhood_id}/summary`, `GET /dashboard/home`, `GET /neighborhoods/{neighborhood_id}/details` | AQI ve ilgili hava kalitesi alanlari doner. |
| 12 | Yeşil Alan Oranı Görüntüleme | Tamamlandı | `GET /environmental-data/{neighborhood_id}`, `GET /statistics/neighborhood/{neighborhood_id}/summary`, `GET /dashboard/home`, `GET /neighborhoods/{neighborhood_id}/details` | Yesil alan orani farkli ekranlar icin saglanir. |
| 13 | Gürültü Seviyesi Görüntüleme | Tamamlandı | `GET /environmental-data/{neighborhood_id}`, `GET /statistics/neighborhood/{neighborhood_id}/summary`, `GET /dashboard/home`, `GET /neighborhoods/{neighborhood_id}/details` | Gurultu degeri ve istatistikleri doner. |
| 14 | Mahalle Yaşam Kalitesi Skoru Görüntüleme | Tamamlandı | `GET /myki/{neighborhood_id}`, `GET /statistics/neighborhood/{neighborhood_id}/summary`, `GET /dashboard/home`, `GET /neighborhoods/{neighborhood_id}/details` | MYKI backend tarafinda hesaplaniyor. |
| 15 | Mahalle Detay Sayfası | Tamamlandı | `GET /neighborhoods/{neighborhood_id}/details` | Mahalle, son veri, MYKI, grafik ozeti ve veri kaynaklari tek endpointte doner. |
| 16 | Grafik ve İstatistik Görüntüleme | Tamamlandı | `GET /statistics/neighborhood/{neighborhood_id}/summary`, `GET /statistics/neighborhood/{neighborhood_id}/history`, `GET /statistics/neighborhood/{neighborhood_id}/chart-data` | Grafik ekranlari icin hazir veri saglanir. |
| 17 | Veri Kaynaklarını Görüntüleme | Tamamlandı | `GET /data-sources`, `GET /data-sources/{source_name}` | Statik/mock veri kaynagi listesi ve detaylari vardir. |
| 18 | Yürüyüş Rotası Önerisi Görüntüleme | Tamamlandı | `POST /routes/recommend` | Rota onerisi backend tarafinda doner. |
| 19 | Rota Seçme | Tamamlandı | `POST /navigation/start`, `POST /route-history` | Route history veya direkt rota bilgisiyle navigasyon secimi desteklenir. |
| 20 | Navigasyon Başlatma | Tamamlandı | `POST /navigation/start`, `GET /navigation/current`, `PATCH /navigation/{navigation_session_id}/complete`, `PATCH /navigation/{navigation_session_id}/cancel`, `GET /navigation/history` | Gercek turn-by-turn mobil tarafta, session yonetimi backendde. |
| 21 | Hava Kalitesi Uyarısı Alma | Kısmen Tamamlandı | `GET /notifications`, `POST /admin/notifications`, `app/services/notification_service.py#create_air_quality_alert_if_needed` | Notification modeli ve helper var; otomatik tetikleme tum akislara bagli degil. |
| 22 | Çevresel Bildirim Alma | Tamamlandı | `GET /notifications`, `PATCH /notifications/{notification_id}/read`, `POST /admin/notifications`, `GET /admin/notifications`, `DELETE /admin/notifications/{notification_id}` | Kullaniciya ozel ve genel bildirimler desteklenir. |
| 23 | Favori Mahalle Ekleme | Tamamlandı | `POST /favorites/{neighborhood_id}` | Ayni mahalle tekrar favorilenemez. |
| 24 | Favori Mahalle Silme | Tamamlandı | `DELETE /favorites/{neighborhood_id}` | Favori kaydi silinebilir. |
| 25 | Geçmiş Rotaları Görüntüleme | Tamamlandı | `GET /route-history`, `GET /route-history/{route_history_id}`, `GET /navigation/history` | Rota gecmisi ve navigasyon oturum gecmisi ayri izlenir. |
| 26 | Kullanıcı Geri Bildirimi Gönderme | Tamamlandı | `POST /feedback` | Kullanici feedback kaydi olusturabilir. |
| 27 | Yönetici Girişi | Admin Tarafı | `POST /admin/users/create-admin`, `POST /auth/login`, `POST /auth/login-json` | Ayrica admin rol kontrolu backendde `role="admin"` ile yapilir. |
| 28 | Mahalle Verisi Görüntüleme | Admin Tarafı | `GET /admin/neighborhoods` | Tum mahalle verileri admin endpointiyle listelenir. |
| 29 | Mahalle Verisi Güncelleme | Admin Tarafı | `PATCH /admin/neighborhoods/{neighborhood_id}` | Kismi guncelleme desteklenir. |
| 30 | Hava Kalitesi Verisi Güncelleme | Admin Tarafı | `PATCH /admin/environmental-data/{environmental_data_id}`, `PATCH /admin/environmental-data/{environmental_data_id}/air-quality` | Hava kalitesi alanlari admin tarafinda guncellenebilir. |
| 31 | Gürültü Verisi Güncelleme | Admin Tarafı | `PATCH /admin/environmental-data/{environmental_data_id}`, `PATCH /admin/environmental-data/{environmental_data_id}/noise` | Gurultu alani ayri endpointle desteklenir. |
| 32 | Yeşil Alan Verisi Güncelleme | Admin Tarafı | `PATCH /admin/environmental-data/{environmental_data_id}`, `PATCH /admin/environmental-data/{environmental_data_id}/green-area` | Yesil alan orani ayri endpointle desteklenir. |
| 33 | Rota Verisi Güncelleme | Admin Tarafı | `GET /admin/routes`, `PATCH /admin/route-history/{route_history_id}` | Tum kullanicilarin rota history kayitlari admin tarafinda gorulur ve guncellenir. |
| 34 | Kullanıcı Geri Bildirimlerini Görüntüleme | Admin Tarafı | `GET /admin/feedback`, `PATCH /admin/feedback/{feedback_id}/status` | Geri bildirimleri listeleme ve durum guncelleme admin tarafinda mevcut. |

## Özet

- Kullanici odakli cekirdek backend gereksinimlerinin buyuk kismi tamamlanmis durumda.
- Izin isteme ve gercek harita/navigasyon cizimi gibi konular mobil/iOS tarafinda.
- Admin veri yonetimi ve admin geri bildirim akislarinin backend karsiliklari mevcut.
- Bazi alanlarda placeholder veya MVP seviye uygulamalar bulunuyor: `logout`, mock hava durumu, statik veri kaynaklari, otomatik hava kalitesi uyarisi helper'i gibi.
