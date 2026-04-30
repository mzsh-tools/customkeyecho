import random
from threading import Event

from PySide6.QtCore import QThread, Signal

from Source.Logic import InputDriver, FocusWatcher
from Source.Data.KeyProfile import DefaultDelayMin, DefaultDelayMax


class KeyPlayer(QThread):
    StatusChanged = Signal(str)

    def __init__(self):
        super().__init__()
        self._Actions = []
        self._DelayMin = DefaultDelayMin
        self._DelayMax = DefaultDelayMax
        self._TargetWindow = ""
        self._StopEvent = Event()

    def Configure(self, Actions, DelayMin, DelayMax, TargetWindow):
        self._Actions = list(Actions)
        self._DelayMin = DelayMin
        self._DelayMax = DelayMax
        self._TargetWindow = TargetWindow

    def run(self):
        if not self._Actions:
            self.StatusChanged.emit("stopped")
            return

        self._StopEvent.clear()
        self.StatusChanged.emit("playing")
        Paused = False

        while not self._StopEvent.is_set():
            for Action in self._Actions:
                if self._StopEvent.is_set():
                    break

                # 焦点检测
                if self._TargetWindow and not FocusWatcher.IsWindowFocused(self._TargetWindow):
                    if not Paused:
                        self.StatusChanged.emit("paused")
                        Paused = True
                    while not self._StopEvent.is_set() and not FocusWatcher.IsWindowFocused(self._TargetWindow):
                        self._StopEvent.wait(0.2)
                    if self._StopEvent.is_set():
                        break
                    self.StatusChanged.emit("playing")
                    Paused = False

                # 发送按键
                if Action.Type == "Key":
                    InputDriver.SendKey(Action.Code)
                else:
                    InputDriver.SendMouseClick(Action.Code)

                # 随机延迟
                Delay = random.randint(self._DelayMin, self._DelayMax) / 1000.0
                self._StopEvent.wait(Delay)

        self.StatusChanged.emit("stopped")

    def Stop(self):
        self._StopEvent.set()
