from datetime import datetime
import re
import unicodedata

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"
ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
COLUMN_WIDTHS = [10, 12, 10, 10, 10, 10, 10]


def color_change(change_pct: float) -> str:
    value = f"{change_pct:+.2f}%"
    if change_pct > 0:
        return f"{RED}{value}{RESET}"
    if change_pct < 0:
        return f"{GREEN}{value}{RESET}"
    return value


def render_quotes(rows: list[dict], include_time: bool = False) -> str:
    lines: list[str] = []
    if include_time:
        lines.append(f"刷新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

    holding_rows = [row for row in rows if row["section"] == "holding"]
    watch_rows = [row for row in rows if row["section"] == "watch"]

    lines.append("持仓列表")
    lines.append(_format_row(["代码", "名称", "当前价", "涨跌幅", "持仓", "成本价", "盈亏"]))
    if holding_rows:
        for row in holding_rows:
            lines.append(
                _format_row(
                    [
                        row["symbol"][2:],
                        row["name"],
                        f"{row['price']:.2f}",
                        color_change(row["change_pct"]),
                        _format_optional(row.get("shares")),
                        _format_optional(row.get("cost")),
                        _format_profit(row.get("profit")),
                    ]
                )
            )
    else:
        lines.append("暂无持仓")

    lines.append("")
    lines.append("观测列表")
    lines.append(_format_row(["代码", "名称", "当前价", "涨跌幅"]))
    if watch_rows:
        for row in watch_rows:
            lines.append(
                _format_row(
                    [
                        row["symbol"][2:],
                        row["name"],
                        f"{row['price']:.2f}",
                        color_change(row["change_pct"]),
                    ]
                )
            )
    else:
        lines.append("暂无观测")
    return "\n".join(lines)


def _format_row(values: list[str]) -> str:
    return "  ".join(_pad_cell(value, COLUMN_WIDTHS[index]) for index, value in enumerate(values))


def _pad_cell(value: object, width: int) -> str:
    text = str(value)
    padding = max(0, width - _display_width(text))
    return f"{text}{' ' * padding}"


def _display_width(value: str) -> int:
    text = ANSI_PATTERN.sub("", value)
    return sum(_char_width(char) for char in text)


def _char_width(char: str) -> int:
    if unicodedata.east_asian_width(char) in {"F", "W"}:
        return 2
    return 1


def _format_optional(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _format_profit(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:+.2f}"
