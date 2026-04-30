from dataclasses import dataclass
from urllib.parse import quote
from urllib.request import urlopen


@dataclass(frozen=True)
class Quote:
    symbol: str
    name: str
    price: float
    change_pct: float
    previous_close: float
    date: str = ""
    time: str = ""


def parse_sina_response(text: str) -> list[Quote]:
    quotes: list[Quote] = []
    for statement in text.split(";"):
        statement = statement.strip()
        if not statement or "hq_str_" not in statement:
            continue
        prefix, raw = statement.split("=", 1)
        symbol = prefix.rsplit("hq_str_", 1)[1]
        fields = raw.strip().strip('"').split(",")
        if len(fields) < 4 or not fields[0]:
            continue
        previous_close = _to_float(fields[2])
        price = _to_float(fields[3])
        change_pct = 0.0 if previous_close == 0 else (price - previous_close) / previous_close * 100
        quotes.append(
            Quote(
                symbol=symbol,
                name=fields[0],
                price=price,
                change_pct=change_pct,
                previous_close=previous_close,
                date=fields[30] if len(fields) > 30 else "",
                time=fields[31] if len(fields) > 31 else "",
            )
        )
    return quotes


def fetch_quotes(symbols: list[str], timeout: float = 5.0) -> list[Quote]:
    if not symbols:
        return []
    symbol_list = ",".join(symbols)
    url = f"http://hq.sinajs.cn/list={quote(symbol_list, safe=',')}"
    request_headers = {"Referer": "https://finance.sina.com.cn/"}
    import urllib.request

    request = urllib.request.Request(url, headers=request_headers)
    with urlopen(request, timeout=timeout) as response:
        body = response.read().decode("gbk", errors="replace")
    return parse_sina_response(body)


def _to_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0
