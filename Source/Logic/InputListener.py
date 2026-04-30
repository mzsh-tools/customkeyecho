from pynput import keyboard, mouse
from PySide6.QtCore import QObject, Signal

from Source.Data.KeyProfile import DefaultHotKeyCode


class InputListener(QObject):
    ActionCaptured = Signal(str, int, str)
    RecordingStopped = Signal()
    HotKeyTriggered = Signal()
    HotKeyCaptured = Signal(int, str)

    def __init__(self):
        super().__init__()
        self._Mode = "idle"  # idle / recording / setting_hotkey
        self._HotKeyCode = DefaultHotKeyCode
        self._KeyboardListener = None
        self._MouseListener = None

    def Start(self):
        """启动全局键盘监听"""
        self._KeyboardListener = keyboard.Listener(on_press=self._OnKeyPress)
        self._KeyboardListener.daemon = True
        self._KeyboardListener.start()

    def Stop(self):
        if self._KeyboardListener:
            self._KeyboardListener.stop()
            self._KeyboardListener = None
        self._StopMouseListener()

    def StartRecording(self):
        self._Mode = "recording"
        self._MouseListener = mouse.Listener(on_click=self._OnMouseClick)
        self._MouseListener.daemon = True
        self._MouseListener.start()

    def StopRecording(self):
        self._Mode = "idle"
        self._StopMouseListener()

    def StartSettingHotKey(self):
        self._Mode = "setting_hotkey"

    def SetHotKeyCode(self, Code: int):
        self._HotKeyCode = Code

    def _StopMouseListener(self):
        if self._MouseListener:
            self._MouseListener.stop()
            self._MouseListener = None

    def _OnKeyPress(self, Key):
        Code, Name = self._ResolveKey(Key)
        if not Code:
            return

        if self._Mode == "recording":
            if Key == keyboard.Key.enter:
                self.StopRecording()
                self.RecordingStopped.emit()
                return
            self.ActionCaptured.emit("Key", Code, Name)

        elif self._Mode == "setting_hotkey":
            self._HotKeyCode = Code
            self._Mode = "idle"
            self.HotKeyCaptured.emit(Code, Name)

        elif self._Mode == "idle" and Code == self._HotKeyCode:
            self.HotKeyTriggered.emit()

    def _OnMouseClick(self, X, Y, Btn, Pressed):
        if not Pressed or self._Mode != "recording":
            return
        Code, Name = self._ResolveMouseButton(Btn)
        if Code:
            self.ActionCaptured.emit("Mouse", Code, Name)

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

    @staticmethod
    def _ResolveMouseButton(Btn):
        Map = {
            mouse.Button.left: (1, "鼠标左键"),
            mouse.Button.right: (2, "鼠标右键"),
            mouse.Button.middle: (3, "鼠标中键"),
        }
        if hasattr(mouse.Button, "x1"):
            Map[mouse.Button.x1] = (4, "鼠标侧键1")
        if hasattr(mouse.Button, "x2"):
            Map[mouse.Button.x2] = (5, "鼠标侧键2")
        return Map.get(Btn, (0, ""))
