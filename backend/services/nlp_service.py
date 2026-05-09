import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from backend.models import RawEntry, Task
from backend.services.finance_service import (
    categorize_transaction,
    create_transaction,
    display_category,
    get_financial_summary,
)
from backend.services.mobile_entry_service import (
    save_body_metric,
    save_expense,
    save_mood_log,
    save_task_entry,
)


CLASS_FINANCE = "financeiro"
CLASS_HEALTH = "saude"
CLASS_MOOD = "humor"
CLASS_PRODUCTIVITY = "produtividade"
CLASS_SCHEDULE = "agenda"
CLASS_WORKOUT = "treino"
CLASS_NOTE = "nota_geral"

POSITIVE_WORDS = {
    "bem",
    "otimo",
    "otima",
    "feliz",
    "animado",
    "animada",
    "focado",
    "focada",
    "concluido",
    "concluida",
    "feito",
}
NEGATIVE_WORDS = {
    "mal",
    "cansado",
    "cansada",
    "ansioso",
    "ansiosa",
    "triste",
    "estressado",
    "estressada",
    "exausto",
    "exausta",
    "dor",
    "doendo",
}
FINANCE_EXPENSE_WORDS = {"gastei", "gasto", "paguei", "comprei", "compra", "despesa"}
FINANCE_INCOME_WORDS = {"recebi", "ganhei", "salario", "salario", "renda", "freela", "entrada"}
HEALTH_WORDS = {"peso", "sono", "dormi", "dormir", "cansado", "cansada", "dor", "saude"}
MOOD_WORDS = {"humor", "energia", "ansiedade", "ansioso", "ansiosa", "feliz", "triste", "estresse"}
PRODUCTIVITY_WORDS = {"tarefa", "fazer", "revisar", "terminar", "entregar", "projeto", "pcp"}
SCHEDULE_WORDS = {"amanha", "hoje", "consulta", "reuniao", "agenda", "compromisso", "evento"}
WORKOUT_WORDS = {"treino", "academia", "peito", "costas", "perna", "braco", "cardio", "ombro"}
DONE_WORDS = {"concluido", "concluida", "feito", "finalizado", "finalizada", "completei"}


@dataclass
class NlpAnalysis:
    raw_text: str
    normalized_text: str
    classification: str
    confidence: float
    status: str
    extracted_data: dict = field(default_factory=dict)
    interpreted_text: str = ""
    suggestion: str = ""

    @property
    def entry_type(self) -> str:
        return self.extracted_data.get("entry_type") or self.classification


def analyze_message(text: str) -> NlpAnalysis:
    raw_text = (text or "").strip()
    normalized = normalize_text(raw_text)
    extracted = extract_common_data(raw_text, normalized)

    classifiers = [
        analyze_finance,
        analyze_health,
        analyze_mood,
        analyze_schedule,
        analyze_workout,
        analyze_productivity,
    ]
    candidates = [candidate for analyzer in classifiers if (candidate := analyzer(raw_text, normalized, extracted))]
    if candidates:
        analysis = max(candidates, key=lambda item: item.confidence)
        analysis.extracted_data.update(extracted)
        return analysis

    sentiment = extracted.get("sentiment")
    suggestion = "Mensagem guardada como nota geral para revisao futura."
    if sentiment == "negative":
        suggestion = "Sinal de baixa energia detectado. Considere reduzir a proxima missao."

    return NlpAnalysis(
        raw_text=raw_text,
        normalized_text=normalized,
        classification=CLASS_NOTE,
        confidence=0.35 if normalized else 0,
        status="raw_input",
        extracted_data=extracted,
        interpreted_text=f"nota geral: {raw_text}" if raw_text else "nota geral vazia",
        suggestion=suggestion,
    )


def analyze_finance(raw_text: str, normalized: str, extracted: dict) -> NlpAnalysis | None:
    words = set(normalized.split())
    has_finance_word = bool(words & FINANCE_EXPENSE_WORDS or words & FINANCE_INCOME_WORDS)
    if not has_finance_word or not extracted["monetary_values"]:
        return None

    amount = extracted["monetary_values"][0]
    transaction_type = "income" if words & FINANCE_INCOME_WORDS and not words & {"gastei", "gasto", "paguei", "comprei"} else "expense"
    description = description_after_amount(normalized, amount)
    if not description:
        description = clean_description_without_keywords(normalized, FINANCE_EXPENSE_WORDS | FINANCE_INCOME_WORDS)
    category = categorize_transaction(description, transaction_type)
    label = display_category(category)
    entry_type = "income" if transaction_type == "income" else "expense"
    verb = "Renda" if transaction_type == "income" else "Gasto"

    return NlpAnalysis(
        raw_text=raw_text,
        normalized_text=normalized,
        classification=CLASS_FINANCE,
        confidence=0.96,
        status="interpreted",
        extracted_data={
            "entry_type": entry_type,
            "transaction_type": transaction_type,
            "amount": amount,
            "description": description or label,
            "category": category,
        },
        interpreted_text=f"{verb} registrado: R${amount:g} - {label}",
        suggestion="Financeiro atualizado automaticamente.",
    )


def analyze_health(raw_text: str, normalized: str, extracted: dict) -> NlpAnalysis | None:
    words = set(normalized.split())
    if "peso" in words and extracted["numbers"]:
        weight = extracted["numbers"][0]
        return NlpAnalysis(
            raw_text=raw_text,
            normalized_text=normalized,
            classification=CLASS_HEALTH,
            confidence=0.95,
            status="interpreted",
            extracted_data={"entry_type": "body_metric", "metric_type": "weight", "value": weight, "unit": "kg"},
            interpreted_text=f"peso corporal registrado: {weight:g} kg",
            suggestion="Use a medida como tendencia, nao como julgamento do dia.",
        )

    if "sono" in words or "dormi" in words or "dormir" in words:
        hours = extracted["numbers"][0] if extracted["numbers"] else None
        quality = "ruim" if any(word in words for word in ["mal", "pouco", "cansado", "cansada"]) else "normal"
        suggestion = "Reduza carga cognitiva hoje." if quality == "ruim" or (hours is not None and hours < 6) else "Energia basal adequada para tarefas medias."
        text = f"sono registrado: {hours:g} horas" if hours is not None else f"sono registrado: qualidade {quality}"
        return NlpAnalysis(
            raw_text=raw_text,
            normalized_text=normalized,
            classification=CLASS_HEALTH,
            confidence=0.82,
            status="interpreted" if hours is not None else "partial",
            extracted_data={"entry_type": "body_metric", "metric_type": "sleep", "value": hours, "unit": "h", "quality": quality},
            interpreted_text=text,
            suggestion=suggestion,
        )

    if words & HEALTH_WORDS:
        sentiment = extracted.get("sentiment") or "neutral"
        return NlpAnalysis(
            raw_text=raw_text,
            normalized_text=normalized,
            classification=CLASS_HEALTH,
            confidence=0.62,
            status="partial",
            extracted_data={"entry_type": "health_note", "sentiment": sentiment},
            interpreted_text=f"registro de saude: {raw_text}",
            suggestion="Contexto de saude salvo. O LIFE OS pode reduzir a exigencia das proximas tarefas.",
        )

    return None


def analyze_mood(raw_text: str, normalized: str, extracted: dict) -> NlpAnalysis | None:
    words = set(normalized.split())
    if not words & MOOD_WORDS:
        return None

    mood = int_keyword(normalized, "humor")
    energy = int_keyword(normalized, "energia")
    anxiety = int_keyword(normalized, "ansiedade")
    sentiment = extracted.get("sentiment") or infer_sentiment(normalized)
    if mood is None and sentiment == "positive":
        mood = 7
    if mood is None and sentiment == "negative":
        mood = 4

    interpreted = []
    if mood is not None:
        interpreted.append(f"humor {mood}")
    if energy is not None:
        interpreted.append(f"energia {energy}")
    if anxiety is not None:
        interpreted.append(f"ansiedade {anxiety}")
    if not interpreted:
        interpreted.append(f"sentimento {sentiment or 'neutro'}")

    return NlpAnalysis(
        raw_text=raw_text,
        normalized_text=normalized,
        classification=CLASS_MOOD,
        confidence=0.78,
        status="interpreted" if mood is not None or energy is not None or anxiety is not None else "partial",
        extracted_data={"entry_type": "mood_log", "mood": mood, "energy": energy, "anxiety": anxiety, "sentiment": sentiment},
        interpreted_text="humor registrado: " + ", ".join(interpreted),
        suggestion=build_context_suggestion(sentiment, energy, anxiety),
    )


def analyze_schedule(raw_text: str, normalized: str, extracted: dict) -> NlpAnalysis | None:
    words = set(normalized.split())
    event_words = SCHEDULE_WORDS - {"hoje", "amanha"}
    if not (words & SCHEDULE_WORDS or extracted["dates"] or extracted["times"]):
        return None
    if not (words & event_words or extracted["times"]):
        return None

    return NlpAnalysis(
        raw_text=raw_text,
        normalized_text=normalized,
        classification=CLASS_SCHEDULE,
        confidence=0.72,
        status="partial",
        extracted_data={"entry_type": "schedule_note", "dates": extracted["dates"], "times": extracted["times"]},
        interpreted_text=f"agenda registrada: {raw_text}",
        suggestion="Compromisso salvo como entrada bruta. Proximo passo: conectar calendario para criar eventos automaticamente.",
    )


def analyze_workout(raw_text: str, normalized: str, extracted: dict) -> NlpAnalysis | None:
    words = set(normalized.split())
    if not words & WORKOUT_WORDS:
        return None

    status = "done" if words & DONE_WORDS else "logged"
    name = remove_words(normalized, {"treino"} | DONE_WORDS).strip() or "treino"
    return NlpAnalysis(
        raw_text=raw_text,
        normalized_text=normalized,
        classification=CLASS_WORKOUT,
        confidence=0.86,
        status="interpreted",
        extracted_data={"entry_type": "workout", "name": name, "workout_status": status},
        interpreted_text=f"treino registrado: {name} | status {status}",
        suggestion="Treino salvo. O LIFE OS pode ajustar a missao considerando energia restante.",
    )


def analyze_productivity(raw_text: str, normalized: str, extracted: dict) -> NlpAnalysis | None:
    words = set(normalized.split())
    if not words & PRODUCTIVITY_WORDS:
        return None

    impact = bounded_score(int_keyword(normalized, "impacto"), 5)
    urgency = bounded_score(int_keyword(normalized, "urgencia"), 5)
    energy = bounded_score(int_keyword(normalized, "energia"), 5)
    name = clean_task_name(normalized)

    return NlpAnalysis(
        raw_text=raw_text,
        normalized_text=normalized,
        classification=CLASS_PRODUCTIVITY,
        confidence=0.74,
        status="interpreted" if "tarefa" in words else "partial",
        extracted_data={
            "entry_type": "task",
            "name": name,
            "impact": impact,
            "urgency": urgency,
            "energy_required": energy,
        },
        interpreted_text=f"tarefa criada: {name} | impacto {impact} | urgencia {urgency} | energia {energy}",
        suggestion="A missao sera recalculada automaticamente.",
    )


def save_raw_entry(
    session,
    analysis: NlpAnalysis,
    chat_id: str = "",
    username: str = "",
    source: str = "telegram",
) -> RawEntry:
    raw_entry = RawEntry(
        source=source,
        raw_text=analysis.raw_text,
        normalized_text=analysis.normalized_text,
        classification=analysis.classification,
        confidence=round(float(analysis.confidence), 3),
        status=analysis.status,
        extracted_data=json.dumps(analysis.extracted_data, ensure_ascii=True),
        interpreted_text=analysis.interpreted_text,
        suggestion=analysis.suggestion,
        chat_id=str(chat_id or ""),
        username=str(username or ""),
    )
    session.add(raw_entry)
    session.flush()
    session.refresh(raw_entry)
    return raw_entry


def apply_analysis(session, analysis: NlpAnalysis, source: str = "telegram") -> None:
    data = analysis.extracted_data
    entry_type = data.get("entry_type")

    if analysis.classification == CLASS_FINANCE:
        create_transaction(
            session,
            amount=data["amount"],
            description=data.get("description", ""),
            transaction_type=data.get("transaction_type", "expense"),
            category=data.get("category"),
            source=source,
        )
        if data.get("transaction_type") == "expense":
            save_expense(session, data["amount"], data.get("description", ""))
        return

    if entry_type == "body_metric" and data.get("value") is not None:
        save_body_metric(session, data.get("metric_type", "metric"), data["value"], data.get("unit", ""))
        return

    if entry_type == "mood_log":
        save_mood_log(session, mood=data.get("mood"), energy=data.get("energy"), anxiety=data.get("anxiety"))
        return

    if entry_type == "workout":
        save_task_entry(session, name=data.get("name") or "treino", entry_type="workout", status=data.get("workout_status", "logged"))
        return

    if entry_type == "task" and analysis.status == "interpreted":
        task = Task(
            name=data.get("name") or analysis.raw_text,
            impact=data.get("impact", 5),
            urgency=data.get("urgency", 5),
            energy_required=data.get("energy_required", 5),
            status="pending",
        )
        session.add(task)
        save_task_entry(session, name=task.name, entry_type="task", status="created")


def build_telegram_response(session, analysis: NlpAnalysis) -> str:
    if analysis.classification == CLASS_FINANCE:
        summary = get_financial_summary(session)
        data = analysis.extracted_data
        if data.get("transaction_type") == "income":
            return f"{analysis.interpreted_text}\nSaldo previsto atualizado: R$ {summary['projected_balance']:.2f}."
        return f"{analysis.interpreted_text}\n{summary['recommendation']}"

    if analysis.status == "raw_input":
        return f"Mensagem salva como nota geral.\nInterpretacao: {analysis.interpreted_text}\nSugestao: {analysis.suggestion}"

    return f"Salvo no LIFE OS.\nInterpretacao: {analysis.interpreted_text}\nProxima recomendacao: {analysis.suggestion}"


def list_raw_entries(session, limit: int = 20) -> dict:
    entries = (
        session.query(RawEntry)
        .order_by(RawEntry.created_at.desc())
        .limit(limit)
        .all()
    )
    serialized = [serialize_raw_entry(entry) for entry in entries]
    return {
        "entries": serialized,
        "interpreted": [entry for entry in serialized if entry["status"] in {"interpreted", "partial"}],
        "unclassified": [entry for entry in serialized if entry["status"] == "raw_input"],
        "suggestions": [entry["suggestion"] for entry in serialized if entry.get("suggestion")][:6],
    }


def serialize_raw_entry(entry: RawEntry) -> dict:
    try:
        extracted = json.loads(entry.extracted_data or "{}")
    except json.JSONDecodeError:
        extracted = {}
    return {
        "id": entry.id,
        "source": entry.source,
        "raw_text": entry.raw_text,
        "classification": entry.classification,
        "confidence": round(entry.confidence, 3),
        "status": entry.status,
        "extracted_data": extracted,
        "interpreted_text": entry.interpreted_text,
        "suggestion": entry.suggestion,
        "chat_id": entry.chat_id,
        "username": entry.username,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


def extract_common_data(raw_text: str, normalized: str) -> dict:
    numbers = [float(match.replace(",", ".")) for match in re.findall(r"\b\d+(?:[\.,]\d+)?\b", normalized)]
    money_values = extract_money_values(normalized, numbers)
    return {
        "numbers": numbers,
        "dates": extract_dates(normalized),
        "times": extract_times(normalized),
        "monetary_values": money_values,
        "sentiment": infer_sentiment(normalized),
    }


def extract_money_values(normalized: str, numbers: list[float]) -> list[float]:
    explicit = [
        float(value.replace(",", "."))
        for value in re.findall(r"(?:r\$\s*|\breais?\s+|\brs\s*)(\d+(?:[\.,]\d+)?)", normalized)
    ]
    if explicit:
        return explicit
    words = set(normalized.split())
    if words & FINANCE_EXPENSE_WORDS or words & FINANCE_INCOME_WORDS:
        return numbers[:1]
    return []


def extract_dates(normalized: str) -> list[str]:
    today = datetime.utcnow().date()
    dates = []
    if "hoje" in normalized:
        dates.append(today.isoformat())
    if "amanha" in normalized:
        dates.append((today + timedelta(days=1)).isoformat())
    for day, month in re.findall(r"\b(\d{1,2})/(\d{1,2})\b", normalized):
        year = today.year
        dates.append(f"{year:04d}-{int(month):02d}-{int(day):02d}")
    return dates


def extract_times(normalized: str) -> list[str]:
    times = []
    for hour, minute in re.findall(r"\b(\d{1,2})h(?:(\d{2}))?\b", normalized):
        times.append(f"{int(hour):02d}:{int(minute or 0):02d}")
    for hour, minute in re.findall(r"\b(\d{1,2}):(\d{2})\b", normalized):
        times.append(f"{int(hour):02d}:{int(minute):02d}")
    return list(dict.fromkeys(times))


def infer_sentiment(normalized: str) -> str | None:
    words = set(normalized.split())
    if words & NEGATIVE_WORDS:
        return "negative"
    if words & POSITIVE_WORDS:
        return "positive"
    return None


def normalize_text(text: str) -> str:
    normalized = " ".join((text or "").strip().lower().split())
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return normalized


def description_after_amount(normalized: str, amount: float) -> str:
    amount_text = f"{amount:g}".replace(".", r"[\.,]")
    match = re.search(rf"\b{amount_text}\b(?:\s*(?:reais|real|rs))?\s*(.*)$", normalized)
    return clean_financial_description(match.group(1) if match else "")


def clean_description_without_keywords(normalized: str, keywords: set[str]) -> str:
    return clean_financial_description(remove_words(normalized, keywords))


def clean_financial_description(description: str) -> str:
    return remove_words(description or "", {"reais", "real", "rs", "r$"}).strip()


def remove_words(text: str, words: set[str]) -> str:
    return " ".join(word for word in text.split() if word not in words)


def int_keyword(text: str, keyword: str) -> int | None:
    match = re.search(rf"\b{keyword}\s+(\d+)", text)
    return int(match.group(1)) if match else None


def bounded_score(value: int | None, default: int) -> int:
    if value is None:
        return default
    return max(1, min(int(value), 10))


def clean_task_name(normalized: str) -> str:
    text = normalized.removeprefix("tarefa ").strip()
    text = re.split(r"\bimpacto\s+\d+", text, maxsplit=1)[0].strip()
    text = re.split(r"\burgencia\s+\d+", text, maxsplit=1)[0].strip()
    text = re.split(r"\benergia\s+\d+", text, maxsplit=1)[0].strip()
    return text or normalized


def build_context_suggestion(sentiment: str | None, energy: int | None, anxiety: int | None) -> str:
    if anxiety is not None and anxiety >= 7:
        return "Priorize tarefa curta e ambiente com baixa friccao."
    if energy is not None and energy <= 4:
        return "Escolha uma missao de baixa energia ou divida a atual em primeiro passo."
    if sentiment == "negative":
        return "Baixa energia detectada. Reduza a exigencia da proxima decisao."
    if sentiment == "positive":
        return "Bom momento para puxar uma tarefa de impacto maior."
    return "Registro salvo para alimentar as proximas decisoes."
