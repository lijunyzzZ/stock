# A Share CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a command-line tool for monitoring A-share holdings and watchlist quotes.

**Architecture:** Use a small Python package with no runtime third-party dependencies. Store user data in a local JSON file, fetch A-share quotes from a Sina-compatible quote endpoint, and render either one-shot or continuously refreshed terminal output.

**Tech Stack:** Python 3 standard library, `unittest`, `argparse`, JSON files, ANSI colors.

---

### Task 1: Core Behavior

**Files:**
- Create: `tests/test_core.py`
- Create: `src/money/symbols.py`
- Create: `src/money/store.py`
- Create: `src/money/provider.py`
- Create: `src/money/render.py`

- [ ] **Step 1: Write failing tests**

```python
def test_normalize_a_share_symbol_adds_market_prefix():
    assert normalize_symbol("600519") == "sh600519"
    assert normalize_symbol("000001") == "sz000001"
    assert normalize_symbol("300750") == "sz300750"
    assert normalize_symbol("430047") == "bj430047"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest discover -s tests -v`

- [ ] **Step 3: Implement minimal core modules**

Add symbol normalization, JSON-backed portfolio storage, Sina quote parsing, and terminal table rendering.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest discover -s tests -v`

### Task 2: CLI

**Files:**
- Create: `src/money/cli.py`
- Create: `src/money/__main__.py`
- Create: `src/money/__init__.py`
- Create: `pyproject.toml`
- Create: `README.md`

- [ ] **Step 1: Write failing CLI tests**

Test adding holdings, adding watch symbols, listing config, and rendering quotes through a fake quote provider.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest discover -s tests -v`

- [ ] **Step 3: Implement CLI commands**

Implement `add-holding`, `remove-holding`, `add-watch`, `remove-watch`, `list`, `show`, and `watch`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest discover -s tests -v`

