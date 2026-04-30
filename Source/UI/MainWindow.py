from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QMainWindow, QComboBox,
    QListWidget, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from Source.Data.KeyProfile import (
    DefaultDelayMax, DefaultDelayMin, DefaultHotKeyCode,
    DefaultHotKeyName, DelayMinLimit, KeyAction,
)
from Source.Logic.ConfigMgr import ConfigMgr
from Source.Logic import FocusWatcher
from Source.Logic.InputListener import InputListener
from Source.Logic.KeyPlayer import KeyPlayer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CustomKeyEcho - 自定义按键回声")
        self.setMinimumSize(420, 500)

        self._Actions: list[KeyAction] = []
        self._HotKeyCode = DefaultHotKeyCode
        self._HotKeyName = DefaultHotKeyName

        self._Listener = InputListener()
        self._Player = KeyPlayer()

        self._InitUI()
        self._ConnectSignals()
        self._LoadConfig()
        self._RefreshWindows()
        self._Listener.Start()

    # ── UI 构建 ──

    def _InitUI(self):
        Central = QWidget()
        self.setCentralWidget(Central)
        Root = QVBoxLayout(Central)
        Root.setSpacing(10)

        # 目标窗口
        WinGroup = QGroupBox("目标窗口")
        WinLayout = QHBoxLayout()
        self._WindowCombo = QComboBox()
        self._WindowCombo.setEditable(True)
        RefreshBtn = QPushButton("刷新列表")
        RefreshBtn.setFixedWidth(80)
        RefreshBtn.clicked.connect(self._RefreshWindows)
        WinLayout.addWidget(self._WindowCombo, 1)
        WinLayout.addWidget(RefreshBtn)
        WinGroup.setLayout(WinLayout)
        Root.addWidget(WinGroup)

        # 按键序列
        KeyGroup = QGroupBox("按键序列")
        KeyLayout = QVBoxLayout()
        self._KeyList = QListWidget()
        self._KeyList.setMinimumHeight(150)
        KeyLayout.addWidget(self._KeyList)
        BtnRow = QHBoxLayout()
        self._RecordBtn = QPushButton("录制按键")
        DeleteBtn = QPushButton("删除选中")
        ClearBtn = QPushButton("清空")
        DeleteBtn.clicked.connect(self._DeleteSelected)
        ClearBtn.clicked.connect(self._ClearActions)
        BtnRow.addWidget(self._RecordBtn)
        BtnRow.addWidget(DeleteBtn)
        BtnRow.addWidget(ClearBtn)
        KeyLayout.addLayout(BtnRow)
        KeyGroup.setLayout(KeyLayout)
        Root.addWidget(KeyGroup)

        # 按键间隔
        DelayGroup = QGroupBox("按键间隔（每次随机取值，防检测）")
        DelayLayout = QHBoxLayout()
        self._DelayMinSpin = QSpinBox()
        self._DelayMinSpin.setRange(DelayMinLimit, 60000)
        self._DelayMinSpin.setValue(DefaultDelayMin)
        self._DelayMinSpin.setSuffix(" ms")
        self._DelayMaxSpin = QSpinBox()
        self._DelayMaxSpin.setRange(DelayMinLimit, 60000)
        self._DelayMaxSpin.setValue(DefaultDelayMax)
        self._DelayMaxSpin.setSuffix(" ms")
        DelayLayout.addWidget(QLabel("最小"))
        DelayLayout.addWidget(self._DelayMinSpin, 1)
        DelayLayout.addWidget(QLabel("~"))
        DelayLayout.addWidget(self._DelayMaxSpin, 1)
        DelayLayout.addWidget(QLabel("最大"))
        DelayGroup.setLayout(DelayLayout)
        Root.addWidget(DelayGroup)

        # 控制
        CtrlGroup = QGroupBox("控制")
        CtrlLayout = QVBoxLayout()
        HKRow = QHBoxLayout()
        HKRow.addWidget(QLabel("快捷键:"))
        self._HotKeyBtn = QPushButton(self._HotKeyName)
        self._HotKeyBtn.setFixedWidth(120)
        HKRow.addWidget(self._HotKeyBtn)
        HKRow.addStretch()
        CtrlLayout.addLayout(HKRow)
        self._StatusLabel = QLabel("状态: 已停止")
        self._StatusLabel.setStyleSheet("font-size: 14px; font-weight: bold;")
        CtrlLayout.addWidget(self._StatusLabel)
        CtrlGroup.setLayout(CtrlLayout)
        Root.addWidget(CtrlGroup)

    # ── 信号连接 ──

    def _ConnectSignals(self):
        self._RecordBtn.clicked.connect(self._ToggleRecording)
        self._HotKeyBtn.clicked.connect(self._StartSettingHotKey)
        self._Listener.ActionCaptured.connect(self._OnActionCaptured)
        self._Listener.RecordingStopped.connect(self._OnRecordingStopped)
        self._Listener.HotKeyTriggered.connect(self._TogglePlayback)
        self._Listener.HotKeyCaptured.connect(self._OnHotKeyCaptured)
        self._Player.StatusChanged.connect(self._OnStatusChanged)
        self._DelayMinSpin.valueChanged.connect(self._OnDelayMinChanged)
        self._DelayMaxSpin.valueChanged.connect(self._OnDelayMaxChanged)

    # ── 窗口列表 ──

    def _RefreshWindows(self):
        CurText = self._WindowCombo.currentText()
        self._WindowCombo.clear()
        self._WindowCombo.addItems(FocusWatcher.ListWindows())
        if CurText:
            Idx = self._WindowCombo.findText(CurText)
            if Idx >= 0:
                self._WindowCombo.setCurrentIndex(Idx)
            else:
                self._WindowCombo.setEditText(CurText)

    # ── 按键录制 ──

    def _ToggleRecording(self):
        if self._Listener._Mode == "recording":
            self._Listener.StopRecording()
            self._OnRecordingStopped()
        else:
            self._RecordBtn.setText("录制中... (按回车结束)")
            self._Listener.StartRecording()

    def _OnActionCaptured(self, Type, Code, Name):
        Action = KeyAction(Type=Type, Code=Code, Name=Name)
        self._Actions.append(Action)
        self._KeyList.addItem(f"{len(self._Actions)}. {Name}")

    def _OnRecordingStopped(self):
        self._RecordBtn.setText("录制按键")
        self._SaveConfig()

    def _DeleteSelected(self):
        Idx = self._KeyList.currentRow()
        if Idx >= 0:
            self._Actions.pop(Idx)
            self._RefreshKeyList()

    def _ClearActions(self):
        self._Actions.clear()
        self._KeyList.clear()

    def _RefreshKeyList(self):
        self._KeyList.clear()
        for I, Action in enumerate(self._Actions, 1):
            self._KeyList.addItem(f"{I}. {Action.Name}")

    # ── 快捷键设置 ──

    def _StartSettingHotKey(self):
        self._HotKeyBtn.setText("请按下快捷键...")
        self._Listener.StartSettingHotKey()

    def _OnHotKeyCaptured(self, Code, Name):
        self._HotKeyCode = Code
        self._HotKeyName = Name
        self._HotKeyBtn.setText(Name)
        self._SaveConfig()

    # ── 回放控制 ──

    def _TogglePlayback(self):
        if self._Player.isRunning():
            self._Player.Stop()
        elif self._Actions:
            self._Player.Configure(
                self._Actions,
                self._DelayMinSpin.value(),
                self._DelayMaxSpin.value(),
                self._WindowCombo.currentText(),
            )
            self._Player.start()

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
            self._DelayMaxSpin.setValue(Value)

    def _OnDelayMaxChanged(self, Value):
        if self._DelayMinSpin.value() > Value:
            self._DelayMinSpin.setValue(Value)

    # ── 配置持久化 ──

    def _SaveConfig(self):
        Cfg = ConfigMgr()
        Cfg.Set("Actions", [{"Type": A.Type, "Code": A.Code, "Name": A.Name} for A in self._Actions])
        Cfg.Set("Delay.Min", self._DelayMinSpin.value())
        Cfg.Set("Delay.Max", self._DelayMaxSpin.value())
        Cfg.Set("HotKey.Code", self._HotKeyCode)
        Cfg.Set("HotKey.Name", self._HotKeyName)
        Cfg.Set("TargetWindow", self._WindowCombo.currentText())
        Cfg.Save()

    def _LoadConfig(self):
        Cfg = ConfigMgr()
        Actions = Cfg.Get("Actions", [])
        self._Actions = [KeyAction(**A) for A in Actions]
        self._RefreshKeyList()
        self._DelayMinSpin.setValue(Cfg.Get("Delay.Min", DefaultDelayMin))
        self._DelayMaxSpin.setValue(Cfg.Get("Delay.Max", DefaultDelayMax))
        self._HotKeyCode = Cfg.Get("HotKey.Code", DefaultHotKeyCode)
        self._HotKeyName = Cfg.Get("HotKey.Name", DefaultHotKeyName)
        self._HotKeyBtn.setText(self._HotKeyName)
        self._Listener.SetHotKeyCode(self._HotKeyCode)
        Target = Cfg.Get("TargetWindow", "")
        if Target:
            self._WindowCombo.setEditText(Target)

    # ── 关闭清理 ──

    def closeEvent(self, Event):
        self._Listener.Stop()
        if self._Player.isRunning():
            self._Player.Stop()
            self._Player.wait(2000)
        self._SaveConfig()
        Event.accept()
