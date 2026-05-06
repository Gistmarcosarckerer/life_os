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
    chat_id = Column(String, nullable=False, default="")
    username = Column(String, nullable=False, default="")
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


class RawEntry(Base):
    __tablename__ = "raw_entries"

    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False, default="telegram")
    raw_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False, default="")
    classification = Column(String, nullable=False, default="nota_geral")
    confidence = Column(Float, nullable=False, default=0)
    status = Column(String, nullable=False, default="raw_input")
    extracted_data = Column(Text, nullable=False, default="{}")
    interpreted_text = Column(Text, nullable=False, default="")
    suggestion = Column(Text, nullable=False, default="")
    chat_id = Column(String, nullable=False, default="")
    username = Column(String, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class FinancialProfile(Base):
    __tablename__ = "financial_profile"

    id = Column(Integer, primary_key=True)
    monthly_income = Column(Float, nullable=False, default=0)
    extra_income = Column(Float, nullable=False, default=0)
    payday = Column(Integer, nullable=False, default=1)
    monthly_savings_goal = Column(Float, nullable=False, default=0)
    emergency_reserve_goal = Column(Float, nullable=False, default=0)
    current_emergency_reserve = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class SpendingCategory(Base):
    __tablename__ = "spending_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    monthly_limit = Column(Float, nullable=False, default=0)
    ideal_percent = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    transaction_type = Column(String, nullable=False, default="expense")
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False, default="")
    category = Column(String, nullable=False, default="outros")
    source = Column(String, nullable=False, default="dashboard")
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    goal_type = Column(String, nullable=False, default="monthly_savings")
    target_amount = Column(Float, nullable=False, default=0)
    current_amount = Column(Float, nullable=False, default=0)
    category = Column(String, nullable=False, default="")
    deadline = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class PurchaseIntention(Base):
    __tablename__ = "purchase_intentions"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    priority = Column(Integer, nullable=False, default=5)
    payment_type = Column(String, nullable=False, default="cash")
    installments = Column(Integer, nullable=False, default=1)
    decision = Column(String, nullable=False, default="attention")
    justification = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class MonthlyFinancialSummary(Base):
    __tablename__ = "monthly_financial_summary"

    id = Column(Integer, primary_key=True)
    month = Column(String, nullable=False)
    income = Column(Float, nullable=False, default=0)
    expenses = Column(Float, nullable=False, default=0)
    projected_balance = Column(Float, nullable=False, default=0)
    estimated_savings = Column(Float, nullable=False, default=0)
    risk_level = Column(String, nullable=False, default="normal")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
