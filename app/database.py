from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Device(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    wifi_connected = Column(Boolean, default=False)
    last_message_time = Column(DateTime)
    first_seen = Column(DateTime, default=datetime.utcnow)

    # Latest known values
    last_metric_values = Column(
        String)  # Store as JSON string: {"battery": "85.5", "temperature": "24.3", "version": "1.1.0"}

    # Relationship to DeviceLog
    logs = relationship("DeviceLog", back_populates="device", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_device_last_message', 'last_message_time'),
    )


class DeviceLog(Base):
    __tablename__ = 'device_logs'

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    metric_type = Column(String, nullable=False)  # 'battery', 'temperature', or 'version'
    metric_value = Column(String, nullable=False)  # Store all values as strings

    # Relationship to Device
    device = relationship("Device", back_populates="logs")

    __table_args__ = (
        # Composite index for efficient querying of device history
        Index('idx_device_metric_time', 'device_id', 'metric_type', 'timestamp'),
    )


def init_db(db_url='sqlite:///fov_dashboard.db'):
    """Initialize database and return session factory"""
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)