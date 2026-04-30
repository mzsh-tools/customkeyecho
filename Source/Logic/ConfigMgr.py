import json
from pathlib import Path
from platformdirs import user_data_dir

AppName = "CustomKeyEcho"


class ConfigMgr:
    _Instance = None
    ConfigPath = Path(user_data_dir(AppName, appauthor=False)) / "Config.json"

    def __new__(cls):
        if cls._Instance is None:
            cls._Instance = super().__new__(cls)
            cls._Instance._Data = {}
            cls._Instance._Load()
        return cls._Instance

    def _Load(self):
        if self.ConfigPath.is_file():
            try:
                self._Data = json.loads(self.ConfigPath.read_text(encoding="utf-8"))
            except Exception:
                self._Data = {}
        else:
            self._Data = {}

    def Save(self):
        self.ConfigPath.parent.mkdir(parents=True, exist_ok=True)
        self.ConfigPath.write_text(
            json.dumps(self._Data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def Get(self, Key: str, Default=None):
        Keys = Key.split(".")
        Cur = self._Data
        for K in Keys:
            if isinstance(Cur, dict) and K in Cur:
                Cur = Cur[K]
            else:
                return Default
        return Cur

    def Set(self, Key: str, Value):
        Keys = Key.split(".")
        Cur = self._Data
        for K in Keys[:-1]:
            if K not in Cur or not isinstance(Cur[K], dict):
                Cur[K] = {}
            Cur = Cur[K]
        Cur[Keys[-1]] = Value
