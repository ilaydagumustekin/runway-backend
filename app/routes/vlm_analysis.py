from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.environmental_data import EnvironmentalData
from app.models.neighborhood import Neighborhood
from app.models.user import User
from app.services.auth_service import get_current_active_user as get_current_user
from app.services.green_area_analysis_service import analyze_neighborhood_green_area

router = APIRouter(prefix="/admin/vlm", tags=["Admin VLM"])

def check_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu islem icin admin yetkisi gereklidir."
        )
    return current_user


def persist_green_area_ratio(db: Session, neighborhood_id: int, green_percentage: float) -> EnvironmentalData:
    record = db.scalars(
        select(EnvironmentalData)
        .where(EnvironmentalData.neighborhood_id == neighborhood_id)
        .order_by(EnvironmentalData.created_at.desc())
        .limit(1)
    ).first()

    if record:
        record.green_area_ratio = green_percentage
    else:
        record = EnvironmentalData(
            neighborhood_id=neighborhood_id,
            pm25=0.0,
            pm10=0.0,
            no2=0.0,
            o3=0.0,
            aqi=50.0,
            green_area_ratio=green_percentage,
            noise_level_dba=55.0,
        )
        db.add(record)

    return record

@router.post("/analyze-neighborhood/{neighborhood_id}")
def analyze_neighborhood(
    neighborhood_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """
    Belirtilen mahalle için uydu görüntüsünü çekip VLM modeliyle yeşil alan analizi yapar.
    """
    neighborhood = db.get(Neighborhood, neighborhood_id)
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Mahalle bulunamadi.")
        
    result = analyze_neighborhood_green_area(neighborhood)
    return result

@router.post("/batch-analyze")
def batch_analyze(
    neighborhood_id: int | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """Mahalleleri sırayla analiz eder ve yeşil alan sonucunu DB'ye yazar."""
    stmt = select(Neighborhood).order_by(Neighborhood.id).limit(limit)
    if neighborhood_id is not None:
        stmt = select(Neighborhood).where(Neighborhood.id == neighborhood_id)

    neighborhoods = db.scalars(stmt).all()
    results = []
    persisted_count = 0
    for n in neighborhoods:
        res = analyze_neighborhood_green_area(n)
        results.append(res)

        if res.get("status") != "success":
            continue

        green_percentage = res.get("analysis", {}).get("green_percentage")
        if green_percentage is None:
            continue

        persist_green_area_ratio(db, n.id, float(green_percentage))
        persisted_count += 1

    db.commit()
    return {
        "analyzed_count": len(neighborhoods),
        "persisted_count": persisted_count,
        "results": results,
    }
