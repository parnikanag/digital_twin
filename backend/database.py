from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./smarthome.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id           = Column(Integer, primary_key=True, index=True)
    timestamp    = Column(DateTime, default=datetime.utcnow)
    room         = Column(String)
    appliance    = Column(String)
    power_w      = Column(Float)
    temp_c       = Column(Float)
    is_on        = Column(Integer, default=1)
    # Real sensor fields (nullable — only set when real hardware is connected)
    humidity     = Column(Float,   nullable=True)   # DHT22 relative humidity %
    smoke_ppm    = Column(Float,   nullable=True)   # MQ2 raw ADC value (0–4095)
    smoke_alert  = Column(Integer, nullable=True)   # 1 = smoke/gas detected, 0 = clear
    motion       = Column(Integer, nullable=True)   # PIR: 1 = motion, 0 = no motion


class IotEvent(Base):
    """Stores discrete IoT events (smoke detected, motion, etc.) for history."""
    __tablename__ = "iot_events"
    id         = Column(Integer, primary_key=True, index=True)
    timestamp  = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String)   # "smoke", "motion", "clear_smoke", "clear_motion"
    room       = Column(String)
    value      = Column(Float,  nullable=True)
    message    = Column(String, nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
