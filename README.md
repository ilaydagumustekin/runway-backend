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

## 14) Notlar

- `Noise Measurements` endpointinde standart alan adı `noise_level_dba` kullanılır.
- Geriye dönük uyumluluk için `dba` gönderilirse backend bunu kabul eder.
- PostgreSQL desteği korunmuştur. İleride `.env` içinde `DATABASE_URL` PostgreSQL URL ile değiştirilebilir.
- JWT ayarları `.env` üzerinden yönetilir: `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ALGORITHM`.
- Swagger Authorize penceresinde `username` alanına email girerek `/auth/login` üzerinden token alınır.
