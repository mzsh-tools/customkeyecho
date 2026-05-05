import random
import time
from threading import Event, Thread

from PySide6.QtCore import QObject, Signal

from Source.Logic import InputDriver, FocusWatcher
from Source.Data.KeyProfile import KeySequence


class KeyPlayer(QObject):
    """多序列并行回放引擎，每个序列独立线程循环执行"""
    StatusChanged = Signal(str)

    def __init__(self):
        super().__init__()
        self._Sequences: list[KeySequence] = []
        self._TargetWindow = ""
        self._StopEvent = Event()
        self._Threads: list[Thread] = []

    def Configure(self, Sequences: list[KeySequence], TargetWindow: str):
        self._Sequences = [s for s in Sequences if s.Actions]
        self._TargetWindow = TargetWindow

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

    def _WaitFocus(self) -> bool:
        """等待目标窗口获得焦点，返回 False 表示窗口关闭或收到停止信号"""
        if not self._TargetWindow or FocusWatcher.IsWindowFocused(self._TargetWindow):
            return True
        if not FocusWatcher.IsWindowExist(self._TargetWindow):
            self._StopEvent.set()
            self.StatusChanged.emit("stopped")
            return False
        self.StatusChanged.emit("paused")
        while not self._StopEvent.is_set() and not FocusWatcher.IsWindowFocused(self._TargetWindow):
            if not FocusWatcher.IsWindowExist(self._TargetWindow):
                self._StopEvent.set()
                self.StatusChanged.emit("stopped")
                return False
            self._StopEvent.wait(0.2)
        if self._StopEvent.is_set():
            return False
        self.StatusChanged.emit("playing")
        return True

    def _PressAction(self, Action):
        """按下 Action 的所有键（不释放）"""
        if Action.Type == "Key":
            for Mod in Action.Modifiers:
                InputDriver.KeyDown(Mod)
                time.sleep(random.uniform(0.010, 0.030))
            InputDriver.KeyDown(Action.Code)
        else:
            InputDriver.MouseDown(Action.Code)

    def _ReleaseAction(self, Action):
        """释放 Action 的所有键（反序）"""
        if Action.Type == "Key":
            InputDriver.KeyUp(Action.Code)
            for Mod in reversed(Action.Modifiers):
                time.sleep(random.uniform(0.010, 0.030))
                InputDriver.KeyUp(Mod)
        else:
            InputDriver.MouseUp(Action.Code)

    def _RunSequence(self, Seq: KeySequence):
        if Seq.DelayMin == 0 and Seq.DelayMax == 0:
            self._RunHoldSequence(Seq)
        else:
            self._RunLoopSequence(Seq)

    def _RunHoldSequence(self, Seq: KeySequence):
        """长按模式：按住第一个 Action 直到停止或失焦"""
        if not Seq.Actions:
            return
        Action = Seq.Actions[0]
        Holding = False
        try:
            while not self._StopEvent.is_set():
                if not self._WaitFocus():
                    return
                if not Holding:
                    self._PressAction(Action)
                    Holding = True
                self._StopEvent.wait(0.1)
                # 失焦时释放，下轮循环重新等待焦点后按下
                if self._TargetWindow and not FocusWatcher.IsWindowFocused(self._TargetWindow):
                    self._ReleaseAction(Action)
                    Holding = False
        finally:
            if Holding:
                self._ReleaseAction(Action)

    def _RunLoopSequence(self, Seq: KeySequence):
        """循环模式：依次发送按键序列并循环"""
        while not self._StopEvent.is_set():
            for Action in Seq.Actions:
                if self._StopEvent.is_set():
                    return
                if not self._WaitFocus():
                    return

                if Action.Type == "Key":
                    if Action.Modifiers:
                        InputDriver.SendKeyCombo(Action.Modifiers, Action.Code)
                    else:
                        InputDriver.SendKey(Action.Code)
                else:
                    InputDriver.SendMouseClick(Action.Code)

                Delay = random.randint(Seq.DelayMin, Seq.DelayMax) / 1000.0
                self._StopEvent.wait(Delay)
