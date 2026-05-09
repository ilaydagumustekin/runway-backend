from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
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
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """Tüm mahalleleri sırayla analiz eder. (MOCK/Demo)"""
    neighborhoods = db.query(Neighborhood).limit(10).all()
    results = []
    for n in neighborhoods:
        res = analyze_neighborhood_green_area(n)
        results.append(res)
        
        # In a real app, we should save these to DB here:
        # n.environmental_data.green_area_ratio = res['analysis'].get('green_percentage')
        
    db.commit()
    return {"analyzed_count": len(neighborhoods), "results": results}
