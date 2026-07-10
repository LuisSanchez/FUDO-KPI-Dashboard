"""Smoke tests for PDF financial report generation."""


def test_build_financial_report(cleaned_sales, sample_expenses_df):
    from simulator.report import build_financial_report

    pdf = build_financial_report(cleaned_sales, sample_expenses_df, month="2026-03")
    assert isinstance(pdf, (bytes, bytearray))
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 500


def test_build_financial_report_all_months(cleaned_sales, sample_expenses_df):
    from simulator.report import build_financial_report

    pdf = build_financial_report(cleaned_sales, sample_expenses_df, month=None)
    assert pdf[:4] == b"%PDF"
