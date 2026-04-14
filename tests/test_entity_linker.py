"""Tests for the ticker dictionary and entity linker."""

from src.pipeline.entity_linker import TickerDictionary


def _make_dict() -> TickerDictionary:
    return TickerDictionary([
        {"ticker": "SBER", "company": "Sberbank", "aliases": ["Сбербанк", "Сбер"]},
        {"ticker": "GAZP", "company": "Gazprom", "aliases": ["Газпром"]},
    ])


def test_resolve_russian_alias():
    td = _make_dict()
    assert td.resolve("Сбербанк объявил о дивидендах") == "SBER"


def test_resolve_english_company():
    td = _make_dict()
    assert td.resolve("Sberbank announces Q1 results") == "SBER"


def test_resolve_ticker_directly():
    td = _make_dict()
    assert td.resolve("Акции GAZP выросли") == "GAZP"


def test_resolve_no_match():
    td = _make_dict()
    assert td.resolve("Apple выпустила новый iPhone") is None


def test_universe():
    td = _make_dict()
    assert td.universe == {"SBER", "GAZP"}


def test_from_yaml(tmp_path):
    yaml_file = tmp_path / "tickers.yaml"
    yaml_file.write_text(
        "tickers:\n"
        "  - ticker: SBER\n"
        "    company: Sberbank\n"
        "    aliases: ['Сбербанк']\n"
    )
    td = TickerDictionary.from_yaml(yaml_file)
    assert td.resolve("Сбербанк") == "SBER"
