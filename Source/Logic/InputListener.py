from pynput import keyboard, mouse
from PySide6.QtCore import QObject, Signal

from Source.Data.KeyProfile import DefaultHotKeyCode

# 修饰键 VK 码 → 显示名称
_ModifierKeys = {
    160: "Shift", 161: "Shift",   # L/R Shift
    162: "Ctrl", 163: "Ctrl",     # L/R Ctrl
    164: "Alt", 165: "Alt",       # L/R Alt
}

# 归一化：左右修饰键统一为左侧 VK
_ModNormalize = {160: 160, 161: 160, 162: 162, 163: 162, 164: 164, 165: 164}

# 鼠标按键映射（不含侧键，侧键通过 win32_event_filter 处理）
_MouseButtonMap = {
    mouse.Button.left: (1, "鼠标左键"),
    mouse.Button.right: (2, "鼠标右键"),
    mouse.Button.middle: (3, "鼠标中键"),
}

# 侧键编号映射
_XButtonMap = {1: (4, "鼠标侧键1"), 2: (5, "鼠标侧键2")}

# 快捷键类型标记：鼠标按键用负数编码区分
# Code > 0 = 键盘 VK，Code < 0 = 鼠标按键（-1=左键, -2=右键, ..., -4=侧键1, -5=侧键2）


class InputListener(QObject):
    ActionCaptured = Signal(str, int, str, list)  # Type, Code, Name, Modifiers
    RecordingStopped = Signal()
    HotKeyTriggered = Signal()
    HotKeyCaptured = Signal(int, str, list)  # Code, Name, Modifiers（鼠标按键 Code 为负数）

    def __init__(self):
        super().__init__()
        self._Mode = "idle"  # idle / recording / setting_hotkey
        self._HotKeyCode = DefaultHotKeyCode
        self._HotKeyModifiers: list[int] = []
        self._KeyboardListener = None
        self._MouseListener = None
        self._HeldModifiers: set[int] = set()

    def Start(self):
        """启动键盘和鼠标全局监听"""
        self._KeyboardListener = keyboard.Listener(
            on_press=self._OnKeyPress,
            on_release=self._OnKeyRelease,
        )
        self._KeyboardListener.daemon = True
        self._KeyboardListener.start()

        self._MouseListener = mouse.Listener(
            on_click=self._OnMouseClick,
            win32_event_filter=self._OnMouseWin32Event,
        )
        self._MouseListener.daemon = True
        self._MouseListener.start()

    def Stop(self):
        if self._KeyboardListener:
            self._KeyboardListener.stop()
            self._KeyboardListener = None
        if self._MouseListener:
            self._MouseListener.stop()
            self._MouseListener = None

    def StartRecording(self):
        self._Mode = "recording"

    def StopRecording(self):
        self._Mode = "idle"

    def StartSettingHotKey(self):
        self._Mode = "setting_hotkey"

    def SetHotKey(self, Code: int, Modifiers: list[int] = None):
        self._HotKeyCode = Code
        self._HotKeyModifiers = Modifiers or []

    # ── 键盘回调 ──

    def _OnKeyPress(self, Key):
        Code, Name = self._ResolveKey(Key)
        if not Code:
            return

        if Code in _ModNormalize:
            self._HeldModifiers.add(_ModNormalize[Code])
            return

        if self._Mode == "recording":
            Mods = sorted(self._HeldModifiers)
            DisplayName = self._BuildComboName(Mods, Name)
            self.ActionCaptured.emit("Key", Code, DisplayName, Mods)

        elif self._Mode == "setting_hotkey":
            Mods = sorted(self._HeldModifiers)
            DisplayName = self._BuildComboName(Mods, Name)
            self._HotKeyCode = Code
            self._HotKeyModifiers = Mods
            self._Mode = "idle"
            self.HotKeyCaptured.emit(Code, DisplayName, Mods)

        elif self._Mode == "idle":
            if Code == self._HotKeyCode and sorted(self._HeldModifiers) == self._HotKeyModifiers:
                self.HotKeyTriggered.emit()

    def _OnKeyRelease(self, Key):
        Code, _ = self._ResolveKey(Key)
        if Code and Code in _ModNormalize:
            self._HeldModifiers.discard(_ModNormalize[Code])

    # ── 鼠标回调（左/右/中键） ──

    def _OnMouseClick(self, X, Y, Btn, Pressed):
        if not Pressed:
            return
        Result = _MouseButtonMap.get(Btn)
        if not Result:
            return
        Code, Name = Result
        self._HandleMouseButton(Code, Name)

    # ── 鼠标侧键（通过 Win32 原始消息捕获，避免重复） ──

    _WM_XBUTTONDOWN = 0x020B

    def _OnMouseWin32Event(self, Msg, Data):
        if Msg == self._WM_XBUTTONDOWN:
            XBtn = (Data.mouseData >> 16) & 0xFFFF
            Result = _XButtonMap.get(XBtn)
            if Result:
                Code, Name = Result
                self._HandleMouseButton(Code, Name)
        return True

    # ── 鼠标按键统一处理 ──

    def _HandleMouseButton(self, Code: int, Name: str):
        """统一处理鼠标按键（录制/设置快捷键/触发快捷键）"""
        # 快捷键用负数编码
        HotKeyCode = -Code

        if self._Mode == "recording":
            Mods = sorted(self._HeldModifiers)
            DisplayName = self._BuildComboName(Mods, Name)
            self.ActionCaptured.emit("Mouse", Code, DisplayName, Mods)

        elif self._Mode == "setting_hotkey":
            Mods = sorted(self._HeldModifiers)
            DisplayName = self._BuildComboName(Mods, Name)
            self._HotKeyCode = HotKeyCode
            self._HotKeyModifiers = Mods
            self._Mode = "idle"
            self.HotKeyCaptured.emit(HotKeyCode, DisplayName, Mods)

        elif self._Mode == "idle":
            if HotKeyCode == self._HotKeyCode and sorted(self._HeldModifiers) == self._HotKeyModifiers:
                self.HotKeyTriggered.emit()

    # ── 工具方法 ──

    def _BuildComboName(self, Mods: list[int], KeyName: str) -> str:
        Parts = []
        for Vk in Mods:
            if Vk in _ModifierKeys:
                Parts.append(_ModifierKeys[Vk])
        Parts.append(KeyName)
        return "+".join(Parts)

    @staticmethod
    def _ResolveKey(Key):
        try:
            if isinstance(Key, keyboard.Key):
                Vk = getattr(Key.value, "vk", 0) or 0
                Name = Key.name.replace("_", " ").title()
                return Vk, Name
            if isinstance(Key, keyboard.KeyCode):
                Vk = getattr(Key, "vk", 0) or 0
                Name = Key.char.upper() if Key.char else f"VK{Vk}"
                return Vk, Name
        except Exception:
            pass
        return 0, ""
