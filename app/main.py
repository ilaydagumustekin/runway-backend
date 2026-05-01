from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

import app.models
from app.core.config import settings
from app.database import Base, SessionLocal, engine
from app.routes import auth, environmental_data, favorites, myki, neighborhoods, noise_measurements, placeholders, route_history, routes, users
from app.services.seed_service import seed_neighborhoods_if_enabled

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    try:
        Base.metadata.create_all(bind=engine)

        if settings.seed_demo_data:
            db = SessionLocal()
            try:
                seed_neighborhoods_if_enabled(db)
            finally:
                db.close()
    except SQLAlchemyError:
        # Keeps API process alive if DB is not available yet.
        return


@app.get("/", tags=["Default"])
def root() -> dict:
    return {"message": "Runway backend API is running"}


@app.get("/health", tags=["Default"])
def health() -> dict:
    return {"status": "ok"}


app.include_router(neighborhoods.router)
app.include_router(environmental_data.router)
app.include_router(myki.router)
app.include_router(noise_measurements.router)
app.include_router(routes.router)
app.include_router(placeholders.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(favorites.router)
app.include_router(route_history.router)
