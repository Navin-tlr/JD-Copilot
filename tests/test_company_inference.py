from app.rag import _infer_company_from_text, _normalize_company_for_metadata


def test_infer_company_from_label():
    text = "Company: Tap Academy\nWe are hiring for business development."
    assert _infer_company_from_text(text) == "Tap Academy"


def test_infer_company_from_special_case():
    text = "Join the TAP ACADEMY sales team and grow our partnerships."
    assert _infer_company_from_text(text) == "Tap Academy"


def test_normalize_company_produces_slug():
    assert _normalize_company_for_metadata("Tap Academy") == "tapacademy"
