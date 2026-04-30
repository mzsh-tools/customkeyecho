"""CustomKeyEcho 功能测试脚本

测试项：
1. 配置管理器 - 读写持久化
2. 窗口焦点检测 - 枚举窗口 / 焦点判断
3. 输入驱动 - SendInput 结构体构建
4. 按键数据模型 - 序列化 / 反序列化
"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def TestKeyProfile():
    print("=== 测试 KeyProfile ===")
    from Source.Data.KeyProfile import KeyAction, DefaultDelayMin, DefaultDelayMax, DelayMinLimit

    Action = KeyAction(Type="Key", Code=65, Name="A")
    print(f"  创建按键: {Action}")
    assert Action.Type == "Key" and Action.Code == 65 and Action.Name == "A"

    # 序列化/反序列化
    Data = {"Type": Action.Type, "Code": Action.Code, "Name": Action.Name}
    Restored = KeyAction(**Data)
    assert Restored == Action
    print(f"  序列化还原: {Restored}")

    print(f"  默认延迟: {DefaultDelayMin}~{DefaultDelayMax}ms, 下限: {DelayMinLimit}ms")
    print("  通过\n")


def TestConfigMgr():
    print("=== 测试 ConfigMgr ===")
    from Source.Logic.ConfigMgr import ConfigMgr

    Cfg = ConfigMgr()
    print(f"  配置路径: {Cfg.ConfigPath}")

    # 写入
    Cfg.Set("Test.Value", 42)
    Cfg.Set("Test.Name", "测试")
    assert Cfg.Get("Test.Value") == 42
    assert Cfg.Get("Test.Name") == "测试"
    assert Cfg.Get("NotExist", "默认") == "默认"
    print("  读写测试: 通过")

    # 单例验证
    Cfg2 = ConfigMgr()
    assert Cfg is Cfg2
    print("  单例验证: 通过\n")


def TestFocusWatcher():
    print("=== 测试 FocusWatcher ===")
    from Source.Logic import FocusWatcher

    Title = FocusWatcher.GetForegroundWindowTitle()
    print(f"  当前焦点窗口: {Title}")

    Windows = FocusWatcher.ListWindows()
    print(f"  可见窗口数量: {len(Windows)}")
    for W in Windows[:5]:
        print(f"    - {W}")
    if len(Windows) > 5:
        print(f"    ... 共 {len(Windows)} 个")

    Focused = FocusWatcher.IsWindowFocused(Title)
    print(f"  焦点匹配（自身）: {Focused}")
    assert Focused
    print("  通过\n")


def TestInputDriver():
    print("=== 测试 InputDriver ===")
    from Source.Logic.InputDriver import _INPUT, _ExtendedVKs
    import ctypes

    # 验证结构体大小合理
    Size = ctypes.sizeof(_INPUT)
    print(f"  INPUT 结构体大小: {Size} 字节")
    assert Size > 0

    # 验证扩展键集合
    print(f"  扩展键数量: {len(_ExtendedVKs)}")
    assert 0x25 in _ExtendedVKs  # 左方向键
    assert 0x2E in _ExtendedVKs  # Delete
    print("  （跳过实际发送按键，避免干扰）")
    print("  通过\n")


def TestInputListener():
    print("=== 测试 InputListener ===")
    from Source.Logic.InputListener import InputListener
    from pynput import keyboard, mouse

    Listener = InputListener()

    # 测试按键解析
    Code, Name = Listener._ResolveKey(keyboard.Key.space)
    print(f"  解析 Space: Code={Code}, Name={Name}")
    assert Name == "Space"

    Code, Name = Listener._ResolveKey(keyboard.Key.enter)
    print(f"  解析 Enter: Code={Code}, Name={Name}")
    assert Name == "Enter"

    # 测试鼠标解析
    Code, Name = Listener._ResolveMouseButton(mouse.Button.left)
    print(f"  解析鼠标左键: Code={Code}, Name={Name}")
    assert Code == 1 and Name == "鼠标左键"

    Code, Name = Listener._ResolveMouseButton(mouse.Button.right)
    print(f"  解析鼠标右键: Code={Code}, Name={Name}")
    assert Code == 2 and Name == "鼠标右键"

    print("  通过\n")


if __name__ == "__main__":
    print("CustomKeyEcho 功能测试\n")
    TestKeyProfile()
    TestConfigMgr()
    TestFocusWatcher()
    TestInputDriver()
    TestInputListener()
    print("全部测试通过")
