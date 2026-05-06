import threading
from datetime import datetime

from config import config


class BackgroundActivityTracker:
    def __init__(self, sample_seconds: int = 5):
        self.sample_seconds = sample_seconds
        self.tracker = None
        self._thread = None
        self._stop_event = threading.Event()
        self._last_error = None
        self._last_capture_at = None
        self._last_log = None

    def start(self):
        if self.is_running:
            return

        if self.tracker is None:
            from backend.services.activity_tracker import ActivityTracker

            self.tracker = ActivityTracker()

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="life-os-activity-tracker",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def status(self) -> dict:
        return {
            "running": self.is_running,
            "sample_seconds": self.sample_seconds,
            "last_capture_at": self._last_capture_at.isoformat()
            if self._last_capture_at
            else None,
            "last_error": self._last_error,
            "current_activity": self._last_log,
        }

    def _run(self):
        while not self._stop_event.is_set():
            try:
                log = self.tracker.capture_once(sample_seconds=self.sample_seconds)
                self._last_capture_at = datetime.utcnow()
                self._last_log = {
                    "id": log.id,
                    "app_name": log.app_name,
                    "window_title": log.window_title,
                    "category": log.category,
                    "duration_seconds": round(log.duration_seconds, 2),
                    "is_context_switch": log.is_context_switch,
                }
                self._last_error = None
            except Exception as exc:
                self._last_error = str(exc)

            self._stop_event.wait(self.sample_seconds)


background_activity_tracker = BackgroundActivityTracker(
    sample_seconds=config.LIFE_OS_SAMPLE_SECONDS
)


def should_start_background_tracker() -> bool:
    if config.LIFE_OS_DISABLE_TRACKER:
        return False

    if not config.LIFE_OS_ENABLE_WINDOWS_TRACKER:
        return False

    import os

    werkzeug_run_main = os.getenv("WERKZEUG_RUN_MAIN")
    if werkzeug_run_main is None:
        return True

    return werkzeug_run_main == "true"
