import asyncio
import re
import threading
from dataclasses import dataclass

from config import config
from backend.database import session_scope
from backend.models import Task
from backend.services.decision_engine import choose_current_mission
from backend.services.mobile_entry_service import (
    create_mobile_entry,
    save_body_metric,
    save_expense,
    save_mood_log,
    save_task_entry,
)
from backend.services.productivity_engine import (
    build_focus_recommendation,
    get_focus_snapshot,
)


@dataclass(frozen=True)
class TelegramInterpretation:
    entry_type: str
    interpreted_text: str
    recommendation: str


class TelegramBotService:
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self._thread = None
        self._last_error = None
        self._running = False

    def start(self):
        if self.is_running:
            return
        if not self.token:
            self._last_error = "TELEGRAM_BOT_TOKEN nao configurado"
            return

        self._thread = threading.Thread(
            target=self._run_thread,
            name="life-os-telegram-bot",
            daemon=True,
        )
        self._thread.start()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and self._running

    def status(self) -> dict:
        return {
            "running": self.is_running,
            "configured": bool(self.token),
            "last_error": self._last_error,
        }

    def _run_thread(self):
        try:
            asyncio.run(self._run_bot())
        except Exception as exc:
            self._running = False
            self._last_error = str(exc)

    async def _run_bot(self):
        try:
            from telegram import Update
            from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
        except ImportError as exc:
            self._last_error = "Instale python-telegram-bot para ativar o Telegram"
            raise exc

        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "LIFE OS ativo. Envie: peso 88.1, sono 6h, gastei 45 almoco, "
                "humor 7 energia 6 ansiedade 3, tarefa revisar PCP impacto 8 urgencia 7 energia 5."
            )

        async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            text = update.message.text or ""
            response = process_telegram_message(text)
            await update.message.reply_text(response)

        application = Application.builder().token(self.token).build()
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        self._running = True
        self._last_error = None
        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        stop_event = asyncio.Event()
        await stop_event.wait()


telegram_bot_service = TelegramBotService()


def process_telegram_message(text: str) -> str:
    normalized = normalize_text(text)
    try:
        with session_scope() as session:
            interpretation = interpret_and_save(session, normalized, text)
            snapshot = get_focus_snapshot(session)
            mission = choose_current_mission(
                session,
                focus_score=snapshot["focus_score"],
                state=snapshot["state"],
            )
            recommendation = (
                interpretation.recommendation
                or build_focus_recommendation(snapshot, mission)
            )
            create_mobile_entry(
                session,
                entry_type=interpretation.entry_type,
                raw_text=text,
                interpreted_text=interpretation.interpreted_text,
                recommendation=recommendation,
            )

        return (
            "Salvo no LIFE OS.\n"
            f"Interpretacao: {interpretation.interpreted_text}\n"
            f"Proxima recomendacao: {recommendation}"
        )
    except ValueError as exc:
        return f"Nao consegui interpretar: {exc}"


def interpret_and_save(session, normalized: str, raw_text: str) -> TelegramInterpretation:
    if normalized.startswith("peso "):
        value = parse_float_after_keyword(normalized, "peso")
        save_body_metric(session, "weight", value, "kg")
        return TelegramInterpretation(
            "body_metric",
            f"peso corporal registrado: {value:g} kg",
            "Use essa medida como tendencia, nao como julgamento do dia.",
        )

    if normalized.startswith("sono "):
        hours = parse_sleep_hours(normalized)
        save_body_metric(session, "sleep", hours, "h")
        recommendation = (
            "Reduza carga cognitiva hoje." if hours < 6 else "Energia basal adequada para tarefas medias."
        )
        return TelegramInterpretation(
            "body_metric",
            f"sono registrado: {hours:g} horas",
            recommendation,
        )

    if normalized.startswith("gastei "):
        amount, description = parse_expense(normalized)
        save_expense(session, amount, description)
        return TelegramInterpretation(
            "expense",
            f"gasto registrado: {amount:g} em {description or 'sem descricao'}",
            "Gasto salvo. Revise padroes se isso se repetir no mesmo contexto.",
        )

    if normalized.startswith("humor "):
        mood, energy, anxiety = parse_mood(normalized)
        save_mood_log(session, mood=mood, energy=energy, anxiety=anxiety)
        recommendation = build_mood_recommendation(mood, energy, anxiety)
        return TelegramInterpretation(
            "mood_log",
            f"humor {mood}, energia {energy}, ansiedade {anxiety}",
            recommendation,
        )

    if normalized.startswith("tarefa "):
        name, impact, urgency, energy = parse_task(normalized)
        task = Task(
            name=name,
            impact=impact,
            urgency=urgency,
            energy_required=energy,
            status="pending",
        )
        session.add(task)
        save_task_entry(session, name=name, entry_type="task", status="created")
        return TelegramInterpretation(
            "task",
            f"tarefa criada: {name} | impacto {impact} | urgencia {urgency} | energia {energy}",
            "A missao sera recalculada automaticamente.",
        )

    if normalized.startswith("treino "):
        name = normalized.removeprefix("treino ").strip()
        status = "done" if has_done_word(name) else "logged"
        clean_name = remove_done_words(name).strip() or "treino"
        save_task_entry(session, name=clean_name, entry_type="workout", status=status)
        return TelegramInterpretation(
            "task_entry",
            f"treino registrado: {clean_name} | status {status}",
            "Treino salvo. Ajuste a proxima missao considerando energia restante.",
        )

    raise ValueError(
        "envie algo como 'peso 88.1', 'sono 6h', 'gastei 45 almoco', "
        "'humor 7 energia 6 ansiedade 3' ou 'tarefa revisar PCP impacto 8 urgencia 7 energia 5'"
    )


def normalize_text(text: str) -> str:
    replacements = {
        "urgência": "urgencia",
        "concluído": "concluido",
        "concluída": "concluida",
        "almoço": "almoco",
    }
    normalized = " ".join((text or "").strip().lower().split())
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized


def parse_float_after_keyword(text: str, keyword: str) -> float:
    match = re.search(rf"\b{keyword}\s+(\d+(?:[\.,]\d+)?)", text)
    if not match:
        raise ValueError(f"valor de {keyword} ausente")
    return float(match.group(1).replace(",", "."))


def parse_sleep_hours(text: str) -> float:
    match = re.search(r"\bsono\s+(\d+(?:[\.,]\d+)?)\s*h?", text)
    if not match:
        raise ValueError("horas de sono ausentes")
    return float(match.group(1).replace(",", "."))


def parse_expense(text: str) -> tuple[float, str]:
    match = re.search(r"\bgastei\s+(\d+(?:[\.,]\d+)?)(?:\s+(.+))?", text)
    if not match:
        raise ValueError("valor do gasto ausente")
    amount = float(match.group(1).replace(",", "."))
    description = (match.group(2) or "").strip()
    return amount, description


def parse_mood(text: str) -> tuple[int, int | None, int | None]:
    mood = parse_int_keyword(text, "humor")
    energy = parse_int_keyword(text, "energia", required=False)
    anxiety = parse_int_keyword(text, "ansiedade", required=False)
    return mood, energy, anxiety


def parse_task(text: str) -> tuple[str, int, int, int]:
    impact_match = re.search(r"\bimpacto\s+(\d+)", text)
    urgency_match = re.search(r"\burgencia\s+(\d+)", text)
    energy_match = re.search(r"\benergia\s+(\d+)", text)
    if not impact_match or not urgency_match or not energy_match:
        raise ValueError("tarefa precisa de impacto, urgencia e energia")

    name = text.removeprefix("tarefa ").strip()
    name = re.split(r"\bimpacto\s+\d+", name, maxsplit=1)[0].strip()
    if not name:
        raise ValueError("nome da tarefa ausente")

    return (
        name,
        bounded_int(impact_match.group(1), "impacto"),
        bounded_int(urgency_match.group(1), "urgencia"),
        bounded_int(energy_match.group(1), "energia"),
    )


def parse_int_keyword(text: str, keyword: str, required: bool = True) -> int | None:
    match = re.search(rf"\b{keyword}\s+(\d+)", text)
    if not match:
        if required:
            raise ValueError(f"{keyword} ausente")
        return None
    return bounded_int(match.group(1), keyword)


def bounded_int(value, field: str) -> int:
    number = int(value)
    if number < 1 or number > 10:
        raise ValueError(f"{field} precisa estar entre 1 e 10")
    return number


def build_mood_recommendation(mood: int, energy: int | None, anxiety: int | None) -> str:
    if anxiety is not None and anxiety >= 7:
        return "Priorize tarefa curta e ambiente com baixa friccao."
    if energy is not None and energy <= 4:
        return "Escolha uma missao de baixa energia ou divida a atual em primeiro passo."
    if mood >= 7 and (energy or 0) >= 6:
        return "Bom momento para tarefa de impacto alto."
    return "Registro salvo. O sistema vai considerar esse contexto nas proximas decisoes."


def has_done_word(text: str) -> bool:
    return any(word in text for word in ["concluido", "concluida", "feito", "finalizado"])


def remove_done_words(text: str) -> str:
    for word in ["concluido", "concluida", "feito", "finalizado"]:
        text = text.replace(word, "")
    return " ".join(text.split())
