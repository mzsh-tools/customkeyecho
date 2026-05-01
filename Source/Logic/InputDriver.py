import ctypes
import random
import time
from ctypes import wintypes

User32 = ctypes.windll.user32

INPUT_KEYBOARD = 1
INPUT_MOUSE = 0
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100
XBUTTON1 = 0x0001
XBUTTON2 = 0x0002
MAPVK_VK_TO_VSC = 0

_ExtendedVKs = {
    0x21, 0x22, 0x23, 0x24,  # PageUp/PageDown/End/Home
    0x25, 0x26, 0x27, 0x28,  # 方向键
    0x2D, 0x2E,              # Insert/Delete
    0x5B, 0x5C,              # Win 键
    0x6F, 0x90,              # 小键盘除号/NumLock
    0xA3, 0xA5,              # 右 Ctrl/右 Alt
}


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("Vk", ctypes.c_ushort),
        ("Scan", ctypes.c_ushort),
        ("Flags", ctypes.c_ulong),
        ("Time", ctypes.c_ulong),
        ("ExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("Dx", ctypes.c_long),
        ("Dy", ctypes.c_long),
        ("MouseData", ctypes.c_ulong),
        ("Flags", ctypes.c_ulong),
        ("Time", ctypes.c_ulong),
        ("ExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("Msg", ctypes.c_ulong),
        ("ParamL", ctypes.c_ushort),
        ("ParamH", ctypes.c_ushort),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [
        ("Ki", _KEYBDINPUT),
        ("Mi", _MOUSEINPUT),
        ("Hi", _HARDWAREINPUT),
    ]


class _INPUT(ctypes.Structure):
    _fields_ = [
        ("Type", ctypes.c_ulong),
        ("Union", _INPUTUNION),
    ]


def _SendKeyEvent(Vk: int, KeyUp: bool):
    """发送单次键盘事件（按下或释放）"""
    Scan = User32.MapVirtualKeyW(Vk, MAPVK_VK_TO_VSC)
    Flags = KEYEVENTF_SCANCODE
    if Vk in _ExtendedVKs:
        Flags |= KEYEVENTF_EXTENDEDKEY
    if KeyUp:
        Flags |= KEYEVENTF_KEYUP

    Inp = _INPUT()
    Inp.Type = INPUT_KEYBOARD
    Inp.Union.Ki.Vk = 0
    Inp.Union.Ki.Scan = Scan
    Inp.Union.Ki.Flags = Flags
    User32.SendInput(1, ctypes.byref(Inp), ctypes.sizeof(_INPUT))


def SendKey(Vk: int):
    """发送键盘按键（按下+释放），使用硬件扫描码"""
    _SendKeyEvent(Vk, False)
    time.sleep(0.01)
    _SendKeyEvent(Vk, True)


def SendKeyCombo(Modifiers: list[int], Vk: int, ComboDelayMin: float = 0.010, ComboDelayMax: float = 0.030):
    """发送组合键：依次按下修饰键 → 按主键 → 依次释放修饰键，间隔随机"""
    def _RandDelay():
        time.sleep(random.uniform(ComboDelayMin, ComboDelayMax))

    for Mod in Modifiers:
        _SendKeyEvent(Mod, False)
        _RandDelay()
    _SendKeyEvent(Vk, False)
    time.sleep(0.01)
    _SendKeyEvent(Vk, True)
    _RandDelay()
    for Mod in reversed(Modifiers):
        _SendKeyEvent(Mod, True)
        _RandDelay()


_MouseBtnFlags = {
    1: (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP, 0),
    2: (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP, 0),
    3: (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP, 0),
    4: (MOUSEEVENTF_XDOWN, MOUSEEVENTF_XUP, XBUTTON1),
    5: (MOUSEEVENTF_XDOWN, MOUSEEVENTF_XUP, XBUTTON2),
}


def SendMouseClick(BtnCode: int):
    """发送鼠标按键（按下+释放）"""
    if BtnCode not in _MouseBtnFlags:
        return
    DownFlag, UpFlag, Data = _MouseBtnFlags[BtnCode]

    Inp = _INPUT()
    Inp.Type = INPUT_MOUSE
    Inp.Union.Mi.Flags = DownFlag
    Inp.Union.Mi.MouseData = Data
    User32.SendInput(1, ctypes.byref(Inp), ctypes.sizeof(_INPUT))

    time.sleep(0.01)

    Inp.Union.Mi.Flags = UpFlag
    Inp.Union.Mi.MouseData = Data
    User32.SendInput(1, ctypes.byref(Inp), ctypes.sizeof(_INPUT))
