def normalize_symbol(symbol: str) -> str:
    value = symbol.strip().lower()
    if len(value) == 8 and value[:2] in {"sh", "sz", "bj"} and value[2:].isdigit():
        return value
    if len(value) != 6 or not value.isdigit():
        raise ValueError(f"invalid A-share symbol: {symbol}")
    if value.startswith(("6", "9")):
        return f"sh{value}"
    if value.startswith(("0", "2", "3")):
        return f"sz{value}"
    if value.startswith(("4", "8")):
        return f"bj{value}"
    raise ValueError(f"unsupported A-share symbol: {symbol}")


def display_symbol(symbol: str) -> str:
    normalized = normalize_symbol(symbol)
    return normalized[2:]

