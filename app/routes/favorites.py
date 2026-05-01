from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.favorite_neighborhood import FavoriteNeighborhood
from app.models.neighborhood import Neighborhood
from app.models.user import User
from app.schemas.favorite_neighborhood import FavoriteNeighborhoodResponse
from app.services.auth_service import get_current_active_user

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.post("/{neighborhood_id}", response_model=FavoriteNeighborhoodResponse, status_code=201)
def add_favorite_neighborhood(
    neighborhood_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FavoriteNeighborhood:
    neighborhood = db.get(Neighborhood, neighborhood_id)
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Neighborhood not found.")

    existing_favorite = db.scalar(
        select(FavoriteNeighborhood).where(
            FavoriteNeighborhood.user_id == current_user.id,
            FavoriteNeighborhood.neighborhood_id == neighborhood_id,
        )
    )
    if existing_favorite:
        raise HTTPException(status_code=400, detail="Neighborhood is already in favorites.")

    favorite = FavoriteNeighborhood(user_id=current_user.id, neighborhood_id=neighborhood_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return db.scalar(
        select(FavoriteNeighborhood)
        .options(joinedload(FavoriteNeighborhood.neighborhood))
        .where(FavoriteNeighborhood.id == favorite.id)
    )


@router.get("", response_model=list[FavoriteNeighborhoodResponse])
def list_favorite_neighborhoods(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> list[FavoriteNeighborhood]:
    favorites = db.scalars(
        select(FavoriteNeighborhood)
        .options(joinedload(FavoriteNeighborhood.neighborhood))
        .where(FavoriteNeighborhood.user_id == current_user.id)
        .order_by(FavoriteNeighborhood.created_at.desc())
    ).all()
    return list(favorites)


@router.delete("/{neighborhood_id}")
def remove_favorite_neighborhood(
    neighborhood_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    favorite = db.scalar(
        select(FavoriteNeighborhood).where(
            FavoriteNeighborhood.user_id == current_user.id,
            FavoriteNeighborhood.neighborhood_id == neighborhood_id,
        )
    )
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite neighborhood not found.")

    db.delete(favorite)
    db.commit()
    return {"message": "Favorite neighborhood removed successfully."}
