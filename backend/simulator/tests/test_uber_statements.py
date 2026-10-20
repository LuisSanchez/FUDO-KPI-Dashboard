"""Page 1 of the Uber Eats monthly statements."""

from pathlib import Path

import pytest

from simulator.processing.uber_statements import (
    load_uber_statements,
    month_from_filename,
    parse_money,
    parse_statement_text,
)

ROOT = Path(__file__).resolve().parents[3]
STATEMENTS = ROOT / "docs" / "2026" / "uber-eats"

SEPTEMBER = """
Ventas (167 Pedidos) 4.272.910 CLP
Tasas de servicio
Tasas de servicio -864.581 CLP
Sep 01-30, 2026 Tasas de servicio totales -864.566 CLP
Ofertas en artículos -1.477.140 CLP
Ajuste de marketing 79.900 CLP
Esta sección consolida todas las Otros cargos de la oferta -95.241 CLP
total neto del mes calendario. Por lo Gastos por anuncios -330.468 CLP
generación del resumen, como Ajustes -918.264 CLP
Total neto 655.892 CLP*
"""

# ventas, ofertas, tasa, anuncios, ajustes, neto
EXPECTED = {
    "2026-01": (182, 5_515_341, -2_073_060, -1_115_120, -798_929, 0, 1_536_690),
    "2026-02": (57, 1_620_187, -451_593, -378_133, -115_970, 0, 689_077),
    "2026-03": (50, 1_264_218, -122_464, -369_736, -136_608, 0, 632_810),
    "2026-04": (118, 3_066_063, -958_747, -658_869, -360_904, 0, 1_076_342),
    "2026-05": (157, 4_042_085, -1_049_843, -948_991, -365_808, 0, 1_752_881),
    "2026-06": (237, 5_563_006, -1_666_317, -1_245_267, -347_669, 53, 2_346_957),
    "2026-07": (200, 5_255_424, -1_087_219, -1_249_609, -386_999, -920_315, 1_457_362),
    "2026-08": (172, 4_678_906, -1_387_901, -993_725, -386_725, -968_284, 852_474),
    "2026-09": (167, 4_272_910, -1_477_140, -864_581, -330_468, -918_264, 655_892),
}


def test_parse_money_distinguishes_thousands_from_january_decimals():
    assert parse_money("655.892 CLP") == 655_892
    assert parse_money("4.272.910 CLP") == 4_272_910
    assert parse_money("-864.581 CLP") == -864_581
    assert parse_money("-CLP798929.11") == -798_929
    assert parse_money("CLP1536689.89*") == 1_536_690
    assert parse_money("CLP5515341.00") == 5_515_341
    assert parse_money("-CLP1115120.00") == -1_115_120
    assert parse_money("+53 CLP") == 53
    assert parse_money("CLP0.00") == 0


def test_september_snippet_keeps_the_fee_line_apart_from_the_total():
    parsed = parse_statement_text(SEPTEMBER, "2026-09")
    assert parsed["pedidos"] == 167
    assert parsed["ventas"] == 4_272_910
    assert parsed["tasa"] == -864_581
    assert parsed["tasa_total"] == -864_566
    assert parsed["ofertas"] == -1_477_140
    assert parsed["anuncios"] == -330_468
    assert parsed["ajustes"] == -918_264
    assert parsed["neto"] == 655_892
    assert parsed["cargo_oferta"] == -95_241


def test_month_from_filename():
    assert month_from_filename("Sep 2026_Oh My Pizza - Cantagallo.pdf") == "2026-09"
    assert month_from_filename("January 2026_x.pdf") == "2026-01"
    assert month_from_filename("notes.pdf") is None
    assert month_from_filename("Foo 2026.pdf") is None


def test_missing_folder_and_unreadable_files_are_skipped(tmp_path):
    assert load_uber_statements(None) == {}
    assert load_uber_statements(tmp_path / "missing") == {}
    (tmp_path / "notes.pdf").write_bytes(b"%PDF")
    (tmp_path / "Sep 2026_broken.pdf").write_bytes(b"not a pdf")
    assert load_uber_statements(tmp_path) == {}


def test_statement_without_totals_is_ignored(tmp_path, monkeypatch):
    pdfplumber = pytest.importorskip("pdfplumber")
    path = tmp_path / "Sep 2026_blank.pdf"
    path.write_bytes(b"x")

    class Page:
        def extract_text(self):
            return "sin numeros"

    class Doc:
        pages = [Page()]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(pdfplumber, "open", lambda *_args, **_kwargs: Doc())
    from simulator.processing.uber_statements import parse_statement_file

    assert parse_statement_file(path) is None
    assert load_uber_statements(tmp_path) == {}


@pytest.mark.skipif(not STATEMENTS.is_dir(), reason="Uber statements are not in this checkout")
def test_real_statements_match_page_one():
    pdfplumber = pytest.importorskip("pdfplumber")
    assert pdfplumber.__name__
    found = load_uber_statements(STATEMENTS)
    again = load_uber_statements(STATEMENTS)
    assert set(found) == set(EXPECTED)
    for month, expected in EXPECTED.items():
        row = found[month]
        assert again[month] == row
        assert (
            row["pedidos"],
            row["ventas"],
            row["ofertas"],
            row["tasa"],
            row["anuncios"],
            row["ajustes"],
            row["neto"],
        ) == expected
    assert sum(row["neto"] for row in found.values()) == 11_000_485
