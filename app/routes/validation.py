from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.neighborhood import Neighborhood
from app.models.user import User
from app.services.auth_service import get_current_active_user as get_current_user
from app.services.tuik_validation_service import validate_neighborhood_data
from app.services.validation.tuik_data_manager import import_mock_tuik_data
from app.schemas.validation import ValidationSummary

router = APIRouter(prefix="/validation", tags=["Validation"])

def check_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu islem icin admin yetkisi gereklidir."
        )
    return current_user

@router.get("/neighborhood/{neighborhood_id}", response_model=ValidationSummary)
def validate_neighborhood(
    neighborhood_id: int,
    db: Session = Depends(get_db)
):
    """
    Belirtilen mahallenin verilerini TUIK referans verileriyle karsilastirir.
    """
    neighborhood = db.get(Neighborhood, neighborhood_id)
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Mahalle bulunamadi.")
        
    result = validate_neighborhood_data(db, neighborhood)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    return result

@router.post("/admin/import-tuik")
def import_tuik_data(
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """
    (MOCK) TUIK referans verilerini import eder.
    """
    import_mock_tuik_data(db)
    return {"status": "success", "message": "TUIK mock verileri aktarildi."}
