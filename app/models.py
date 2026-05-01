from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text, Enum, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base


class Gender(str, enum.Enum):
    M = "M"
    F = "F"
    O = "O"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    VALIDATED = "VALIDATED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class OrderItemStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESULTED = "RESULTED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


class ResultStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_VALIDATION = "PENDING_VALIDATION"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


class EquipmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    SUPERVISOR = "SUPERVISOR"
    TECHNICIAN = "TECHNICIAN"
    RECEPTIONIST = "RECEPTIONIST"


class Urgency(str, enum.Enum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    STAT = "STAT"


# ─── Users ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True)
    hashed_password = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.TECHNICIAN)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    validated_results = relationship("Result", back_populates="validated_by_user")


# ─── Patients ─────────────────────────────────────────────────────────────────

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    document_type = Column(String(10), default="DNI")
    document_number = Column(String(20), unique=True, nullable=False, index=True)
    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    birth_date = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    phone = Column(String(30))
    email = Column(String(150))
    address = Column(String(250))
    city = Column(String(100))
    health_insurance = Column(String(100))
    insurance_number = Column(String(50))
    observations = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    orders = relationship("Order", back_populates="patient")


# ─── Doctors ──────────────────────────────────────────────────────────────────

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    specialty = Column(String(100))
    license_number = Column(String(50), unique=True)
    phone = Column(String(30))
    email = Column(String(150))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    orders = relationship("Order", back_populates="doctor")


# ─── Test Catalog ─────────────────────────────────────────────────────────────

class TestCategory(Base):
    __tablename__ = "test_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text)
    color = Column(String(20), default="#0d6efd")
    is_active = Column(Boolean, default=True)

    tests = relationship("Test", back_populates="category")


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    abbreviation = Column(String(30))
    category_id = Column(Integer, ForeignKey("test_categories.id"), nullable=False)
    method = Column(String(100))
    unit = Column(String(50))
    # Reference ranges (can vary by age/gender, stored as text for flexibility)
    ref_range_male = Column(String(200))
    ref_range_female = Column(String(200))
    ref_min = Column(Float)
    ref_max = Column(Float)
    turnaround_hours = Column(Integer, default=24)
    price = Column(Float, default=0.0)
    requires_fasting = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    observations = Column(Text)

    category = relationship("TestCategory", back_populates="tests")
    order_items = relationship("OrderItem", back_populates="test")


# ─── Equipment / Analyzers ────────────────────────────────────────────────────

class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    model = Column(String(100))
    manufacturer = Column(String(100))
    serial_number = Column(String(100), unique=True)
    equipment_type = Column(String(100))  # Hematología, Bioquímica, etc.
    location = Column(String(100))
    status = Column(Enum(EquipmentStatus), default=EquipmentStatus.ACTIVE)
    last_calibration = Column(Date)
    next_calibration = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    results = relationship("Result", back_populates="equipment")


# ─── Orders ───────────────────────────────────────────────────────────────────

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    urgency = Column(Enum(Urgency), default=Urgency.ROUTINE)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True))
    clinical_info = Column(Text)
    observations = Column(Text)
    total_price = Column(Float, default=0.0)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    patient = relationship("Patient", back_populates="orders")
    doctor = relationship("Doctor", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    created_by = relationship("User", foreign_keys=[created_by_id])


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    status = Column(Enum(OrderItemStatus), default=OrderItemStatus.PENDING)
    notes = Column(Text)

    order = relationship("Order", back_populates="items")
    test = relationship("Test", back_populates="order_items")
    result = relationship("Result", back_populates="order_item", uselist=False)


# ─── Results ──────────────────────────────────────────────────────────────────

class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=False, unique=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    value = Column(String(200))
    numeric_value = Column(Float)
    unit = Column(String(50))
    status = Column(Enum(ResultStatus), default=ResultStatus.DRAFT)
    is_abnormal = Column(Boolean, default=False)
    abnormal_flag = Column(String(10))  # H (high), L (low), C (critical)
    validated_by_id = Column(Integer, ForeignKey("users.id"))
    validated_at = Column(DateTime(timezone=True))
    result_date = Column(DateTime(timezone=True), server_default=func.now())
    observations = Column(Text)

    order_item = relationship("OrderItem", back_populates="result")
    equipment = relationship("Equipment", back_populates="results")
    validated_by_user = relationship("User", back_populates="validated_results")
