from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from backend.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    impact = Column(Integer, nullable=False, default=5)
    urgency = Column(Integer, nullable=False, default=5)
    energy_required = Column(Integer, nullable=False, default=5)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    app_name = Column(String, nullable=False)
    window_title = Column(String, nullable=False, default="")
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    category = Column(String, nullable=False, default="neutral")
    is_context_switch = Column(Boolean, nullable=False, default=False)


class MobileEntry(Base):
    __tablename__ = "mobile_entries"

    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False, default="telegram")
    entry_type = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    interpreted_text = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False, default="")
    source = Column(String, nullable=False, default="telegram")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class BodyMetric(Base):
    __tablename__ = "body_metrics"

    id = Column(Integer, primary_key=True)
    metric_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False, default="")
    source = Column(String, nullable=False, default="telegram")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class MoodLog(Base):
    __tablename__ = "mood_logs"

    id = Column(Integer, primary_key=True)
    mood = Column(Integer, nullable=True)
    energy = Column(Integer, nullable=True)
    anxiety = Column(Integer, nullable=True)
    source = Column(String, nullable=False, default="telegram")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class TaskEntry(Base):
    __tablename__ = "task_entries"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    entry_type = Column(String, nullable=False, default="task")
    status = Column(String, nullable=False, default="logged")
    source = Column(String, nullable=False, default="telegram")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
