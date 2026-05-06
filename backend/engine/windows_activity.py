import ctypes
from ctypes import wintypes
from dataclasses import dataclass


@dataclass(frozen=True)
class ActiveWindow:
    app_name: str
    window_title: str


class WindowsActivityReader:
    def __init__(self):
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    def get_active_window(self) -> ActiveWindow:
        hwnd = self.user32.GetForegroundWindow()
        if not hwnd:
            return ActiveWindow(app_name="unknown", window_title="")

        title = self._get_window_title(hwnd)
        process_id = self._get_process_id(hwnd)
        app_name = self._get_process_name(process_id)
        return ActiveWindow(app_name=app_name, window_title=title)

    def _get_window_title(self, hwnd) -> str:
        length = self.user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return ""

        buffer = ctypes.create_unicode_buffer(length + 1)
        self.user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value

    def _get_process_id(self, hwnd) -> int:
        process_id = wintypes.DWORD()
        self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        return int(process_id.value)

    def _get_process_name(self, process_id: int) -> str:
        if not process_id:
            return "unknown"

        process_query_limited_information = 0x1000
        handle = self.kernel32.OpenProcess(
            process_query_limited_information,
            False,
            process_id,
        )
        if not handle:
            return "unknown"

        try:
            buffer = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buffer))
            ok = self.kernel32.QueryFullProcessImageNameW(
                handle,
                0,
                buffer,
                ctypes.byref(size),
            )
            if not ok:
                return "unknown"

            return buffer.value.split("\\")[-1].lower()
        finally:
            self.kernel32.CloseHandle(handle)
