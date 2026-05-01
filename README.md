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
- `GET /users/me`
- `POST /auth/logout`

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

Email ve şifre doğruysa JWT access token döner. Bilgiler hatalıysa `401` döner.

Örnek request body:

```json
{
  "email": "ada@example.com",
  "password": "strongpass123"
}
```

Örnek response:

```json
{
  "access_token": "your-jwt-token",
  "token_type": "bearer"
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

## 10) Notlar

- `Noise Measurements` endpointinde standart alan adı `noise_level_dba` kullanılır.
- Geriye dönük uyumluluk için `dba` gönderilirse backend bunu kabul eder.
- PostgreSQL desteği korunmuştur. İleride `.env` içinde `DATABASE_URL` PostgreSQL URL ile değiştirilebilir.
- JWT ayarları `.env` üzerinden yönetilir: `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ALGORITHM`.
