import socket
import threading
import time
import webbrowser

from backend.app import app


HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}"


def is_server_running(host: str = HOST, port: int = PORT) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def open_browser_once(timeout_seconds: float = 15):
    def _open():
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if is_server_running():
                break
            time.sleep(0.25)
        webbrowser.open(URL, new=2)

    threading.Thread(target=_open, daemon=True).start()


def main():
    if is_server_running():
        webbrowser.open(URL, new=2)
        return

    open_browser_once()
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
