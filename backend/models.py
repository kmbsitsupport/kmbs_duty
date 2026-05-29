from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class TelegramUser(Base):
    __tablename__ = "telegram_users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    person = relationship("Person", back_populates="user", uselist=False)


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    telegram_user_id = Column(Integer, ForeignKey("telegram_users.id"), nullable=True)
    telegram_username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("TelegramUser", back_populates="person")
    schedule_entries = relationship("ScheduleEntry", back_populates="person")
    checklists = relationship("Checklist", back_populates="assigned_to")
    alerts = relationship("Alert", back_populates="person")


class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    date = Column(String, nullable=False)
    time_start = Column(String, nullable=True)
    time_end = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    raw_name = Column(String, nullable=True)
    source_file = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    person = relationship("Person", back_populates="schedule_entries")


class Checklist(Base):
    __tablename__ = "checklists"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    created_by_id = Column(Integer, nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    assigned_to = relationship("Person", back_populates="checklists")
    items = relationship("ChecklistItem", back_populates="checklist", cascade="all, delete-orphan")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(Integer, primary_key=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id"), nullable=False)
    text = Column(String, nullable=False)
    is_done = Column(Boolean, default=False)
    order = Column(Integer, default=0)

    checklist = relationship("Checklist", back_populates="items")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    message = Column(Text, nullable=False)
    send_at = Column(DateTime, nullable=True)
    is_sent = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    repeat_daily = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    person = relationship("Person", back_populates="alerts")
