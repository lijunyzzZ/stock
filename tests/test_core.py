import os
import re
import tempfile
import unicodedata
import unittest

import money.provider
from money.provider import fetch_quotes, parse_sina_response
from money.render import GREEN, RED, RESET, render_quotes
from money.store import PortfolioStore
from money.symbols import normalize_symbol


class SymbolTests(unittest.TestCase):
    def test_normalize_a_share_symbol_adds_market_prefix(self):
        self.assertEqual(normalize_symbol("600519"), "sh600519")
        self.assertEqual(normalize_symbol("000001"), "sz000001")
        self.assertEqual(normalize_symbol("300750"), "sz300750")
        self.assertEqual(normalize_symbol("430047"), "bj430047")

    def test_normalize_keeps_existing_prefix_and_strips_spaces(self):
        self.assertEqual(normalize_symbol(" SH600519 "), "sh600519")


class StoreTests(unittest.TestCase):
    def test_store_persists_holdings_and_watchlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "portfolio.json")
            store = PortfolioStore(path)

            store.add_holding("600519", shares=2, cost=1500.5)
            store.add_watch("300750")

            reloaded = PortfolioStore(path)
            self.assertEqual(
                reloaded.data["holdings"],
                [{"symbol": "sh600519", "shares": 2.0, "cost": 1500.5}],
            )
            self.assertEqual(reloaded.data["watchlist"], [{"symbol": "sz300750"}])

    def test_store_moves_symbol_out_of_watchlist_when_added_to_holdings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "portfolio.json")
            store = PortfolioStore(path)

            store.add_watch("600519")
            store.add_holding("600519", shares=None, cost=None)

            self.assertEqual(store.data["watchlist"], [])
            self.assertEqual(store.data["holdings"], [{"symbol": "sh600519"}])


class ProviderTests(unittest.TestCase):
    def test_parse_sina_response_calculates_change_percent(self):
        response = (
            'var hq_str_sh600519="贵州茅台,1700.00,1680.00,1716.80,'
            '1720.00,1690.00,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'
            '2026-04-30,10:30:00,00";'
        )

        quotes = parse_sina_response(response)

        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0].symbol, "sh600519")
        self.assertEqual(quotes[0].name, "贵州茅台")
        self.assertEqual(quotes[0].price, 1716.8)
        self.assertAlmostEqual(quotes[0].change_pct, 2.1905, places=4)

    def test_fetch_quotes_uses_http_endpoint_and_keeps_commas_for_symbol_lists(self):
        response = (
            'var hq_str_sh600519="贵州茅台,1700.00,1680.00,1716.80,'
            '1720.00,1690.00,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'
            '2026-04-30,10:30:00,00";'
        ).encode("gbk")
        captured_urls = []

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return response

        def fake_urlopen(request, timeout):
            captured_urls.append(request.full_url)
            return FakeResponse()

        original = money.provider.urlopen
        money.provider.urlopen = fake_urlopen
        try:
            quotes = fetch_quotes(["sh600519", "sz300750"])
        finally:
            money.provider.urlopen = original

        self.assertEqual(captured_urls, ["http://hq.sinajs.cn/list=sh600519,sz300750"])
        self.assertEqual(quotes[0].symbol, "sh600519")


class RenderTests(unittest.TestCase):
    def test_render_uses_expected_colors_and_omits_position_for_watchlist(self):
        rows = [
            {
                "section": "holding",
                "symbol": "sh600519",
                "name": "贵州茅台",
                "price": 1716.8,
                "change_pct": 2.19,
                "previous_close": 1680.0,
                "shares": 2,
                "cost": 1500,
                "profit": 433.6,
            },
            {
                "section": "watch",
                "symbol": "sz300750",
                "name": "宁德时代",
                "price": 180.0,
                "change_pct": -1.23,
            },
        ]

        output = render_quotes(rows)

        self.assertIn(f"{GREEN}1716.80{RESET}", output)
        self.assertIn(f"{RED}+2.19%{RESET}", output)
        self.assertIn(f"{RED}+433.60{RESET}", output)
        self.assertIn(f"今日盈亏：{RED}+73.60{RESET}", output)
        self.assertIn(f"总盈亏：{RED}+433.60{RESET}", output)
        self.assertLess(output.index("今日盈亏："), output.index("总盈亏："))
        self.assertIn(f"{RED}180.00{RESET}", output)
        self.assertIn(f"{GREEN}-1.23%{RESET}", output)
        watch_section = output.split("观测列表", 1)[1]
        self.assertNotIn("持仓", watch_section.splitlines()[1])
        self.assertNotIn("成本", watch_section.splitlines()[1])

    def test_render_totals_multiple_holding_profits_and_colors_loss_green(self):
        rows = [
            {
                "section": "holding",
                "symbol": "sh600585",
                "name": "海螺水泥",
                "price": 21.18,
                "change_pct": -0.38,
                "previous_close": 21.26,
                "shares": 1900,
                "cost": 21.3,
                "profit": -228.0,
            },
            {
                "section": "holding",
                "symbol": "sz000001",
                "name": "平安银行",
                "price": 10.0,
                "change_pct": 0.0,
                "previous_close": 10.0,
                "shares": 100,
                "cost": 11.0,
                "profit": -100.0,
            },
        ]

        output = render_quotes(rows)

        self.assertIn(f"{RED}21.18{RESET}", output)
        self.assertIn(f"{GREEN}-228.00{RESET}", output)
        self.assertIn(f"今日盈亏：{GREEN}-152.00{RESET}", output)
        self.assertIn(f"总盈亏：{GREEN}-328.00{RESET}", output)

    def test_render_aligns_columns_with_chinese_names_and_color_codes(self):
        rows = [
            {
                "section": "holding",
                "symbol": "sh600585",
                "name": "海螺水泥",
                "price": 21.18,
                "change_pct": -0.38,
                "shares": 1900,
                "cost": 21.3,
                "profit": -228.0,
            }
        ]

        output = render_quotes(rows)
        lines = [_strip_ansi(line).rstrip() for line in output.splitlines()]
        header = lines[1]
        data = lines[2]

        for column in ["代码", "名称", "当前价", "涨跌幅", "持仓", "成本价", "盈亏"]:
            self.assertEqual(_display_index(header, column), _display_index(data, _value_for_column(column)))


def _strip_ansi(value: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", value)


def _value_for_column(column: str) -> str:
    return {
        "代码": "600585",
        "名称": "海螺水泥",
        "当前价": "21.18",
        "涨跌幅": "-0.38%",
        "持仓": "1900",
        "成本价": "21.3",
        "盈亏": "-228.00",
    }[column]


def _display_index(line: str, needle: str) -> int:
    char_index = line.index(needle)
    return sum(_char_width(char) for char in line[:char_index])


def _char_width(char: str) -> int:
    if unicodedata.east_asian_width(char) in {"F", "W"}:
        return 2
    return 1


if __name__ == "__main__":
    unittest.main()
