from dataclasses import dataclass

DelayMinLimit = 10
DefaultDelayMin = 1000
DefaultDelayMax = 1500
DefaultHotKeyCode = 117  # F6
DefaultHotKeyName = "F6"


@dataclass
class KeyAction:
    Type: str  # "Key" / "Mouse"
    Code: int
    Name: str
