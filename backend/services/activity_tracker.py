from datetime import datetime, timedelta

from backend.database import session_scope
from backend.engine.windows_activity import ActiveWindow, WindowsActivityReader
from backend.models import ActivityLog


PRODUCTIVE_APPS = {
    "code.exe",
    "cursor.exe",
    "pycharm64.exe",
    "webstorm64.exe",
    "devenv.exe",
    "terminal.exe",
    "windowsterminal.exe",
    "powershell.exe",
    "cmd.exe",
    "excel.exe",
    "winword.exe",
    "notion.exe",
    "obsidian.exe",
}

DISTRACTION_APPS = {
    "chrome.exe",
    "msedge.exe",
    "firefox.exe",
    "brave.exe",
    "discord.exe",
    "telegram.exe",
    "whatsapp.exe",
    "spotify.exe",
    "steam.exe",
}

PRODUCTIVE_TITLE_HINTS = {
    "github",
    "gitlab",
    "stackoverflow",
    "docs",
    "documentation",
    "localhost",
    "python",
    "flask",
    "fastapi",
}

DISTRACTION_TITLE_HINTS = {
    "youtube",
    "instagram",
    "tiktok",
    "netflix",
    "x.com",
    "twitter",
    "reddit",
}


def classify_activity(app_name: str, window_title: str) -> str:
    app = (app_name or "").lower()
    title = (window_title or "").lower()

    if any(hint in title for hint in DISTRACTION_TITLE_HINTS):
        return "distraction"
    if any(hint in title for hint in PRODUCTIVE_TITLE_HINTS):
        return "productive"
    if app in PRODUCTIVE_APPS:
        return "productive"
    if app in DISTRACTION_APPS:
        return "distraction"
    return "neutral"


class ActivityTracker:
    def __init__(self, reader=None):
        self.reader = reader or WindowsActivityReader()

    def capture_once(self, sample_seconds: int = 5) -> ActivityLog:
        active_window = self.reader.get_active_window()
        now = datetime.utcnow()
        started_at = now - timedelta(seconds=sample_seconds)

        with session_scope() as session:
            previous = (
                session.query(ActivityLog)
                .order_by(ActivityLog.ended_at.desc())
                .first()
            )
            category = classify_activity(
                active_window.app_name,
                active_window.window_title,
            )

            if self._can_extend_previous(previous, active_window, sample_seconds):
                previous.ended_at = now
                previous.duration_seconds = max(
                    previous.duration_seconds + float(sample_seconds),
                    (previous.ended_at - previous.started_at).total_seconds(),
                )
                previous.category = category
                log = previous
            else:
                log = ActivityLog(
                    app_name=active_window.app_name,
                    window_title=active_window.window_title,
                    started_at=started_at,
                    ended_at=now,
                    duration_seconds=float(sample_seconds),
                    category=category,
                    is_context_switch=self._is_context_switch(previous, active_window),
                )
                session.add(log)

            session.flush()
            session.refresh(log)
            session.expunge(log)
            return log

    def _is_context_switch(self, previous, active_window: ActiveWindow) -> bool:
        if previous is None:
            return False
        return (
            previous.app_name != active_window.app_name
            or self._normalize_title(previous.window_title)
            != self._normalize_title(active_window.window_title)
        )

    def _can_extend_previous(
        self,
        previous,
        active_window: ActiveWindow,
        sample_seconds: int,
    ) -> bool:
        if previous is None:
            return False

        same_window = (
            previous.app_name == active_window.app_name
            and self._normalize_title(previous.window_title)
            == self._normalize_title(active_window.window_title)
        )
        if not same_window:
            return False

        max_gap_seconds = max(sample_seconds * 2, 10)
        gap_seconds = (datetime.utcnow() - previous.ended_at).total_seconds()
        return gap_seconds <= max_gap_seconds

    def _normalize_title(self, title: str) -> str:
        return " ".join((title or "").lower().split())
