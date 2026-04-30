import sys

# Windows 控制台默认 GBK，强制切 UTF-8 以免中文/emoji 编码崩
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from PySide6.QtWidgets import QApplication
from Source.UI.MainWindow import MainWindow


def Main():
    App = QApplication(sys.argv)
    App.setApplicationName("CustomKeyEcho")
    Window = MainWindow()
    Window.show()
    sys.exit(App.exec())


if __name__ == "__main__":
    Main()
