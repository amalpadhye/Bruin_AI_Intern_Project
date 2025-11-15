"""Database models for ForkU."""
from sqlalchemy import Column, String, Integer, Numeric, ARRAY, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.database import Base
import uuid


class MenuItem(Base):
    """Menu item model with nutrition information."""
    __tablename__ = "menu_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False, index=True)
    calories = Column(Integer)
    serving_size = Column(Text)
    protein_g = Column(Numeric(10, 2))
    fat_g = Column(Numeric(10, 2))
    carbs_g = Column(Numeric(10, 2))
    fiber_g = Column(Numeric(10, 2))
    ingredients = Column(JSONB)  # Array of ingredient strings
    dining_hall = Column(Text, index=True)
    service = Column(Text)  # Breakfast, Lunch, Dinner
    dates_seen = Column(ARRAY(Text))  # Array of dates this item appeared
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Unique constraint: same name, dining hall, and service
    __table_args__ = (
        {'postgresql_partition_by': 'RANGE (created_at)'} if False else {},  # Can enable partitioning later
    )

