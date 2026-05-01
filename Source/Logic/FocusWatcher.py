import ctypes
from ctypes import wintypes

User32 = ctypes.windll.user32


def GetForegroundWindowTitle() -> str:
    Hwnd = User32.GetForegroundWindow()
    Length = User32.GetWindowTextLengthW(Hwnd)
    if Length == 0:
        return ""
    Buf = ctypes.create_unicode_buffer(Length + 1)
    User32.GetWindowTextW(Hwnd, Buf, Length + 1)
    return Buf.value


def IsWindowFocused(Title: str) -> bool:
    if not Title:
        return True
    return Title.lower() in GetForegroundWindowTitle().lower()


def IsWindowExist(Title: str) -> bool:
    """检查标题匹配的窗口是否存在"""
    if not Title:
        return True
    TitleLower = Title.lower()
    for W in ListWindows():
        if TitleLower in W.lower():
            return True
    return False


def ListWindows() -> list[str]:
    """枚举所有可见窗口标题"""
    Titles = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _EnumCallback(Hwnd, _):
        if User32.IsWindowVisible(Hwnd):
            Length = User32.GetWindowTextLengthW(Hwnd)
            if Length > 0:
                Buf = ctypes.create_unicode_buffer(Length + 1)
                User32.GetWindowTextW(Hwnd, Buf, Length + 1)
                if Buf.value.strip():
                    Titles.append(Buf.value)
        return True

    User32.EnumWindows(_EnumCallback, 0)
    return Titles
