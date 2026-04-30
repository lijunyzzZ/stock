import argparse
import os
import sys
import time
from collections.abc import Callable, Sequence
from typing import TextIO

from .provider import Quote, fetch_quotes
from .render import render_quotes
from .store import PortfolioStore
from .symbols import display_symbol


QuoteFetcher = Callable[[list[str]], list[Quote]]


def main(
    argv: Sequence[str] | None = None,
    store_path: str | os.PathLike[str] | None = None,
    quote_fetcher: QuoteFetcher = fetch_quotes,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = PortfolioStore(store_path or args.config)

    try:
        if args.command == "add-holding":
            store.add_holding(args.symbol, shares=args.shares, cost=args.cost)
            print(f"已添加持仓：{display_symbol(args.symbol)}", file=out)
            return 0
        if args.command == "remove-holding":
            store.remove_holding(args.symbol)
            print(f"已删除持仓：{display_symbol(args.symbol)}", file=out)
            return 0
        if args.command == "add-watch":
            store.add_watch(args.symbol)
            print(f"已添加观测：{display_symbol(args.symbol)}", file=out)
            return 0
        if args.command == "remove-watch":
            store.remove_watch(args.symbol)
            print(f"已删除观测：{display_symbol(args.symbol)}", file=out)
            return 0
        if args.command == "list":
            print(render_config(store), file=out)
            return 0
        if args.command is None or args.command == "show":
            return show_once(store, quote_fetcher, out, err, include_time=False)
        if args.command == "watch":
            return watch_loop(store, quote_fetcher, out, err, interval=args.interval)
    except ValueError as exc:
        print(f"错误：{exc}", file=err)
        return 2
    except OSError as exc:
        print(f"行情请求失败：{exc}", file=err)
        return 3

    parser.print_help(out)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stock", description="A股持仓和观测列表命令行监控工具")
    parser.add_argument("--config", help="配置文件路径，默认 ~/.stock-cli/portfolio.json")
    subparsers = parser.add_subparsers(dest="command")

    add_holding = subparsers.add_parser("add-holding", help="添加或更新持仓")
    add_holding.add_argument("symbol")
    add_holding.add_argument("--shares", type=float)
    add_holding.add_argument("--cost", type=float)

    remove_holding = subparsers.add_parser("remove-holding", help="删除持仓")
    remove_holding.add_argument("symbol")

    add_watch = subparsers.add_parser("add-watch", help="添加观测股票")
    add_watch.add_argument("symbol")

    remove_watch = subparsers.add_parser("remove-watch", help="删除观测股票")
    remove_watch.add_argument("symbol")

    subparsers.add_parser("list", help="查看已配置的持仓和观测列表")
    subparsers.add_parser("show", help="输出一次行情")

    watch = subparsers.add_parser("watch", help="实时刷新行情")
    watch.add_argument("--interval", type=float, default=5.0, help="刷新间隔秒数，默认 5")

    return parser


def render_config(store: PortfolioStore) -> str:
    lines = ["持仓列表"]
    if store.data["holdings"]:
        for item in store.data["holdings"]:
            parts = [item["symbol"][2:]]
            if "shares" in item:
                parts.append(f"持仓={_format_number(item['shares'])}")
            if "cost" in item:
                parts.append(f"成本={_format_number(item['cost'])}")
            lines.append("  ".join(parts))
    else:
        lines.append("暂无持仓")

    lines.append("")
    lines.append("观测列表")
    if store.data["watchlist"]:
        lines.extend(item["symbol"][2:] for item in store.data["watchlist"])
    else:
        lines.append("暂无观测")
    return "\n".join(lines)


def show_once(
    store: PortfolioStore,
    quote_fetcher: QuoteFetcher,
    out: TextIO,
    err: TextIO,
    include_time: bool,
) -> int:
    symbols = store.all_symbols()
    if not symbols:
        print("暂无持仓或观测股票，请先添加。", file=out)
        return 0
    quotes = {quote.symbol: quote for quote in quote_fetcher(symbols)}
    rows = build_rows(store, quotes)
    print(render_quotes(rows, include_time=include_time), file=out)
    return 0


def watch_loop(
    store: PortfolioStore,
    quote_fetcher: QuoteFetcher,
    out: TextIO,
    err: TextIO,
    interval: float,
) -> int:
    if interval <= 0:
        print("错误：--interval 必须大于 0", file=err)
        return 2
    try:
        while True:
            print("\033[2J\033[H", end="", file=out)
            show_once(store, quote_fetcher, out, err, include_time=True)
            print("\n按 Ctrl+C 退出", file=out)
            out.flush()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n已退出", file=out)
        return 0


def build_rows(store: PortfolioStore, quotes: dict[str, Quote]) -> list[dict]:
    rows: list[dict] = []
    for holding in store.data["holdings"]:
        quote = quotes.get(holding["symbol"])
        if quote is None:
            continue
        shares = holding.get("shares")
        cost = holding.get("cost")
        profit = None
        if shares is not None and cost is not None:
            profit = (quote.price - cost) * shares
        rows.append(
            {
                "section": "holding",
                "symbol": quote.symbol,
                "name": quote.name,
                "price": quote.price,
                "change_pct": quote.change_pct,
                "shares": shares,
                "cost": cost,
                "profit": profit,
            }
        )
    for watched in store.data["watchlist"]:
        quote = quotes.get(watched["symbol"])
        if quote is None:
            continue
        rows.append(
            {
                "section": "watch",
                "symbol": quote.symbol,
                "name": quote.name,
                "price": quote.price,
                "change_pct": quote.change_pct,
            }
        )
    return rows


def _format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(value)
