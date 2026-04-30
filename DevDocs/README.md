# CustomKeyEcho - 开发文档

## 项目大纲

游戏用按键宏工具。用户录制一组键盘/鼠标按键序列，设定随机延迟区间，通过快捷键启停循环回放。支持窗口焦点检测，焦点丢失自动暂停。

技术栈：Python 3.12 + PySide6 + pynput + ctypes（Win32 API）

三层架构：UI（PySide6）/ Logic（回放引擎、输入驱动、全局监听、焦点检测）/ Data（数据模型）

```
Source/
├── Data/KeyProfile.py        # 数据模型 + 常量
├── Logic/
│   ├── ConfigMgr.py          # 配置持久化
│   ├── InputDriver.py        # SendInput 封装
│   ├── InputListener.py      # pynput 全局监听
│   ├── FocusWatcher.py       # 窗口焦点检测
│   └── KeyPlayer.py          # 回放引擎
└── UI/MainWindow.py          # 主窗口
```

## 功能进度

| 功能 | 状态 | 说明 |
|------|------|------|
| 按键录制与序列管理 | ✅ 完成 | [设计](按键回放/设计.md) |
| 循环回放引擎 | ✅ 完成 | [设计](按键回放/设计.md) |
| 随机延迟 | ✅ 完成 | [设计](按键回放/设计.md) |
| 窗口焦点检测 | ✅ 完成 | [设计](焦点检测/设计.md) |
| SendInput 驱动输入 | ✅ 完成 | [设计](输入驱动/设计.md) |
| 配置持久化 | ✅ 完成 | ConfigMgr 单例模板 |
| GUI | ✅ 完成 | PySide6 MainWindow |
| Interception 驱动级输入 | ⏳ 待开始 | 作为 SendInput 的升级方案，应对内核级反作弊 |

## 当前任务

- [ ] 实际游戏测试验证
- [ ] 打包为可执行文件（PyInstaller）
- [ ] 考虑 Interception 驱动支持

## 阻塞与待讨论

| 事项 | 类型 | 说明 |
|------|------|------|
| 回车键无法录入序列 | ❓ 待讨论 | 回车用于结束录制，如需录入回车需换用其他结束键（如 Esc）或增加 UI 手动添加按键功能 |
| 内核级反作弊拦截 SendInput | ❓ 待讨论 | 部分游戏（EAC/BattlEye）会拦截 SendInput，需 Interception 驱动方案 |
