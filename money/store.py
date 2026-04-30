import json
import os
from pathlib import Path

from .symbols import normalize_symbol


DEFAULT_HOME = Path.home() / ".stock-cli"
DEFAULT_PATH = DEFAULT_HOME / "portfolio.json"


class PortfolioStore:
    def __init__(self, path: str | os.PathLike[str] | None = None):
        self.path = Path(path) if path else Path(os.environ.get("STOCK_CLI_CONFIG", DEFAULT_PATH))
        self.data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {"holdings": [], "watchlist": []}
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return {
            "holdings": data.get("holdings", []),
            "watchlist": data.get("watchlist", []),
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(self.data, file, ensure_ascii=False, indent=2)
            file.write("\n")

    def add_holding(self, symbol: str, shares: float | None = None, cost: float | None = None) -> None:
        normalized = normalize_symbol(symbol)
        entry = {"symbol": normalized}
        if shares is not None:
            entry["shares"] = float(shares)
        if cost is not None:
            entry["cost"] = float(cost)

        self.data["holdings"] = [item for item in self.data["holdings"] if item["symbol"] != normalized]
        self.data["watchlist"] = [item for item in self.data["watchlist"] if item["symbol"] != normalized]
        self.data["holdings"].append(entry)
        self.save()

    def remove_holding(self, symbol: str) -> None:
        normalized = normalize_symbol(symbol)
        self.data["holdings"] = [item for item in self.data["holdings"] if item["symbol"] != normalized]
        self.save()

    def add_watch(self, symbol: str) -> None:
        normalized = normalize_symbol(symbol)
        if any(item["symbol"] == normalized for item in self.data["holdings"]):
            return
        self.data["watchlist"] = [item for item in self.data["watchlist"] if item["symbol"] != normalized]
        self.data["watchlist"].append({"symbol": normalized})
        self.save()

    def remove_watch(self, symbol: str) -> None:
        normalized = normalize_symbol(symbol)
        self.data["watchlist"] = [item for item in self.data["watchlist"] if item["symbol"] != normalized]
        self.save()

    def all_symbols(self) -> list[str]:
        symbols = [item["symbol"] for item in self.data["holdings"]]
        symbols.extend(item["symbol"] for item in self.data["watchlist"])
        return symbols

