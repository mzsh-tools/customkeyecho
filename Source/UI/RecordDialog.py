from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout


class RecordDialog(QDialog):
    """录制弹窗：鼠标在区域内时录制按键，移出暂停，用户手动关闭"""
    RecordingStarted = Signal()
    RecordingStopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("录制按键")
        self.setFixedSize(300, 150)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)
        self.setMouseTracking(True)

        self._Active = False

        Layout = QVBoxLayout(self)
        Layout.setContentsMargins(20, 20, 20, 20)
        self._Label = QLabel("鼠标在此区域内时录制按键\n移出暂停，关闭窗口结束")
        self._Label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._Label.setStyleSheet("font-size: 14px;")
        self._Label.setMouseTracking(True)
        Layout.addWidget(self._Label)

    def showEvent(self, Event):
        super().showEvent(Event)
        if self.underMouse():
            self._SetActive(True)

    def enterEvent(self, Event):
        self._SetActive(True)
        super().enterEvent(Event)

    def leaveEvent(self, Event):
        self._SetActive(False)
        super().leaveEvent(Event)

    def closeEvent(self, Event):
        if self._Active:
            self._SetActive(False)
        self.RecordingStopped.emit()
        super().closeEvent(Event)

    def _SetActive(self, Active: bool):
        if Active == self._Active:
            return
        self._Active = Active
        if Active:
            self._Label.setText("录制中...")
            self._Label.setStyleSheet("font-size: 14px; color: #00b4ff; font-weight: bold;")
            self.RecordingStarted.emit()
        else:
            self._Label.setText("已暂停（鼠标移入继续）")
            self._Label.setStyleSheet("font-size: 14px; color: gray;")
            self.RecordingStopped.emit()

    def IsActive(self) -> bool:
        return self._Active


class HotKeyDialog(QDialog):
    """快捷键设置弹窗：鼠标在区域内时按下任意键设为快捷键"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置快捷键")
        self.setFixedSize(300, 150)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)
        self.setMouseTracking(True)

        self._Active = False

        Layout = QVBoxLayout(self)
        Layout.setContentsMargins(20, 20, 20, 20)
        self._Label = QLabel("鼠标移入此区域\n然后按下要设为快捷键的按键")
        self._Label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._Label.setStyleSheet("font-size: 14px;")
        self._Label.setMouseTracking(True)
        Layout.addWidget(self._Label)

    def showEvent(self, Event):
        super().showEvent(Event)
        if self.underMouse():
            self._SetActive(True)

    def enterEvent(self, Event):
        self._SetActive(True)
        super().enterEvent(Event)

    def leaveEvent(self, Event):
        self._SetActive(False)
        super().leaveEvent(Event)

    def _SetActive(self, Active: bool):
        if Active == self._Active:
            return
        self._Active = Active
        if Active:
            self._Label.setText("请按下快捷键...")
            self._Label.setStyleSheet("font-size: 14px; color: #00b4ff; font-weight: bold;")
        else:
            self._Label.setText("鼠标移入此区域\n然后按下要设为快捷键的按键")
            self._Label.setStyleSheet("font-size: 14px;")

    def OnCaptured(self):
        self.accept()

    def IsActive(self) -> bool:
        return self._Active
