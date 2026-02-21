from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import bindparam, inspect as sa_inspect, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from database import SessionLocal
import models

app = FastAPI()


def _sa_model_to_dict(instance: object) -> dict:
    mapper = sa_inspect(instance).mapper
    return {attr.key: getattr(instance, attr.key) for attr in mapper.column_attrs}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "AgriStack Mock API Running"}

@app.get("/agristack/farmer/{farmer_id}")
def get_farmer(farmer_id: str, db: Session = Depends(get_db)):
    try:
        farmer = (
            db.query(models.Farmer)
            .filter(models.Farmer.farmer_id == farmer_id)
            .first()
        )

        if not farmer:
            raise HTTPException(status_code=404, detail="Farmer not found")

        land = (
            db.query(models.LandParcel)
            .filter(models.LandParcel.farmer_id == farmer_id)
            .all()
        )

        parcel_ids = [p.parcel_id for p in land]

        crop_seasons = []
        crop_history = []
        dcs_records = []
        if parcel_ids:
            in_parcels = bindparam("parcel_ids", expanding=True)

            crop_seasons_stmt = (
                text(
                    """
                    SELECT *
                    FROM crop_seasons
                    WHERE parcel_id IN :parcel_ids
                    ORDER BY season_year DESC, created_at DESC
                    """
                )
                .bindparams(in_parcels)
            )
            crop_history_stmt = (
                text(
                    """
                    SELECT *
                    FROM crop_history
                    WHERE parcel_id IN :parcel_ids
                    ORDER BY season_year DESC, created_at DESC
                    """
                )
                .bindparams(in_parcels)
            )
            dcs_stmt = (
                text(
                    """
                    SELECT *
                    FROM digital_crop_survey
                    WHERE parcel_id IN :parcel_ids
                    ORDER BY survey_date DESC, created_at DESC
                    """
                )
                .bindparams(in_parcels)
            )

            crop_seasons = (
                db.execute(crop_seasons_stmt, {"parcel_ids": parcel_ids})
                .mappings()
                .all()
            )
            crop_history = (
                db.execute(crop_history_stmt, {"parcel_ids": parcel_ids})
                .mappings()
                .all()
            )
            dcs_records = (
                db.execute(dcs_stmt, {"parcel_ids": parcel_ids}).mappings().all()
            )

        schemes_stmt = text(
            """
            SELECT
                s.scheme_id,
                s.scheme_name,
                fs.enrollment_status,
                fs.enrollment_date
            FROM farmer_schemes fs
            JOIN schemes s ON s.scheme_id = fs.scheme_id
            WHERE fs.farmer_id = :farmer_id
            ORDER BY s.scheme_name ASC
            """
        )
        schemes = (
            db.execute(schemes_stmt, {"farmer_id": farmer_id}).mappings().all()
        )
    except OperationalError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Database unavailable. Check DATABASE_URL and network. "
                "This Supabase DB host resolves to IPv6 only; you need IPv6 connectivity "
                "or an IPv4-capable endpoint (e.g., Supabase connection pooler host)."
            ),
        )

    return {
        "farmer": _sa_model_to_dict(farmer),
        "land_parcels": [_sa_model_to_dict(p) for p in land],
        "current_seasons": [dict(row) for row in crop_seasons],
        "crop_history": [dict(row) for row in crop_history],
        "schemes": [dict(row) for row in schemes],
        "digital_crop_survey": [dict(row) for row in dcs_records],
    }

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)