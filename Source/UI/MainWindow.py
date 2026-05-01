from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QGroupBox, QHBoxLayout, QLabel, QListWidgetItem,
    QMainWindow, QComboBox, QListWidget, QMenu, QPushButton, QSpinBox,
    QSystemTrayIcon, QVBoxLayout, QWidget,
)

from Source.Data.KeyProfile import (
    DefaultDelayMax, DefaultDelayMin, DefaultHotKeyCode,
    DefaultHotKeyName, DelayMinLimit, KeyAction, KeySequence,
)
from Source.Logic.ConfigMgr import ConfigMgr
from Source.Logic import FocusWatcher
from Source.Logic.InputListener import InputListener
from Source.Logic.KeyPlayer import KeyPlayer
from Source.UI.RecordDialog import RecordDialog, HotKeyDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CustomKeyEcho - 自定义按键回声")
        self.setMinimumSize(500, 620)
        IconPath = Path(__file__).resolve().parent.parent.parent / "Assets" / "icon.png"
        if IconPath.exists():
            self.setWindowIcon(QIcon(str(IconPath)))

        self._Sequences: list[KeySequence] = []
        self._TargetWindow = ""
        self._HotKeyCode = DefaultHotKeyCode
        self._HotKeyName = DefaultHotKeyName
        self._HotKeyModifiers: list[int] = []

        self._Listener = InputListener()
        self._Player = KeyPlayer()

        self._ReallyQuit = False

        self._InitUI()
        self._InitTray()
        self._RefreshWindows()
        self._LoadConfig()
        self._ConnectSignals()
        self._Listener.Start()

    def show(self):
        if self._AutoHideCheck.isChecked():
            self.hide()
        else:
            super().show()

    # ── UI 构建 ──

    def _InitUI(self):
        Central = QWidget()
        self.setCentralWidget(Central)
        Root = QVBoxLayout(Central)
        Root.setSpacing(10)

        # 通用设置（最上方）
        GeneralGroup = QGroupBox("通用设置")
        GeneralLayout = QVBoxLayout()

        # 目标窗口
        WinRow = QHBoxLayout()
        WinRow.addWidget(QLabel("目标窗口:"))
        self._WindowCombo = QComboBox()
        self._WindowCombo.setEditable(False)
        RefreshBtn = QPushButton("刷新")
        RefreshBtn.setFixedWidth(60)
        RefreshBtn.clicked.connect(self._RefreshWindows)
        WinRow.addWidget(self._WindowCombo, 1)
        WinRow.addWidget(RefreshBtn)
        GeneralLayout.addLayout(WinRow)

        # 快捷键
        HKRow = QHBoxLayout()
        HKRow.addWidget(QLabel("快捷键:"))
        self._HotKeyBtn = QPushButton(self._HotKeyName)
        self._HotKeyBtn.setFixedWidth(150)
        HKRow.addWidget(self._HotKeyBtn)
        HKRow.addStretch()
        GeneralLayout.addLayout(HKRow)


        # 启动后自动隐藏到托盘
        self._AutoHideCheck = QCheckBox("启动后自动隐藏到托盘")
        GeneralLayout.addWidget(self._AutoHideCheck)

        GeneralGroup.setLayout(GeneralLayout)
        Root.addWidget(GeneralGroup)

        # 序列列表
        SeqGroup = QGroupBox("按键序列列表（各行独立并行执行）")
        SeqLayout = QVBoxLayout()
        self._SeqList = QListWidget()
        self._SeqList.setMinimumHeight(120)
        self._SeqList.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._SeqList.setDefaultDropAction(Qt.DropAction.MoveAction)
        SeqLayout.addWidget(self._SeqList)
        SeqBtnRow = QHBoxLayout()
        AddSeqBtn = QPushButton("添加序列")
        DelSeqBtn = QPushButton("删除选中")
        AddSeqBtn.clicked.connect(self._AddSequence)
        DelSeqBtn.clicked.connect(self._DeleteSequence)
        SeqBtnRow.addWidget(AddSeqBtn)
        SeqBtnRow.addWidget(DelSeqBtn)
        SeqBtnRow.addStretch()
        SeqLayout.addLayout(SeqBtnRow)
        SeqGroup.setLayout(SeqLayout)
        Root.addWidget(SeqGroup)

        # 序列详情编辑区
        DetailGroup = QGroupBox("序列详情（选中上方序列后编辑）")
        DetailLayout = QVBoxLayout()

        self._KeyList = QListWidget()
        self._KeyList.setMinimumHeight(100)
        DetailLayout.addWidget(self._KeyList)
        KeyBtnRow = QHBoxLayout()
        self._RecordBtn = QPushButton("录制按键")
        DeleteKeyBtn = QPushButton("删除选中按键")
        ClearKeyBtn = QPushButton("清空按键")
        DeleteKeyBtn.clicked.connect(self._DeleteSelectedKey)
        ClearKeyBtn.clicked.connect(self._ClearKeys)
        KeyBtnRow.addWidget(self._RecordBtn)
        KeyBtnRow.addWidget(DeleteKeyBtn)
        KeyBtnRow.addWidget(ClearKeyBtn)
        DetailLayout.addLayout(KeyBtnRow)

        DelayLayout = QHBoxLayout()
        self._DelayMinSpin = QSpinBox()
        self._DelayMinSpin.setRange(DelayMinLimit, 60000)
        self._DelayMinSpin.setValue(DefaultDelayMin)
        self._DelayMinSpin.setKeyboardTracking(False)
        self._DelayMaxSpin = QSpinBox()
        self._DelayMaxSpin.setRange(DelayMinLimit, 60000)
        self._DelayMaxSpin.setValue(DefaultDelayMax)
        self._DelayMaxSpin.setKeyboardTracking(False)
        DelayLayout.addWidget(QLabel("间隔"))
        DelayLayout.addWidget(self._DelayMinSpin, 1)
        DelayLayout.addWidget(QLabel("~"))
        DelayLayout.addWidget(self._DelayMaxSpin, 1)
        DelayLayout.addWidget(QLabel("ms"))
        DetailLayout.addLayout(DelayLayout)

        DetailGroup.setLayout(DetailLayout)
        Root.addWidget(DetailGroup)

        # 状态
        self._StatusLabel = QLabel("状态: 已停止")
        self._StatusLabel.setStyleSheet("font-size: 14px; font-weight: bold;")
        Root.addWidget(self._StatusLabel)

    # ── 系统托盘 ──

    def _InitTray(self):
        self._Tray = QSystemTrayIcon(self)
        self._Tray.setIcon(self.windowIcon() or QIcon())
        self._Tray.setToolTip("CustomKeyEcho")

        TrayMenu = QMenu()
        ShowAction = QAction("显示窗口", self)
        ShowAction.triggered.connect(self._ShowFromTray)
        QuitAction = QAction("退出", self)
        QuitAction.triggered.connect(self._QuitApp)
        TrayMenu.addAction(ShowAction)
        TrayMenu.addSeparator()
        TrayMenu.addAction(QuitAction)

        self._Tray.setContextMenu(TrayMenu)
        self._Tray.activated.connect(self._OnTrayActivated)
        self._Tray.show()

    def _OnTrayActivated(self, Reason):
        if Reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._ShowFromTray()

    def _ShowFromTray(self):
        self.showNormal()
        self.activateWindow()

    def _QuitApp(self):
        self._ReallyQuit = True
        self.close()

    # ── 信号连接 ──

    def _ConnectSignals(self):
        self._RecordBtn.clicked.connect(self._ToggleRecording)
        self._HotKeyBtn.clicked.connect(self._StartSettingHotKey)
        self._Listener.ActionCaptured.connect(self._OnActionCaptured)
        self._Listener.HotKeyTriggered.connect(self._TogglePlayback)
        self._Player.StatusChanged.connect(self._OnStatusChanged)
        self._DelayMinSpin.valueChanged.connect(self._OnDelayMinChanged)
        self._DelayMaxSpin.valueChanged.connect(self._OnDelayMaxChanged)
        self._SeqList.currentRowChanged.connect(self._OnSeqSelected)
        self._SeqList.model().rowsMoved.connect(self._OnSeqReordered)
        self._WindowCombo.currentIndexChanged.connect(self._OnTargetWindowChanged)

    # ── 窗口列表 ──

    def _RefreshWindows(self):
        CurIdx = self._WindowCombo.currentIndex()
        CurText = self._WindowCombo.currentText()
        self._WindowCombo.clear()
        self._WindowCombo.addItem("(不检测焦点)", "")
        self._WindowCombo.addItems(FocusWatcher.ListWindows())
        if CurText and CurIdx > 0:
            Idx = self._WindowCombo.findText(CurText)
            if Idx >= 0:
                self._WindowCombo.setCurrentIndex(Idx)

    # ── 序列列表管理 ──

    def _AddSequence(self):
        Seq = KeySequence()
        self._Sequences.append(Seq)
        self._RefreshSeqList()
        self._SeqList.setCurrentRow(len(self._Sequences) - 1)
        self._SaveConfig()

    def _DeleteSequence(self):
        Idx = self._SeqList.currentRow()
        if Idx < 0:
            return
        self._Sequences.pop(Idx)
        self._RefreshSeqList()
        self._RefreshDetail()
        self._SaveConfig()

    def _OnSeqSelected(self, Idx):
        self._RefreshDetail()

    def _OnSeqReordered(self):
        # 按 item 存储的原始索引重建顺序
        OldSeqs = list(self._Sequences)
        self._Sequences = [
            OldSeqs[self._SeqList.item(I).data(Qt.ItemDataRole.UserRole)]
            for I in range(self._SeqList.count())
            if self._SeqList.item(I).data(Qt.ItemDataRole.UserRole) < len(OldSeqs)
        ]
        self._RefreshSeqList()
        self._SaveConfig()

    def _RefreshSeqList(self):
        self._SeqList.blockSignals(True)
        Cur = self._SeqList.currentRow()
        self._SeqList.clear()
        for I, Seq in enumerate(self._Sequences):
            Item = QListWidgetItem(Seq.DisplayName())
            Item.setData(Qt.ItemDataRole.UserRole, I)
            self._SeqList.addItem(Item)
        if 0 <= Cur < len(self._Sequences):
            self._SeqList.setCurrentRow(Cur)
        self._SeqList.blockSignals(False)

    def _UpdateCurrentSeqDisplay(self):
        Idx = self._SeqList.currentRow()
        if 0 <= Idx < len(self._Sequences):
            self._SeqList.item(Idx).setText(self._Sequences[Idx].DisplayName())

    # ── 序列详情编辑 ──

    def _CurrentSeq(self) -> KeySequence | None:
        Idx = self._SeqList.currentRow()
        if 0 <= Idx < len(self._Sequences):
            return self._Sequences[Idx]
        return None

    def _RefreshDetail(self):
        Seq = self._CurrentSeq()
        self._KeyList.clear()
        if Seq is None:
            self._DelayMinSpin.setValue(DefaultDelayMin)
            self._DelayMaxSpin.setValue(DefaultDelayMax)
            return
        for I, Action in enumerate(Seq.Actions, 1):
            self._KeyList.addItem(f"{I}. {Action.Name}")
        self._DelayMinSpin.blockSignals(True)
        self._DelayMaxSpin.blockSignals(True)
        self._DelayMinSpin.setValue(Seq.DelayMin)
        self._DelayMaxSpin.setValue(Seq.DelayMax)
        self._DelayMinSpin.blockSignals(False)
        self._DelayMaxSpin.blockSignals(False)

    # ── 按键录制 ──

    def _ToggleRecording(self):
        if self._CurrentSeq() is None:
            self._AddSequence()
        self._RecordDlg = RecordDialog(parent=self)
        self._RecordDlg.RecordingStarted.connect(self._Listener.StartRecording)
        self._RecordDlg.RecordingStopped.connect(self._Listener.StopRecording)
        self._RecordDlg.exec()
        self._RecordDlg = None
        self._Listener.StopRecording()
        self._SaveConfig()

    def _OnActionCaptured(self, Type, Code, Name, Modifiers):
        # 只在录制弹窗激活（鼠标在区域内）时才记录
        if hasattr(self, "_RecordDlg") and self._RecordDlg and not self._RecordDlg.IsActive():
            return
        Seq = self._CurrentSeq()
        if Seq is None:
            return
        Action = KeyAction(Type=Type, Code=Code, Name=Name, Modifiers=Modifiers)
        Seq.Actions.append(Action)
        self._KeyList.addItem(f"{len(Seq.Actions)}. {Name}")
        self._UpdateCurrentSeqDisplay()

    def _DeleteSelectedKey(self):
        Seq = self._CurrentSeq()
        if Seq is None:
            return
        Idx = self._KeyList.currentRow()
        if Idx >= 0:
            Seq.Actions.pop(Idx)
            self._RefreshDetail()
            self._UpdateCurrentSeqDisplay()
            self._SaveConfig()

    def _ClearKeys(self):
        Seq = self._CurrentSeq()
        if Seq is None:
            return
        Seq.Actions.clear()
        self._KeyList.clear()
        self._UpdateCurrentSeqDisplay()
        self._SaveConfig()

    # ── 快捷键设置 ──

    def _StartSettingHotKey(self):
        Dlg = HotKeyDialog(parent=self)
        self._HotKeyDlg = Dlg
        self._Listener.StartSettingHotKey()
        self._Listener.HotKeyCaptured.connect(self._OnHotKeyCapturedWithDlg)
        Dlg.exec()
        self._Listener.HotKeyCaptured.disconnect(self._OnHotKeyCapturedWithDlg)
        self._HotKeyDlg = None
        # 如果弹窗关闭时未捕获到快捷键，恢复 idle
        if self._Listener._Mode == "setting_hotkey":
            self._Listener._Mode = "idle"

    def _OnHotKeyCapturedWithDlg(self, Code, Name, Modifiers):
        if self._HotKeyDlg and self._HotKeyDlg.IsActive():
            self._HotKeyCode = Code
            self._HotKeyName = Name
            self._HotKeyModifiers = Modifiers
            self._HotKeyBtn.setText(Name)
            self._SaveConfig()
            self._HotKeyDlg.OnCaptured()

    # ── 回放控制 ──

    def _GetTargetWindow(self) -> str:
        return self._TargetWindow

    def _OnTargetWindowChanged(self, Idx):
        Data = self._WindowCombo.itemData(Idx)
        if Data is not None:
            self._TargetWindow = Data
        else:
            self._TargetWindow = self._WindowCombo.itemText(Idx)
        self._SaveConfig()

    def _TogglePlayback(self):
        # 快捷键仅在目标窗口焦点时生效
        Target = self._GetTargetWindow()
        if Target and not FocusWatcher.IsWindowFocused(Target):
            return

        if self._Player.IsRunning():
            self._Player.Stop()
        elif self._Sequences:
            self._Player.Configure(self._Sequences, Target)
            self._Player.Start()

    def _OnStatusChanged(self, Status):
        Map = {
            "playing": "状态: 运行中",
            "paused": "状态: 已暂停（等待窗口焦点）",
            "stopped": "状态: 已停止",
        }
        self._StatusLabel.setText(Map.get(Status, Status))

    # ── 延迟校验 ──

    def _OnDelayMinChanged(self, Value):
        if self._DelayMaxSpin.value() < Value:
            self._DelayMaxSpin.blockSignals(True)
            self._DelayMaxSpin.setValue(Value)
            self._DelayMaxSpin.blockSignals(False)
        Seq = self._CurrentSeq()
        if Seq:
            Seq.DelayMin = Value
            Seq.DelayMax = self._DelayMaxSpin.value()
            self._UpdateCurrentSeqDisplay()
            self._SaveConfig()

    def _OnDelayMaxChanged(self, Value):
        if self._DelayMinSpin.value() > Value:
            self._DelayMinSpin.blockSignals(True)
            self._DelayMinSpin.setValue(Value)
            self._DelayMinSpin.blockSignals(False)
        Seq = self._CurrentSeq()
        if Seq:
            Seq.DelayMax = Value
            Seq.DelayMin = self._DelayMinSpin.value()
            self._UpdateCurrentSeqDisplay()
            self._SaveConfig()

    # ── 配置持久化 ──

    def _SaveConfig(self):
        Cfg = ConfigMgr()
        Cfg.Set("Sequences", [S.ToDict() for S in self._Sequences])
        Cfg.Set("HotKey.Code", self._HotKeyCode)
        Cfg.Set("HotKey.Name", self._HotKeyName)
        Cfg.Set("HotKey.Modifiers", self._HotKeyModifiers)
        Cfg.Set("AutoHide", self._AutoHideCheck.isChecked())
        Cfg.Set("TargetWindow", self._TargetWindow)
        Cfg.Save()

    def _LoadConfig(self):
        Cfg = ConfigMgr()
        SeqData = Cfg.Get("Sequences", [])
        # 兼容旧格式：旧版用 "Actions" 扁平列表 + "Delay.Min/Max"
        if not SeqData:
            OldActions = Cfg.Get("Actions", [])
            if OldActions:
                SeqData = [{
                    "Actions": OldActions,
                    "DelayMin": Cfg.Get("Delay.Min", DefaultDelayMin),
                    "DelayMax": Cfg.Get("Delay.Max", DefaultDelayMax),
                }]
        self._Sequences = [KeySequence.FromDict(D) for D in SeqData]
        self._RefreshSeqList()
        self._HotKeyCode = Cfg.Get("HotKey.Code", DefaultHotKeyCode)
        self._HotKeyName = Cfg.Get("HotKey.Name", DefaultHotKeyName)
        self._HotKeyModifiers = Cfg.Get("HotKey.Modifiers", [])
        self._HotKeyBtn.setText(self._HotKeyName)
        self._Listener.SetHotKey(self._HotKeyCode, self._HotKeyModifiers)
        self._AutoHideCheck.setChecked(Cfg.Get("AutoHide", False))
        self._TargetWindow = Cfg.Get("TargetWindow", "")
        if self._TargetWindow:
            Idx = self._WindowCombo.findText(self._TargetWindow)
            if Idx >= 0:
                self._WindowCombo.setCurrentIndex(Idx)
            else:
                # 窗口当前不存在（如游戏未开），追加到列表显示
                self._WindowCombo.addItem(self._TargetWindow)
                self._WindowCombo.setCurrentIndex(self._WindowCombo.count() - 1)

    # ── 关闭清理 ──

    def closeEvent(self, Event):
        if not self._ReallyQuit:
            Event.ignore()
            self.hide()
            return
        self._Listener.Stop()
        if self._Player.IsRunning():
            self._Player.Stop()
        self._SaveConfig()
        self._Tray.hide()
        Event.accept()
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()
