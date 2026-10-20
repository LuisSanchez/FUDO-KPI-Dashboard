"""Read the calendar summary on page 1 of an Uber Eats monthly statement.

Weekly pages cross months, so only the consolidated first page is used.
Amounts stay signed as Uber prints them: fees and ads are negative, the
deposit ("Total neto") is what reached the bank.
"""

from __future__ import annotations

import re
from pathlib import Path

_MONTHS = {
    "jan": "01",
    "january": "01",
    "feb": "02",
    "february": "02",
    "mar": "03",
    "march": "03",
    "apr": "04",
    "april": "04",
    "may": "05",
    "jun": "06",
    "june": "06",
    "jul": "07",
    "july": "07",
    "aug": "08",
    "august": "08",
    "sep": "09",
    "sept": "09",
    "september": "09",
    "oct": "10",
    "october": "10",
    "nov": "11",
    "november": "11",
    "dec": "12",
    "december": "12",
}

# pdfplumber interleaves the two columns, so a label is often mid-line.
# An optional leading plus covers "Ajustes +53 CLP".
_AMOUNT = r"([+-]?\s*(?:CLP)?\s*-?[\d.]+(?:\s*CLP)?)"

_cache: dict[str, tuple[float, dict]] = {}


def month_from_filename(name: str) -> str | None:
    match = re.match(r"([A-Za-z]+)\s+(\d{4})", name.strip())
    if not match:
        return None
    month = _MONTHS.get(match.group(1).lower())
    if not month:
        return None
    return f"{match.group(2)}-{month}"


def parse_money(token: str) -> int:
    """Parse an Uber amount. Dots in groups of three are thousands, not decimals."""
    cleaned = token.replace("*", "").replace("+", "").strip()
    negative = "-" in cleaned
    cleaned = cleaned.replace("-", "").replace("CLP", "").replace(" ", "")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", cleaned):
        value = int(cleaned.replace(".", ""))
    else:
        value = int(round(float(cleaned)))
    return -value if negative else value


def _amount_after(text: str, label: str) -> int | None:
    # "Tasas de servicio" is also the prefix of "Tasas de servicio totales".
    guard = "(?! totales)" if label == "Tasas de servicio" else ""
    match = re.search(rf"{re.escape(label)}{guard}\s+{_AMOUNT}", text)
    if not match:
        return None
    return parse_money(match.group(1))


def parse_statement_text(text: str, month: str) -> dict:
    sales = re.search(rf"Ventas \((\d+) Pedidos\)\s+{_AMOUNT}", text)
    tasa_bruta = _amount_after(text, "Tasas de servicio")
    return {
        "month": month,
        "pedidos": int(sales.group(1)) if sales else None,
        "ventas": parse_money(sales.group(2)) if sales else None,
        "ofertas": _amount_after(text, "Ofertas en artículos"),
        "tasa": tasa_bruta,
        "tasa_total": _amount_after(text, "Tasas de servicio totales"),
        "cargo_oferta": _amount_after(text, "Otros cargos de la oferta"),
        "anuncios": _amount_after(text, "Gastos por anuncios"),
        "ajuste_marketing": _amount_after(text, "Ajuste de marketing"),
        "ajustes": _amount_after(text, "Ajustes"),
        "neto": _amount_after(text, "Total neto"),
    }


def parse_statement_file(path: Path) -> dict | None:
    month = month_from_filename(path.name)
    if month is None:
        return None
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        text = pdf.pages[0].extract_text() or ""
    parsed = parse_statement_text(text, month)
    if parsed.get("neto") is None and parsed.get("ventas") is None:
        return None
    return parsed


def load_uber_statements(directory: Path | None) -> dict[str, dict]:
    """Map YYYY-MM to the page-1 summary. Empty when the folder or parser is missing."""
    if directory is None or not directory.is_dir():
        return {}
    found: dict[str, dict] = {}
    for path in sorted(directory.glob("*.pdf")):
        key = str(path.resolve())
        try:
            stamp = path.stat().st_mtime
        except OSError:
            continue
        cached = _cache.get(key)
        if cached and cached[0] == stamp:
            found[cached[1]["month"]] = cached[1]
            continue
        try:
            parsed = parse_statement_file(path)
        except Exception:
            continue
        if not parsed:
            continue
        _cache[key] = (stamp, parsed)
        found[parsed["month"]] = parsed
    return found
