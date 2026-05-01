from dataclasses import dataclass, field

DelayMinLimit = 10
DefaultDelayMin = 1000
DefaultDelayMax = 1500
DefaultComboDelayMin = 10  # 组合键间隔下限（ms）
DefaultComboDelayMax = 30  # 组合键间隔上限（ms）
DefaultHotKeyCode = 117  # F6
DefaultHotKeyName = "F6"


@dataclass
class KeyAction:
    Type: str  # "Key" / "Mouse"
    Code: int
    Name: str
    Modifiers: list[int] = field(default_factory=list)  # 修饰键 VK 码列表


@dataclass
class KeySequence:
    Actions: list[KeyAction] = field(default_factory=list)
    DelayMin: int = DefaultDelayMin
    DelayMax: int = DefaultDelayMax

    def ToDict(self) -> dict:
        return {
            "Actions": [
                {"Type": A.Type, "Code": A.Code, "Name": A.Name, "Modifiers": A.Modifiers}
                for A in self.Actions
            ],
            "DelayMin": self.DelayMin,
            "DelayMax": self.DelayMax,
        }

    @staticmethod
    def FromDict(Data: dict) -> "KeySequence":
        Actions = []
        for A in Data.get("Actions", []):
            Actions.append(KeyAction(
                Type=A["Type"], Code=A["Code"], Name=A["Name"],
                Modifiers=A.get("Modifiers", []),
            ))
        return KeySequence(
            Actions=Actions,
            DelayMin=Data.get("DelayMin", DefaultDelayMin),
            DelayMax=Data.get("DelayMax", DefaultDelayMax),
        )

    def DisplayName(self) -> str:
        if not self.Actions:
            return "(空序列)"
        Keys = ", ".join(A.Name for A in self.Actions[:4])
        if len(self.Actions) > 4:
            Keys += f" ... (+{len(self.Actions) - 4})"
        return f"[{Keys}]  {self.DelayMin}~{self.DelayMax}ms"
