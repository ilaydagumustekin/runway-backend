#!/usr/bin/env python3
"""
Tüm environmental_data kayıtlarını siler, mahalleler için OpenAQ fetch ile
gerçek ölçüm satırları biriktirir, ardından ML modelini eğitir.

Gereksinimler: .env içinde OPENAQ_API_KEY (veya OPENAQ_KEY), yeterli istasyon verisi.
Kullanım: python scripts/ml_fill_openaq_train.py [--target 55] [--sleep 0.4]
"""
from __future__ import annotations

import argparse
import sys
import time

from sqlalchemy import delete, func, select

from app.database import SessionLocal
from app.models.environmental_data import EnvironmentalData
from app.models.neighborhood import Neighborhood
from app.services.air_quality_fetch_service import fetch_and_persist_air_quality
from app.services.ml.model_trainer import MIN_TRAINING_RECORDS, train_model_from_db


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target",
        type=int,
        default=MIN_TRAINING_RECORDS + 10,
        help="Toplam AQI dolu satır hedefi (varsayılan eğitim eşiğinden biraz fazla).",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.2,
        help="Tur sonu bekleme (saniye); OpenAQ 429 riskini azaltır.",
    )
    parser.add_argument(
        "--neighborhood-id",
        type=int,
        default=None,
        help="Yalnız bu mahalle için fetch (varsayılan: tüm mahalleler sırayla).",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        deleted = db.execute(delete(EnvironmentalData))
        db.commit()
        print(f"Silinen environmental_data satırı: {deleted.rowcount or 0}")

        if args.neighborhood_id is not None:
            hoods = db.scalars(
                select(Neighborhood).where(Neighborhood.id == args.neighborhood_id)
            ).all()
        else:
            hoods = db.scalars(select(Neighborhood).order_by(Neighborhood.id)).all()

        if not hoods:
            print("Mahalle bulunamadı.", file=sys.stderr)
            return 1

        attempts = 0
        max_attempts = max(200, args.target * 4)

        while attempts < max_attempts:
            cnt = db.scalar(
                select(func.count())
                .select_from(EnvironmentalData)
                .where(EnvironmentalData.aqi.isnot(None))
            )
            if cnt is not None and cnt >= args.target:
                print(f"Hedef AQI satır sayısına ulaşıldı: {cnt}")
                break

            for n in hoods:
                if cnt is not None and cnt >= args.target:
                    break
                res = fetch_and_persist_air_quality(n, db)
                attempts += 1
                status = res.get("status")
                if status == "success":
                    print(f"  [{attempts}] mahalle={n.id} ok (persisted={res.get('persisted_environmental_data_id')})")
                else:
                    print(f"  [{attempts}] mahalle={n.id} -> {status}: {res.get('message', res)}")

            cnt = db.scalar(
                select(func.count())
                .select_from(EnvironmentalData)
                .where(EnvironmentalData.aqi.isnot(None))
            )

            if args.sleep > 0:
                time.sleep(args.sleep)
        else:
            print(
                f"Yeterli veri toplanamadı ({cnt or 0}/{args.target}). "
                "OPENAQ_API_KEY ve istasyon kapsamasını kontrol edin.",
                file=sys.stderr,
            )
            return 1

        result = train_model_from_db(db)
        print("Eğitim:", result)
        if result.get("status") != "success":
            return 1
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
