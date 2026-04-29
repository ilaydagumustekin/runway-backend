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

## 9) Notlar

- `Noise Measurements` endpointinde standart alan adı `noise_level_dba` kullanılır.
- Geriye dönük uyumluluk için `dba` gönderilirse backend bunu kabul eder.
- PostgreSQL desteği korunmuştur. İleride `.env` içinde `DATABASE_URL` PostgreSQL URL ile değiştirilebilir.
