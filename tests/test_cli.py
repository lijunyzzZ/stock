import os
import tempfile
import unittest
from io import StringIO

from money.cli import main
from money.provider import Quote


class CliTests(unittest.TestCase):
    def test_cli_adds_holding_and_watch_then_lists_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "portfolio.json")
            output = StringIO()

            self.assertEqual(main(["add-holding", "600519", "--shares", "2", "--cost", "1500"], path, out=output), 0)
            self.assertEqual(main(["add-watch", "300750"], path, out=output), 0)
            self.assertEqual(main(["list"], path, out=output), 0)

            text = output.getvalue()
            self.assertIn("已添加持仓：600519", text)
            self.assertIn("已添加观测：300750", text)
            self.assertIn("600519  持仓=2", text)
            self.assertIn("300750", text)

    def test_cli_show_renders_quotes_from_fetcher(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "portfolio.json")
            output = StringIO()
            main(["add-holding", "600519", "--shares", "2", "--cost", "1500"], path, out=StringIO())
            main(["add-watch", "300750"], path, out=StringIO())

            def fake_fetcher(symbols):
                self.assertEqual(symbols, ["sh600519", "sz300750"])
                return [
                    Quote("sh600519", "贵州茅台", 1716.8, 2.19, 1680),
                    Quote("sz300750", "宁德时代", 180.0, -1.23, 182.24),
                ]

            self.assertEqual(main(["show"], path, quote_fetcher=fake_fetcher, out=output), 0)

            text = output.getvalue()
            self.assertIn("持仓列表", text)
            self.assertIn("观测列表", text)
            self.assertIn("今日盈亏", text)
            self.assertIn("73.60", text)
            self.assertIn("433.60", text)
            self.assertIn("\033[31m+2.19%\033[0m", text)
            self.assertIn("\033[32m-1.23%\033[0m", text)

    def test_cli_without_command_defaults_to_show(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "portfolio.json")
            output = StringIO()
            main(["add-watch", "600519"], path, out=StringIO())

            def fake_fetcher(symbols):
                self.assertEqual(symbols, ["sh600519"])
                return [Quote("sh600519", "贵州茅台", 1391.0, -0.5, 1398.0)]

            self.assertEqual(main([], path, quote_fetcher=fake_fetcher, out=output), 0)

            self.assertIn("持仓列表", output.getvalue())
            self.assertIn("贵州茅台", output.getvalue())

    def test_cli_accepts_explicit_config_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "custom.json")
            output = StringIO()

            self.assertEqual(main(["--config", path, "add-watch", "600519"], out=output), 0)
            self.assertEqual(main(["--config", path, "list"], out=output), 0)

            self.assertIn("600519", output.getvalue())


if __name__ == "__main__":
    unittest.main()
