import random
from threading import Event, Thread

from PySide6.QtCore import QObject, Signal

from Source.Logic import InputDriver, FocusWatcher
from Source.Data.KeyProfile import DefaultComboDelayMin, DefaultComboDelayMax, KeySequence


class KeyPlayer(QObject):
    """多序列并行回放引擎，每个序列独立线程循环执行"""
    StatusChanged = Signal(str)

    def __init__(self):
        super().__init__()
        self._Sequences: list[KeySequence] = []
        self._TargetWindow = ""
        self._ComboDelayMin = DefaultComboDelayMin
        self._ComboDelayMax = DefaultComboDelayMax
        self._StopEvent = Event()
        self._Threads: list[Thread] = []

    def Configure(self, Sequences: list[KeySequence], TargetWindow: str,
                  ComboDelayMin: int = DefaultComboDelayMin, ComboDelayMax: int = DefaultComboDelayMax):
        self._Sequences = [s for s in Sequences if s.Actions]
        self._TargetWindow = TargetWindow
        self._ComboDelayMin = ComboDelayMin
        self._ComboDelayMax = ComboDelayMax

    def Start(self):
        if not self._Sequences:
            return
        self._StopEvent.clear()
        self._Threads.clear()
        for Seq in self._Sequences:
            T = Thread(target=self._RunSequence, args=(Seq,), daemon=True)
            self._Threads.append(T)
            T.start()
        self.StatusChanged.emit("playing")

    def Stop(self):
        self._StopEvent.set()
        for T in self._Threads:
            T.join(timeout=2)
        self._Threads.clear()
        self.StatusChanged.emit("stopped")

    def IsRunning(self) -> bool:
        return any(T.is_alive() for T in self._Threads)

    def _RunSequence(self, Seq: KeySequence):
        Paused = False
        ComboMinSec = self._ComboDelayMin / 1000.0
        ComboMaxSec = self._ComboDelayMax / 1000.0

        while not self._StopEvent.is_set():
            for Action in Seq.Actions:
                if self._StopEvent.is_set():
                    return

                # 焦点检测
                if self._TargetWindow and not FocusWatcher.IsWindowFocused(self._TargetWindow):
                    # 目标窗口已关闭 → 自动停止所有序列
                    if not FocusWatcher.IsWindowExist(self._TargetWindow):
                        self._StopEvent.set()
                        self.StatusChanged.emit("stopped")
                        return
                    if not Paused:
                        self.StatusChanged.emit("paused")
                        Paused = True
                    while not self._StopEvent.is_set() and not FocusWatcher.IsWindowFocused(self._TargetWindow):
                        if not FocusWatcher.IsWindowExist(self._TargetWindow):
                            self._StopEvent.set()
                            self.StatusChanged.emit("stopped")
                            return
                        self._StopEvent.wait(0.2)
                    if self._StopEvent.is_set():
                        return
                    if Paused:
                        self.StatusChanged.emit("playing")
                        Paused = False

                # 发送按键
                if Action.Type == "Key":
                    if Action.Modifiers:
                        InputDriver.SendKeyCombo(Action.Modifiers, Action.Code, ComboMinSec, ComboMaxSec)
                    else:
                        InputDriver.SendKey(Action.Code)
                else:
                    InputDriver.SendMouseClick(Action.Code)

                # 随机延迟
                Delay = random.randint(Seq.DelayMin, Seq.DelayMax) / 1000.0
                self._StopEvent.wait(Delay)
