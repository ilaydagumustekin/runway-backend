# Runway Backend (FastAPI MVP)

**Yapay Zekâ Destekli Mahalle Yaşam Kalitesi Analizi ve Akıllı Rota Önerisi** projesinin backend MVP uygulamasıdır.

## Proje Amacı

Bu proje, mahalle bazlı çevresel verileri (hava kalitesi, yeşil alan oranı, gürültü seviyesi) toplayıp analiz ederek
**Mahalle Yaşam Kalitesi İndeksi (MYKİ)** üretmeyi ve mobil uygulama için çevresel kalite odaklı rota önerisi sunmayı amaçlar.

## 1) Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Ortam Değişkenleri

`.env.example` dosyasını kopyalayıp `.env` oluşturun:

```bash
cp .env.example .env
```

Varsayılan olarak SQLite kullanılır:

- `DATABASE_URL=sqlite:///./runway.db`
- `CORS_ORIGINS=*`
- `SEED_DEMO_DATA=true`

## 3) Uygulamayı Çalıştırma

```bash
uvicorn app.main:app --reload
```

## 4) Dokümantasyon

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 5) Kullanılan Teknolojiler

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- Uvicorn

## 6) Temel Endpointler

- `GET /`
- `GET /health`
- `GET /neighborhoods`
- `GET /neighborhoods/{neighborhood_id}`
- `POST /environmental-data`
- `GET /environmental-data/{neighborhood_id}`
- `GET /myki/{neighborhood_id}`
- `POST /noise-measurements`
- `POST /routes/recommend`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/login-json`
- `GET /users/me`
- `POST /auth/logout`
- `POST /favorites/{neighborhood_id}`
- `GET /favorites`
- `DELETE /favorites/{neighborhood_id}`
- `POST /route-history`
- `GET /route-history`
- `GET /route-history/{route_history_id}`
- `DELETE /route-history/{route_history_id}`
- `POST /feedback`
- `GET /feedback/my`
- `GET /admin/feedback`
- `PATCH /admin/feedback/{feedback_id}/status`
- `POST /admin/users/create-admin`
- `GET /admin/neighborhoods`
- `PATCH /admin/neighborhoods/{neighborhood_id}`
- `GET /admin/environmental-data`
- `PATCH /admin/environmental-data/{environmental_data_id}`
- `PATCH /admin/environmental-data/{environmental_data_id}/air-quality`
- `PATCH /admin/environmental-data/{environmental_data_id}/noise`
- `PATCH /admin/environmental-data/{environmental_data_id}/green-area`
- `GET /admin/routes`
- `PATCH /admin/route-history/{route_history_id}`
- `GET /notifications`
- `PATCH /notifications/{notification_id}/read`
- `POST /admin/notifications`
- `GET /admin/notifications`
- `DELETE /admin/notifications/{notification_id}`
- `GET /statistics/neighborhood/{neighborhood_id}/summary`
- `GET /statistics/neighborhood/{neighborhood_id}/history`
- `GET /statistics/neighborhood/{neighborhood_id}/chart-data`
- `GET /data-sources`
- `GET /data-sources/{source_name}`
- `GET /neighborhoods/{neighborhood_id}/details`
- `GET /location/nearest-neighborhood`
- `GET /location/nearby-neighborhoods`
- `GET /map/neighborhood-markers`
- `GET /map/neighborhood-markers/with-scores`

## 7) Test Akışı

- `GET /health`
- `GET /neighborhoods`
- `POST /environmental-data`
- `GET /environmental-data/{neighborhood_id}`
- `GET /myki/{neighborhood_id}`
- `POST /noise-measurements`
- `POST /routes/recommend`

## 8) Future Integrations

- Air quality prediction
- Green area analysis
- TÜİK validation

## 9) Auth Endpointleri

Swagger içinde `Auth` ve `Users` tagleri altında aşağıdaki endpointler görünür:

### `POST /auth/register`

Yeni kullanıcı oluşturur. `email` daha önce kayıtlıysa `400` döner.

Örnek request body:

```json
{
  "full_name": "Ada Lovelace",
  "email": "ada@example.com",
  "password": "strongpass123"
}
```

### `POST /auth/login`

Swagger Authorize ile uyumlu giriş endpointidir. `application/x-www-form-urlencoded` formatında
`username` (email olarak yorumlanır) ve `password` bekler.
Bilgiler doğruysa JWT access token döner, hatalıysa `401` döner.

Örnek form alanları:

```text
username=ada@example.com
password=strongpass123
```

Örnek response:

```json
{
  "access_token": "your-jwt-token",
  "token_type": "bearer"
}
```

### `POST /auth/login-json`

JSON body ile giriş için alternatif endpointtir.

Örnek request body:

```json
{
  "email": "ada@example.com",
  "password": "strongpass123"
}
```

### `GET /users/me`

`Authorization: Bearer <token>` header'ı ile giriş yapan kullanıcının bilgisini döner.

Örnek header:

```text
Authorization: Bearer your-jwt-token
```

### `POST /auth/logout`

Şimdilik placeholder response döner:

```json
{
  "message": "Logout successful. Please remove token on client side."
}
```

## 10) Favorites Endpointleri

Swagger içinde `Favorites` tag'i altında aşağıdaki endpointler görünür:

### `POST /favorites/{neighborhood_id}`

Bearer token ile giriş yapan kullanıcının ilgili mahalleyi favorilerine ekler.

- Mahalle yoksa `404`
- Aynı mahalle zaten favorideyse `400`

Örnek:

```text
POST /favorites/1
Authorization: Bearer your-jwt-token
```

### `GET /favorites`

Giriş yapan kullanıcının favori mahallelerini listeler. Favori yoksa boş liste döner.
Response içinde mahalle bilgileri de bulunur: `id`, `name`, `city`, `district`, `latitude`, `longitude`.

Örnek:

```text
GET /favorites
Authorization: Bearer your-jwt-token
```

### `DELETE /favorites/{neighborhood_id}`

Giriş yapan kullanıcının ilgili mahalleyi favorilerinden kaldırır.

- Favori kayıt yoksa `404`

Başarılı response:

```json
{
  "message": "Favorite neighborhood removed successfully."
}
```

## 11) Örnek Akış

1. `POST /auth/register` ile kullanıcı oluştur.
2. `POST /auth/login` veya `POST /auth/login-json` ile token al.
3. `POST /favorites/{neighborhood_id}` ile mahalleyi favorilere ekle.
4. `GET /favorites` ile favori listesini görüntüle.
5. `DELETE /favorites/{neighborhood_id}` ile favoriden kaldır.

## 12) Route History Endpointleri

Swagger içinde `Route History` tag'i altında aşağıdaki endpointler görünür:

### `POST /route-history`

Bearer token ile giriş yapan kullanıcı için rota geçmişi kaydı oluşturur.

Örnek request body:

```json
{
  "route_name": "Daha Temiz ve Sessiz Yaya Rotasi (Mock)",
  "start_latitude": 37.7800,
  "start_longitude": 30.5600,
  "destination_latitude": 37.7700,
  "destination_longitude": 30.5500,
  "estimated_duration_minutes": 18,
  "environmental_score": 84.5
}
```

### `GET /route-history`

Giriş yapan kullanıcının rota geçmişini en yeniden en eskiye doğru listeler. Kayıt yoksa boş liste döner.

### `GET /route-history/{route_history_id}`

Sadece giriş yapan kullanıcının kendi rota geçmişi kaydını döner. Kayıt yoksa veya başka kullanıcıya aitse `404` döner.

### `DELETE /route-history/{route_history_id}`

Sadece giriş yapan kullanıcının kendi rota geçmişi kaydını siler.

Başarılı response:

```json
{
  "message": "Route history deleted successfully."
}
```

## 13) Örnek Route History Akışı

1. `POST /auth/register` ile kullanıcı oluştur.
2. `POST /auth/login` veya `POST /auth/login-json` ile token al.
3. `POST /routes/recommend` ile rota önerisi al.
4. `POST /route-history` ile önerilen rotayı geçmişe kaydet.
5. `GET /route-history` ile geçmiş rotaları listele.
6. `GET /route-history/{route_history_id}` ile tek kaydı görüntüle.
7. `DELETE /route-history/{route_history_id}` ile kaydı sil.

## 14) Feedback Endpointleri

Swagger içinde `Feedback` ve `Admin Feedback` tag'leri altında aşağıdaki endpointler görünür:

### `POST /feedback`

Bearer token ile giriş yapan kullanıcı geri bildirim gönderir. `status` otomatik olarak `new` atanır.

Örnek request body:

```json
{
  "subject": "Rota sonucu beklediğimden yavaştı",
  "message": "Bazı sokaklarda süre tahmini gerçeğe göre uzun kaldı.",
  "rating": 4,
  "category": "suggestion"
}
```

### `GET /feedback/my`

Giriş yapan kullanıcının kendi geri bildirimlerini en yeniden en eskiye doğru listeler. Kayıt yoksa boş liste döner.

### `GET /admin/feedback`

Sadece `role="admin"` olan kullanıcılar erişebilir. Tüm kullanıcıların geri bildirimlerini en yeniden en eskiye doğru listeler.
Admin olmayan kullanıcı erişirse `403` döner.

### `PATCH /admin/feedback/{feedback_id}/status`

Sadece `role="admin"` olan kullanıcılar erişebilir. Belirli bir geri bildirimin durumunu günceller.

Örnek request body:

```json
{
  "status": "reviewed"
}
```

## 15) Örnek Feedback Akışı

1. `POST /auth/register` ile kullanıcı oluştur.
2. `POST /auth/login` veya `POST /auth/login-json` ile token al.
3. `POST /feedback` ile geri bildirim gönder.
4. `GET /feedback/my` ile kendi geri bildirimlerini listele.
5. Admin kullanıcı ile `GET /admin/feedback` üzerinden tüm kayıtları görüntüle.
6. Admin kullanıcı ile `PATCH /admin/feedback/{feedback_id}/status` üzerinden durumu güncelle.

## 16) Admin Users Endpointi

Swagger içinde `Admin Users` tag'i altında aşağıdaki endpoint görünür:

### `POST /admin/users/create-admin`

MVP/test amaçlı admin kullanıcı oluşturur. Yeni kullanıcıyı doğrudan `role="admin"` ile kaydeder.

Örnek request body:

```json
{
  "full_name": "Platform Admin",
  "email": "admin@example.com",
  "password": "strongpass123"
}
```

Önemli güvenlik notu:

- Bu endpoint production ortamında açık bırakılmamalıdır.
- Uygulamada endpoint Swagger'da görünür kalır, ancak varsayılan tasarım gereği sadece `SEED_DEMO_DATA=true` iken çalışır.
- `SEED_DEMO_DATA=false` olduğunda endpoint `403` döner.

## 17) Admin Test Akışı

1. `POST /admin/users/create-admin` ile admin kullanıcı oluştur.
2. `POST /auth/login` veya `POST /auth/login-json` ile admin olarak token al.
3. Normal kullanıcı ile `POST /feedback` üzerinden geri bildirim oluştur.
4. Admin token ile `GET /admin/feedback` çağır.
5. Admin token ile `PATCH /admin/feedback/{feedback_id}/status` çağır.

## 18) Admin Data Endpointleri

Swagger içinde `Admin Data` tag'i altında aşağıdaki endpointler görünür. Tüm endpointler Bearer token ister ve sadece `role="admin"` kullanıcılar erişebilir.

### `GET /admin/neighborhoods`

Tüm mahalle kayıtlarını listeler.

### `PATCH /admin/neighborhoods/{neighborhood_id}`

Mahalle bilgisini kısmi olarak günceller.

Örnek request body:

```json
{
  "name": "Guncel Mahalle",
  "city": "Isparta",
  "district": "Merkez",
  "latitude": 37.7805,
  "longitude": 30.5611,
  "boundary_data": "{\"type\":\"Polygon\"}"
}
```

### `GET /admin/environmental-data`

Tüm environmental data kayıtlarını en yeniden en eskiye listeler.

### `PATCH /admin/environmental-data/{environmental_data_id}`

Environmental data kaydını kısmi olarak günceller.

Örnek request body:

```json
{
  "pm25": 12.0,
  "pm10": 22.0,
  "no2": 18.0,
  "o3": 31.0,
  "aqi": 56.0,
  "green_area_ratio": 47.5,
  "noise_level_dba": 58.0
}
```

### `PATCH /admin/environmental-data/{environmental_data_id}/air-quality`

Sadece hava kalitesi alanlarını günceller.

Örnek request body:

```json
{
  "pm25": 10.0,
  "pm10": 21.0,
  "no2": 16.0,
  "o3": 29.0,
  "aqi": 51.0
}
```

### `PATCH /admin/environmental-data/{environmental_data_id}/noise`

Sadece gürültü alanını günceller.

```json
{
  "noise_level_dba": 54.0
}
```

### `PATCH /admin/environmental-data/{environmental_data_id}/green-area`

Sadece yeşil alan oranını günceller.

```json
{
  "green_area_ratio": 52.0
}
```

### `GET /admin/routes`

Tüm kullanıcıların rota geçmişi kayıtlarını en yeniden en eskiye listeler.

### `PATCH /admin/route-history/{route_history_id}`

Rota geçmişi kaydını kısmi olarak günceller.

Örnek request body:

```json
{
  "route_name": "Guncel Admin Rotasi",
  "estimated_duration_minutes": 17,
  "environmental_score": 88.4
}
```

## 19) Admin Data Test Akışı

1. `POST /admin/users/create-admin` ile admin kullanıcı oluştur.
2. Admin olarak giriş yapıp Bearer token al.
3. `GET /admin/neighborhoods` ile mahalleleri listele.
4. `PATCH /admin/neighborhoods/{neighborhood_id}` ile mahalle güncelle.
5. `GET /admin/environmental-data` ile environmental data kayıtlarını listele.
6. `PATCH /admin/environmental-data/{environmental_data_id}` veya alt endpointlerle veri güncelle.
7. `GET /admin/routes` ile tüm rota geçmişlerini görüntüle.
8. `PATCH /admin/route-history/{route_history_id}` ile rota geçmişini güncelle.

## 20) Notification Endpointleri

Swagger içinde `Notifications` ve `Admin Notifications` tag'leri altında aşağıdaki endpointler görünür:

### `GET /notifications`

Giriş yapan kullanıcıya ait bildirimleri ve `user_id=null` olan genel bildirimleri en yeniden en eskiye doğru listeler.

### `PATCH /notifications/{notification_id}/read`

Kullanıcının kendi bildirimi veya genel bildirimi için `is_read` alanını günceller.

Örnek request body:

```json
{
  "is_read": true
}
```

### `POST /admin/notifications`

Sadece admin kullanıcılar erişebilir. Yeni bildirim oluşturur.

Örnek request body:

```json
{
  "user_id": null,
  "neighborhood_id": 1,
  "title": "Hava Kalitesi Uyarisi",
  "message": "Secili mahallede hava kalitesi sagliksiz seviyeye yaklasti.",
  "notification_type": "air_quality",
  "severity": "high"
}
```

### `GET /admin/notifications`

Tüm bildirimleri en yeniden en eskiye listeler.

### `DELETE /admin/notifications/{notification_id}`

Belirli bir bildirimi siler.

Başarılı response:

```json
{
  "message": "Notification deleted successfully."
}
```

## 21) Otomatik Hava Kalitesi Uyarisi Helper'i

`app/services/notification_service.py` içinde `create_air_quality_alert_if_needed(db, user_id, neighborhood_id, aqi)` helper'i eklidir.

- `aqi < 100` ise bildirim oluşturmaz
- `aqi >= 100` ise `severity="medium"`
- `aqi >= 150` ise `severity="high"`
- `aqi >= 200` ise `severity="critical"`

Bu helper ileride environmental data ekleme veya analiz akışlarına bağlanabilecek şekilde hazırdır.

## 22) Notification Test Akışı

1. `POST /admin/users/create-admin` ile admin kullanıcı oluştur.
2. Normal kullanıcı oluşturup giriş yap.
3. Admin ile `POST /admin/notifications` çağırarak kullanıcıya özel veya genel bildirim oluştur.
4. Normal kullanıcı ile `GET /notifications` çağırarak bildirimleri görüntüle.
5. `PATCH /notifications/{notification_id}/read` ile bildirimi okundu işaretle.
6. Admin ile `GET /admin/notifications` üzerinden tüm bildirimleri görüntüle.
7. Gerekirse `DELETE /admin/notifications/{notification_id}` ile bildirimi sil.

## 23) Statistics Endpointleri

Swagger içinde `Statistics` tag'i altında aşağıdaki endpointler görünür:

### `GET /statistics/neighborhood/{neighborhood_id}/summary`

Verilen mahalle icin son environmental data kaydina gore ozet istatistik dondurur.

### `GET /statistics/neighborhood/{neighborhood_id}/history`

Mahallenin environmental data gecmisini en eskiden en yeniye listeler.

Query parametresi:

```text
limit=20
```

### `GET /statistics/neighborhood/{neighborhood_id}/chart-data`

Mobil grafik ekrani icin hazir seri verisi dondurur.

Ornek response:

```json
{
  "neighborhood_id": 1,
  "labels": ["2026-05-01", "2026-05-02"],
  "aqi": [55, 60],
  "noise_level_dba": [58, 61],
  "green_area_ratio": [32.5, 35.0],
  "myki_score": [66.0, 68.2]
}
```

## 24) Data Sources Endpointleri

Swagger icinde `Data Sources` tag'i altinda asagidaki endpointler gorunur:

### `GET /data-sources`

Projede kullanilan veri kaynaklarini listeler.

### `GET /data-sources/{source_name}`

Belirli veri kaynaginin detayini dondurur.

Desteklenen `source_name` ornekleri:

- `openaq`
- `waqi`
- `airnow`
- `mobile-sensor`
- `google-maps-satellite`
- `vlm`
- `tuik-cip`
- `user-contributed`

## 25) Statistics ve Data Sources Test Akisi

1. `GET /statistics/neighborhood/{neighborhood_id}/summary` ile ozet kart verisini al.
2. `GET /statistics/neighborhood/{neighborhood_id}/history?limit=20` ile zaman serisini al.
3. `GET /statistics/neighborhood/{neighborhood_id}/chart-data` ile mobil grafik verisini al.
4. `GET /data-sources` ile veri kaynaklarini listele.
5. `GET /data-sources/openaq` gibi bir endpoint ile tek kaynak detayini al.

## 26) Neighborhood Details Endpointi

Swagger icinde `Neighborhood Details` tag'i altinda asagidaki endpoint gorunur:

### `GET /neighborhoods/{neighborhood_id}/details`

Mahalle detay sayfasi icin birlesik veri doner. Tek response icinde mahalle bilgisi, son environmental data, MYKI, grafik ozeti ve veri kaynaklari yer alir.

Ornek response yapisi:

```json
{
  "neighborhood": {
    "id": 1,
    "name": "Cunur",
    "city": "Isparta",
    "district": "Merkez",
    "latitude": 37.8344,
    "longitude": 30.5267,
    "boundary_data": null
  },
  "latest_environmental_data": {
    "id": 1,
    "aqi": 55,
    "pm25": 18.5,
    "pm10": 35.2,
    "no2": 22.1,
    "o3": 40.0,
    "green_area_ratio": 32.5,
    "noise_level_dba": 58.0,
    "created_at": "2026-05-02T12:00:00"
  },
  "myki": {
    "score": 66.04,
    "category": "high"
  },
  "chart_summary": {
    "labels": ["2026-05-01"],
    "aqi": [55.0],
    "noise_level_dba": [58.0],
    "green_area_ratio": [32.5],
    "myki_score": [66.04]
  },
  "data_sources": [
    {
      "name": "OpenAQ",
      "type": "air_quality",
      "status": "planned"
    }
  ]
}
```

Not:

- Mahalle bulunamazsa `404` doner.
- Environmental data yoksa `latest_environmental_data` ve `myki` `null` doner.
- Bu durumda `chart_summary` bos diziler ile gelir.

## 27) Neighborhood Details Test Akisi

1. `GET /neighborhoods/{neighborhood_id}/details` ile birlesik mahalle detay verisini al.
2. `GET /statistics/neighborhood/{neighborhood_id}/summary` ile summary sonucu karsilastir.
3. `GET /statistics/neighborhood/{neighborhood_id}/chart-data` ile grafik ozetini karsilastir.
4. `GET /data-sources` ile veri kaynagi listesiyle ayni kaynaklarin dondugunu kontrol et.

## 28) Location ve Map Endpointleri

Swagger icinde `Location` tag'i altinda asagidaki endpointler gorunur:

### `GET /location/nearest-neighborhood`

Verilen latitude/longitude koordinatina en yakin mahalleyi bulur.

Ornek:

```text
GET /location/nearest-neighborhood?latitude=37.78&longitude=30.56
```

### `GET /location/nearby-neighborhoods`

Belirli yaricap icindeki mahalleleri en yakindan uzaga listeler.

Ornek:

```text
GET /location/nearby-neighborhoods?latitude=37.78&longitude=30.56&radius_km=5&limit=10
```

### `GET /map/neighborhood-markers`

Harita markerlari icin tum mahalleleri ozet olarak doner.

### `GET /map/neighborhood-markers/with-scores`

Harita uzerinde renkli skor markerlari icin mahalleleri MYKI ozetiyle doner.
Environmental data olmayan mahallelerde `myki_score` ve `myki_category` `null` gelir.

## 29) Location ve Map Test Akisi

1. `GET /location/nearest-neighborhood?latitude=37.78&longitude=30.56` ile en yakin mahalleyi bul.
2. `GET /location/nearby-neighborhoods?latitude=37.78&longitude=30.56&radius_km=5&limit=10` ile yakin mahalleleri listele.
3. `GET /map/neighborhood-markers` ile tum marker verilerini al.
4. `GET /map/neighborhood-markers/with-scores` ile MYKI ozetli marker verilerini al.

## 30) Notlar

- `Noise Measurements` endpointinde standart alan adı `noise_level_dba` kullanılır.
- Geriye dönük uyumluluk için `dba` gönderilirse backend bunu kabul eder.
- PostgreSQL desteği korunmuştur. İleride `.env` içinde `DATABASE_URL` PostgreSQL URL ile değiştirilebilir.
- JWT ayarları `.env` üzerinden yönetilir: `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ALGORITHM`.
- Swagger Authorize penceresinde `username` alanına email girerek `/auth/login` üzerinden token alınır.
## 16) Notlar

- `Noise Measurements` endpointinde standart alan adı `noise_level_dba` kullanılır.
- Geriye dönük uyumluluk için `dba` gönderilirse backend bunu kabul eder.
- PostgreSQL desteği korunmuştur. İleride `.env` içinde `DATABASE_URL` PostgreSQL URL ile değiştirilebilir.
- JWT ayarları `.env` üzerinden yönetilir: `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ALGORITHM`.
- Swagger Authorize penceresinde `username` alanına email girerek `/auth/login` üzerinden token alınır.
