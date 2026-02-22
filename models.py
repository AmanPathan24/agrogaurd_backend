from sqlalchemy import Column, String, Integer, Float, Date, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Farmer(Base):
    __tablename__ = "farmers"
    farmer_id = Column(String, primary_key=True)
    full_name = Column(String)
    gender = Column(String)
    mobile_number = Column(String)
    village = Column(String)
    district = Column(String)
    state = Column(String)
    created_at = Column(DateTime)

class LandParcel(Base):
    __tablename__ = "land_parcels"
    parcel_id = Column(Integer, primary_key=True)
    farmer_id = Column(String)
    area_hectares = Column(Float)
    soil_type = Column(String)
    irrigation_type = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)