import time

from backend.database import init_db
from backend.services.activity_tracker import ActivityTracker


def main():
    init_db()
    tracker = ActivityTracker()
    sample_seconds = 5

    print("LIFE OS activity tracker iniciado. Pressione Ctrl+C para parar.")
    while True:
        log = tracker.capture_once(sample_seconds=sample_seconds)
        print(
            f"{log.app_name} | {log.category} | "
            f"{log.duration_seconds:.0f}s | troca={log.is_context_switch}"
        )
        time.sleep(sample_seconds)


if __name__ == "__main__":
    main()
