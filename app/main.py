from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import app.models
from app.core.config import settings
from app.database import Base, SessionLocal, engine
from app.routes import admin_data, admin_users, auth, dashboard, environmental_data, feedback, favorites, location, myki, navigation, neighborhood_details, neighborhoods, noise_measurements, notifications, placeholders, route_history, routes, statistics, users
from app.services.seed_service import seed_neighborhoods_if_enabled

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_user_profile_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    expected_columns = {
        "phone_number": "ALTER TABLE users ADD COLUMN phone_number VARCHAR(30)",
        "profile_image_url": "ALTER TABLE users ADD COLUMN profile_image_url VARCHAR(500)",
        "preferred_city": "ALTER TABLE users ADD COLUMN preferred_city VARCHAR(80)",
        "preferred_district": "ALTER TABLE users ADD COLUMN preferred_district VARCHAR(80)",
    }

    with engine.begin() as connection:
        existing_tables = connection.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        ).fetchall()
        if not existing_tables:
            return

        rows = connection.execute(text("PRAGMA table_info(users)")).fetchall()
        existing_columns = {row[1] for row in rows}

        for column_name, alter_sql in expected_columns.items():
            if column_name not in existing_columns:
                connection.execute(text(alter_sql))


@app.on_event("startup")
def on_startup() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        ensure_user_profile_columns()

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
app.include_router(neighborhood_details.router)
app.include_router(environmental_data.router)
app.include_router(myki.router)
app.include_router(noise_measurements.router)
app.include_router(routes.router)
app.include_router(placeholders.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(favorites.router)
app.include_router(route_history.router)
app.include_router(navigation.router)
app.include_router(dashboard.router)
app.include_router(feedback.feedback_router)
app.include_router(feedback.admin_feedback_router)
app.include_router(admin_users.router)
app.include_router(admin_data.router)
app.include_router(notifications.notifications_router)
app.include_router(notifications.admin_notifications_router)
app.include_router(statistics.statistics_router)
app.include_router(statistics.data_sources_router)
app.include_router(location.router)
