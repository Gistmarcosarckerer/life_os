import calendar
from collections import defaultdict
from datetime import datetime

from backend.models import (
    FinancialGoal,
    FinancialProfile,
    PurchaseIntention,
    SpendingCategory,
    Transaction,
)


DEFAULT_CATEGORIES = [
    ("alimentacao", 0, 12),
    ("transporte", 0, 8),
    ("carro", 0, 12),
    ("lazer", 0, 8),
    ("saude", 0, 8),
    ("mercado", 0, 18),
    ("assinatura", 0, 5),
    ("divida/parcela", 0, 15),
    ("investimento", 0, 15),
    ("outros", 0, 10),
]

CATEGORY_KEYWORDS = {
    "alimentacao": ["almoco", "jantar", "lanche", "cafe", "ifood", "restaurante", "pizza"],
    "transporte": ["uber", "99", "onibus", "metro", "taxi", "combustivel", "gasolina"],
    "carro": ["carro", "mecanico", "seguro", "ipva", "pneu", "oficina", "estacionamento"],
    "lazer": ["cinema", "bar", "show", "viagem", "jogo", "lazer", "festa"],
    "saude": ["farmacia", "remedio", "medico", "consulta", "exame", "dentista"],
    "mercado": ["mercado", "supermercado", "compras", "hortifruti", "feira"],
    "assinatura": ["netflix", "spotify", "prime", "assinatura", "icloud", "google", "plano"],
    "divida/parcela": ["parcela", "emprestimo", "financiamento", "cartao", "boleto", "divida"],
    "investimento": ["investimento", "tesouro", "acao", "reserva", "cdb", "cripto"],
}


def seed_financial_defaults(session):
    existing_profile = session.query(FinancialProfile).first()
    if existing_profile is None:
        session.add(FinancialProfile(payday=1))

    existing_names = {
        category.name for category in session.query(SpendingCategory).all()
    }
    for name, monthly_limit, ideal_percent in DEFAULT_CATEGORIES:
        if name not in existing_names:
            session.add(
                SpendingCategory(
                    name=name,
                    monthly_limit=monthly_limit,
                    ideal_percent=ideal_percent,
                )
            )


def get_or_create_profile(session) -> FinancialProfile:
    profile = session.query(FinancialProfile).first()
    if profile is None:
        profile = FinancialProfile(payday=1)
        session.add(profile)
        session.flush()
        session.refresh(profile)
    return profile


def update_financial_profile(session, data: dict) -> FinancialProfile:
    profile = get_or_create_profile(session)
    profile.monthly_income = money_value(data.get("monthly_income", profile.monthly_income))
    profile.extra_income = money_value(data.get("extra_income", profile.extra_income))
    profile.payday = bounded_int(data.get("payday", profile.payday), "payday", 1, 31)
    profile.monthly_savings_goal = money_value(
        data.get("monthly_savings_goal", profile.monthly_savings_goal)
    )
    profile.emergency_reserve_goal = money_value(
        data.get("emergency_reserve_goal", profile.emergency_reserve_goal)
    )
    profile.current_emergency_reserve = money_value(
        data.get("current_emergency_reserve", profile.current_emergency_reserve)
    )
    profile.updated_at = datetime.utcnow()
    session.flush()
    session.refresh(profile)
    return profile


def serialize_profile(profile: FinancialProfile) -> dict:
    return {
        "id": profile.id,
        "monthly_income": round(profile.monthly_income, 2),
        "extra_income": round(profile.extra_income, 2),
        "payday": profile.payday,
        "monthly_savings_goal": round(profile.monthly_savings_goal, 2),
        "emergency_reserve_goal": round(profile.emergency_reserve_goal, 2),
        "current_emergency_reserve": round(profile.current_emergency_reserve, 2),
    }


def create_transaction(
    session,
    amount: float,
    description: str,
    transaction_type: str = "expense",
    category: str | None = None,
    source: str = "dashboard",
    occurred_at: datetime | None = None,
) -> Transaction:
    transaction_type = normalize_transaction_type(transaction_type)
    category = category or categorize_transaction(description, transaction_type)
    transaction = Transaction(
        transaction_type=transaction_type,
        amount=money_value(amount),
        description=(description or "").strip(),
        category=category,
        source=source,
        occurred_at=occurred_at or datetime.utcnow(),
    )
    session.add(transaction)
    session.flush()
    session.refresh(transaction)
    return transaction


def serialize_transaction(transaction: Transaction) -> dict:
    return {
        "id": transaction.id,
        "transaction_type": transaction.transaction_type,
        "amount": round(transaction.amount, 2),
        "description": transaction.description,
        "category": transaction.category,
        "source": transaction.source,
        "occurred_at": transaction.occurred_at.isoformat()
        if transaction.occurred_at
        else None,
    }


def list_transactions(session, limit: int = 30) -> list[dict]:
    transactions = (
        session.query(Transaction)
        .order_by(Transaction.occurred_at.desc())
        .limit(limit)
        .all()
    )
    return [serialize_transaction(transaction) for transaction in transactions]


def get_financial_summary(session, reference_date: datetime | None = None) -> dict:
    now = reference_date or datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    _, days_in_month = calendar.monthrange(now.year, now.month)
    remaining_days = max(days_in_month - now.day, 0)

    profile = get_or_create_profile(session)
    transactions = (
        session.query(Transaction)
        .filter(Transaction.occurred_at >= month_start)
        .all()
    )

    transaction_income = sum(
        item.amount for item in transactions if item.transaction_type == "income"
    )
    total_expenses = sum(
        item.amount for item in transactions if item.transaction_type == "expense"
    )
    configured_income = profile.monthly_income + profile.extra_income
    total_income = configured_income + transaction_income
    projected_balance = total_income - total_expenses
    estimated_savings = projected_balance
    income_spent_percent = (total_expenses / total_income * 100) if total_income > 0 else 0
    average_daily_spend = total_expenses / max(now.day, 1)
    target_savings = profile.monthly_savings_goal
    daily_limit = max((total_income - total_expenses - target_savings) / max(remaining_days, 1), 0)

    by_category = summarize_by_category(transactions)
    alerts = build_financial_alerts(
        profile=profile,
        total_income=total_income,
        total_expenses=total_expenses,
        projected_balance=projected_balance,
        spent_percent=income_spent_percent,
        remaining_days=remaining_days,
        daily_limit=daily_limit,
        by_category=by_category,
    )
    risk_level = calculate_risk_level(income_spent_percent, projected_balance, daily_limit)
    health_score = calculate_health_score(
        spent_percent=income_spent_percent,
        projected_balance=projected_balance,
        total_income=total_income,
        target_savings=target_savings,
    )

    return {
        "profile": serialize_profile(profile),
        "month": now.strftime("%Y-%m"),
        "days_remaining": remaining_days,
        "income": round(total_income, 2),
        "configured_income": round(configured_income, 2),
        "transaction_income": round(transaction_income, 2),
        "total_expenses": round(total_expenses, 2),
        "projected_balance": round(projected_balance, 2),
        "estimated_savings": round(estimated_savings, 2),
        "income_spent_percent": round(income_spent_percent, 1),
        "average_daily_spend": round(average_daily_spend, 2),
        "recommended_daily_limit": round(daily_limit, 2),
        "health_score": health_score,
        "risk_level": risk_level,
        "alerts": alerts,
        "by_category": by_category,
        "recommendation": build_daily_financial_recommendation(
            risk_level,
            projected_balance,
            daily_limit,
            alerts,
        ),
    }


def summarize_by_category(transactions: list[Transaction]) -> list[dict]:
    totals = defaultdict(float)
    for item in transactions:
        if item.transaction_type == "expense":
            totals[item.category] += item.amount
    return [
        {"category": category, "amount": round(amount, 2)}
        for category, amount in sorted(totals.items(), key=lambda row: row[1], reverse=True)
    ]


def build_financial_alerts(
    profile: FinancialProfile,
    total_income: float,
    total_expenses: float,
    projected_balance: float,
    spent_percent: float,
    remaining_days: int,
    daily_limit: float,
    by_category: list[dict],
) -> list[str]:
    alerts = []
    if total_income <= 0:
        alerts.append("Configure sua renda mensal para o LIFE OS calcular limites reais.")
        return alerts

    if spent_percent >= 70 and remaining_days > 0:
        alerts.append(
            f"Voce ja gastou {spent_percent:.0f}% da renda e ainda faltam {remaining_days} dias no mes."
        )
    if projected_balance < profile.monthly_savings_goal:
        alerts.append(
            "Seu saldo previsto esta abaixo da meta de economia mensal."
        )
    if daily_limit > 0:
        alerts.append(
            f"Para fechar o mes positivo, limite seus gastos a R$ {daily_limit:.2f} por dia."
        )
    if projected_balance < 0:
        alerts.append("Risco alto: o mes esta projetado para fechar negativo.")

    leisure = next((item["amount"] for item in by_category if item["category"] == "lazer"), 0)
    if leisure > total_income * 0.08:
        alerts.append("Seu gasto com lazer esta acima do ideal para a renda atual.")

    if not alerts:
        alerts.append("Financeiro sob controle. Mantenha compras grandes em avaliacao antes de executar.")
    return alerts


def calculate_risk_level(spent_percent: float, projected_balance: float, daily_limit: float) -> str:
    if projected_balance < 0 or spent_percent >= 90:
        return "alto"
    if spent_percent >= 70 or daily_limit < 50:
        return "atencao"
    return "baixo"


def calculate_health_score(
    spent_percent: float,
    projected_balance: float,
    total_income: float,
    target_savings: float,
) -> int:
    score = 100
    score -= min(spent_percent * 0.65, 65)
    if total_income > 0 and projected_balance < target_savings:
        score -= 18
    if projected_balance < 0:
        score -= 25
    return int(max(0, min(100, round(score))))


def build_daily_financial_recommendation(
    risk_level: str,
    projected_balance: float,
    daily_limit: float,
    alerts: list[str],
) -> str:
    if risk_level == "alto":
        return "Pause compras nao essenciais e priorize reduzir saidas recorrentes esta semana."
    if risk_level == "atencao":
        return f"Use R$ {daily_limit:.2f} como teto diario ate nova entrada de renda."
    if projected_balance > 0:
        return "Bom momento para preservar caixa e avaliar aportes ou reserva."
    return alerts[0] if alerts else "Mantenha acompanhamento diario."


def evaluate_purchase(session, data: dict) -> dict:
    summary = get_financial_summary(session)
    name = required_text(data.get("name"), "name")
    amount = money_value(data.get("amount", 0))
    priority = bounded_int(data.get("priority", 5), "priority", 1, 10)
    installments = bounded_int(data.get("installments", 1), "installments", 1, 60)
    payment_type = str(data.get("payment_type", "cash") or "cash").strip().lower()
    installment_value = amount / installments
    projected_after_purchase = summary["projected_balance"] - (
        installment_value if payment_type == "installments" else amount
    )

    decision = "aprovado"
    reasons = []
    if amount >= 500 and summary["risk_level"] != "baixo":
        decision = "nao recomendado"
        reasons.append("Compra acima de R$ 500 nao recomendada esta semana pelo risco atual.")
    elif projected_after_purchase < summary["profile"]["monthly_savings_goal"]:
        decision = "atencao"
        reasons.append("A compra reduz o saldo abaixo da meta de economia mensal.")

    if priority <= 4 and summary["risk_level"] != "baixo":
        decision = "nao recomendado"
        reasons.append("Prioridade baixa em periodo de risco financeiro.")
    if payment_type == "installments" and installments > 1:
        reasons.append(f"Parcelamento adiciona R$ {installment_value:.2f} por parcela ao fluxo.")
    if not reasons:
        reasons.append("Compra cabe no saldo previsto e nao pressiona a meta atual.")

    intention = PurchaseIntention(
        name=name,
        amount=amount,
        priority=priority,
        payment_type=payment_type,
        installments=installments,
        decision=decision,
        justification=" ".join(reasons),
    )
    session.add(intention)
    session.flush()
    session.refresh(intention)

    return {
        "id": intention.id,
        "name": name,
        "amount": round(amount, 2),
        "priority": priority,
        "payment_type": payment_type,
        "installments": installments,
        "installment_value": round(installment_value, 2),
        "decision": decision,
        "justification": intention.justification,
        "projected_balance_after_purchase": round(projected_after_purchase, 2),
    }


def create_goal(session, data: dict) -> FinancialGoal:
    goal = FinancialGoal(
        name=required_text(data.get("name"), "name"),
        goal_type=str(data.get("goal_type", "monthly_savings") or "monthly_savings"),
        target_amount=money_value(data.get("target_amount", 0)),
        current_amount=money_value(data.get("current_amount", 0)),
        category=str(data.get("category", "") or ""),
        status=str(data.get("status", "active") or "active"),
    )
    session.add(goal)
    session.flush()
    session.refresh(goal)
    return goal


def list_goals(session) -> list[dict]:
    goals = (
        session.query(FinancialGoal)
        .filter(FinancialGoal.status == "active")
        .order_by(FinancialGoal.created_at.desc())
        .all()
    )
    return [
        {
            "id": goal.id,
            "name": goal.name,
            "goal_type": goal.goal_type,
            "target_amount": round(goal.target_amount, 2),
            "current_amount": round(goal.current_amount, 2),
            "category": goal.category,
            "status": goal.status,
        }
        for goal in goals
    ]


def categorize_transaction(description: str, transaction_type: str = "expense") -> str:
    if transaction_type == "income":
        return "renda"
    text = (description or "").lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "outros"


def normalize_transaction_type(value: str) -> str:
    value = (value or "expense").strip().lower()
    if value in {"income", "entrada", "receita", "renda"}:
        return "income"
    return "expense"


def money_value(value) -> float:
    try:
        return max(float(str(value).replace(",", ".")), 0)
    except (TypeError, ValueError):
        return 0


def bounded_int(value, field: str, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} precisa ser numero") from exc
    if number < minimum or number > maximum:
        raise ValueError(f"{field} precisa estar entre {minimum} e {maximum}")
    return number


def required_text(value, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} e obrigatorio")
    return text
