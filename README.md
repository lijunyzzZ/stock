# A股命令行监控

一个轻量的命令行工具，用于维护 A 股持仓列表和观测列表，并查看实时涨跌幅。

## 使用

```bash
python3 -m money add-holding 600519 --shares 2 --cost 1500
python3 -m money add-watch 300750
python3 -m money list
python3 -m money show
python3 -m money watch --interval 5
```

使用指定配置文件：

```bash
python3 -m money --config /path/to/portfolio.json show
```

## 颜色规则

- 上涨：红字
- 下跌：绿字
- 观测列表不展示持仓、成本、盈亏字段

## 本地配置

默认保存到：

```text
~/.stock-cli/portfolio.json
```

可以通过环境变量覆盖：

```bash
STOCK_CLI_CONFIG=/path/to/portfolio.json python3 -m money show
```

## 测试

```bash
python3 -m unittest discover -s tests -v
```
