"""
Test suite for company name validation to prevent garbage detection.
Tests the _is_valid_company_name function logic.
"""

import re


# Copy of the validation logic from ingest/pipeline.py
_PLACEHOLDER_COMPANY_SLUGS = {
    "unknown", "companyname", "tbd", "tba", "pending", "none", "na", "null"
}


def _is_placeholder_company(name: str | None) -> bool:
    if not name:
        return True
    cleaned = name.strip()
    if not cleaned:
        return True
    if cleaned.startswith("#"):
        return True
    slug = re.sub(r"[^a-z]", "", cleaned.lower())
    return not slug or slug in _PLACEHOLDER_COMPANY_SLUGS


def _is_valid_company_name(name: str | None) -> bool:
    """
    Validate that extracted company name is real, not garbage like 'pdf', 'document', etc.
    Returns True if the name looks like a legitimate company name.
    """
    if not name:
        return False
    
    cleaned = name.strip()
    if not cleaned or len(cleaned) < 2:
        return False
    
    # Reject if it's a placeholder
    if _is_placeholder_company(cleaned):
        return False
    
    # Normalize for pattern matching
    normalized = cleaned.lower().replace("_", " ").replace("-", " ").strip()
    
    # Reject common file-related garbage patterns
    garbage_patterns = [
        r'^pdf\b',           # 'pdf', 'pdf_123'
        r'\bpdf$',           # 'document_pdf'
        r'\bpdf\d+',         # 'pdf123', 'pdf456'
        r'^doc\b',           # 'doc', 'document'
        r'^file\b',          # 'file', 'file_123'
        r'^jd\b',            # 'jd', 'jd_final'
        r'\bjd$',            # 'company_jd'
        r'^\d+$',            # Pure numbers like '123'
        r'^[a-z]_\d+$',      # Pattern like 'a_123', 'x_456'
        r'^\d+[a-z]+\d+$',   # Pattern like '123abc456'
        r'^temp\b',          # 'temp', 'temporary'
        r'^test\b',          # 'test', 'testing'
        r'^sample\b',        # 'sample'
        r'^draft\b',         # 'draft'
        r'^untitled\b',      # 'untitled'
        r'^copy\b',          # 'copy', 'copy of'
        r'\bcopy$',          # 'final_copy'
        r'^unnamed\b',       # 'unnamed'
        r'^new\b',           # 'new', 'new document'
        r'^final\b',         # 'final', 'final_version'
        r'\bfinal$',         # 'doc_final'
        r'placeholder',      # 'placeholder'
        r'^page\s',          # 'page 1', 'page number'
        r'document\s+id',    # 'document id 123'
        r'_v\d+$',           # 'doc_v1', 'file_v2'
        r'version',          # 'version 1', 'final version'
    ]
    
    for pattern in garbage_patterns:
        if re.search(pattern, normalized):
            print(f"⚠️ Rejected garbage company name: '{cleaned}' (matched pattern: {pattern})")
            return False
    
    # Reject if it's too generic (single common word)
    generic_words = {
        'document', 'file', 'paper', 'text', 'page', 'content',
        'company', 'organization', 'business', 'firm', 'enterprise',
        'job', 'role', 'position', 'opening', 'vacancy',
        'description', 'details', 'information', 'data'
    }
    
    if normalized in generic_words:
        print(f"⚠️ Rejected generic company name: '{cleaned}'")
        return False
    
    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', cleaned):
        print(f"⚠️ Rejected non-alphabetic company name: '{cleaned}'")
        return False
    
    # If it contains numbers, must have meaningful text too (e.g., "Adobe 2024" is OK, "123_pdf" is not)
    if re.search(r'\d', cleaned):
        # Count alphabetic characters
        alpha_chars = len(re.findall(r'[a-zA-Z]', cleaned))
        digit_chars = len(re.findall(r'\d', cleaned))
        
        # If more digits than letters, probably garbage
        if digit_chars > alpha_chars:
            print(f"⚠️ Rejected number-heavy company name: '{cleaned}'")
            return False
    
    return True


def test_garbage_company_names():
    """Test that garbage company names are rejected"""
    
    # File-related garbage
    assert not _is_valid_company_name("pdf"), "Should reject 'pdf'"
    assert not _is_valid_company_name("pdf_123"), "Should reject 'pdf_123'"
    assert not _is_valid_company_name("document_pdf"), "Should reject 'document_pdf'"
    assert not _is_valid_company_name("doc"), "Should reject 'doc'"
    assert not _is_valid_company_name("document"), "Should reject 'document'"
    assert not _is_valid_company_name("file"), "Should reject 'file'"
    assert not _is_valid_company_name("file_123"), "Should reject 'file_123'"
    
    # Number-heavy patterns
    assert not _is_valid_company_name("123"), "Should reject pure numbers"
    assert not _is_valid_company_name("456789"), "Should reject pure numbers"
    assert not _is_valid_company_name("a_123"), "Should reject 'a_123'"
    assert not _is_valid_company_name("x_456"), "Should reject 'x_456'"
    assert not _is_valid_company_name("123abc456"), "Should reject '123abc456'"
    
    # Generic words
    assert not _is_valid_company_name("company"), "Should reject 'company'"
    assert not _is_valid_company_name("organization"), "Should reject 'organization'"
    assert not _is_valid_company_name("business"), "Should reject 'business'"
    assert not _is_valid_company_name("job"), "Should reject 'job'"
    assert not _is_valid_company_name("description"), "Should reject 'description'"
    
    # Temporary/test patterns
    assert not _is_valid_company_name("temp"), "Should reject 'temp'"
    assert not _is_valid_company_name("test"), "Should reject 'test'"
    assert not _is_valid_company_name("sample"), "Should reject 'sample'"
    assert not _is_valid_company_name("draft"), "Should reject 'draft'"
    assert not _is_valid_company_name("untitled"), "Should reject 'untitled'"
    assert not _is_valid_company_name("copy"), "Should reject 'copy'"
    assert not _is_valid_company_name("unnamed"), "Should reject 'unnamed'"
    assert not _is_valid_company_name("new"), "Should reject 'new'"
    assert not _is_valid_company_name("placeholder"), "Should reject 'placeholder'"
    
    # Empty or minimal
    assert not _is_valid_company_name(""), "Should reject empty string"
    assert not _is_valid_company_name("   "), "Should reject whitespace"
    assert not _is_valid_company_name("a"), "Should reject single letter"
    assert not _is_valid_company_name(None), "Should reject None"
    
    # Non-alphabetic
    assert not _is_valid_company_name("123456"), "Should reject pure numbers"
    assert not _is_valid_company_name("___"), "Should reject pure symbols"
    
    print("✅ All garbage company name tests passed!")


def test_valid_company_names():
    """Test that valid company names are accepted"""
    
    # Major companies
    assert _is_valid_company_name("Google"), "Should accept 'Google'"
    assert _is_valid_company_name("Microsoft"), "Should accept 'Microsoft'"
    assert _is_valid_company_name("Amazon"), "Should accept 'Amazon'"
    assert _is_valid_company_name("Apple"), "Should accept 'Apple'"
    assert _is_valid_company_name("Meta"), "Should accept 'Meta'"
    assert _is_valid_company_name("Netflix"), "Should accept 'Netflix'"
    
    # Multi-word companies
    assert _is_valid_company_name("Goldman Sachs"), "Should accept 'Goldman Sachs'"
    assert _is_valid_company_name("JP Morgan"), "Should accept 'JP Morgan'"
    assert _is_valid_company_name("Bank of America"), "Should accept 'Bank of America'"
    
    # Companies with numbers (but alphabetic dominance)
    assert _is_valid_company_name("Adobe 2024"), "Should accept 'Adobe 2024'"
    assert _is_valid_company_name("Salesforce Q4"), "Should accept 'Salesforce Q4'"
    
    # Companies with special characters
    assert _is_valid_company_name("Procter & Gamble"), "Should accept 'Procter & Gamble'"
    assert _is_valid_company_name("AT&T"), "Should accept 'AT&T'"
    assert _is_valid_company_name("3M Company"), "Should accept '3M Company'"
    
    # Acronyms and abbreviations
    assert _is_valid_company_name("IBM"), "Should accept 'IBM'"
    assert _is_valid_company_name("KPMG"), "Should accept 'KPMG'"
    assert _is_valid_company_name("PWC"), "Should accept 'PWC'"
    assert _is_valid_company_name("EY"), "Should accept 'EY'"
    
    # Indian companies
    assert _is_valid_company_name("Tata Consultancy Services"), "Should accept 'Tata Consultancy Services'"
    assert _is_valid_company_name("Infosys"), "Should accept 'Infosys'"
    assert _is_valid_company_name("Wipro"), "Should accept 'Wipro'"
    assert _is_valid_company_name("Reliance"), "Should accept 'Reliance'"
    
    # Consulting firms
    assert _is_valid_company_name("Deloitte"), "Should accept 'Deloitte'"
    assert _is_valid_company_name("McKinsey"), "Should accept 'McKinsey'"
    assert _is_valid_company_name("BCG"), "Should accept 'BCG'"
    assert _is_valid_company_name("Bain"), "Should accept 'Bain'"
    
    print("✅ All valid company name tests passed!")


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    
    # Numbers in names (acceptable if more letters than digits)
    assert _is_valid_company_name("Adobe Systems 2024"), "Should accept company with year"
    assert not _is_valid_company_name("2024_abc"), "Should reject number-heavy pattern"
    
    # Whitespace variations
    assert _is_valid_company_name("  Google  "), "Should accept with extra whitespace"
    assert _is_valid_company_name("Microsoft\n"), "Should accept with newline"
    
    # Case variations
    assert _is_valid_company_name("GOOGLE"), "Should accept uppercase"
    assert _is_valid_company_name("google"), "Should accept lowercase"
    assert _is_valid_company_name("GoOgLe"), "Should accept mixed case"
    
    # Underscores and hyphens
    assert _is_valid_company_name("Google_India"), "Should accept underscores in real names"
    assert _is_valid_company_name("Coca-Cola"), "Should accept hyphens"
    
    # Minimum length boundary (2-char companies like EA, HP exist)
    assert _is_valid_company_name("HP"), "Should accept 2-char company names like HP"
    assert _is_valid_company_name("EA"), "Should accept 2-char company names like EA"
    assert _is_valid_company_name("IBM"), "Should accept 3-char names"
    
    print("✅ All edge case tests passed!")


def test_real_world_scenarios():
    """Test real-world scenarios from actual ingestion"""
    
    # Scenario 1: Vision model returns garbage from poorly scanned PDF
    assert not _is_valid_company_name("pdf123"), "Scenario: OCR garbage"
    assert not _is_valid_company_name("Page 1"), "Scenario: OCR picked up page number"
    assert not _is_valid_company_name("Document ID 456"), "Scenario: Document metadata"
    
    # Scenario 2: Filename-based extraction with file patterns
    assert not _is_valid_company_name("jd_final_copy"), "Scenario: Filename pattern"
    assert not _is_valid_company_name("untitled_document"), "Scenario: Default filename"
    
    # Scenario 3: Valid companies that might be confused
    assert _is_valid_company_name("Target"), "Scenario: Real company name"
    assert _is_valid_company_name("The Gap"), "Scenario: Company with article"
    assert _is_valid_company_name("Oracle"), "Scenario: Common word but real company"
    
    # Scenario 4: International companies
    assert _is_valid_company_name("Samsung"), "Scenario: Korean company"
    assert _is_valid_company_name("Sony"), "Scenario: Japanese company"
    assert _is_valid_company_name("Huawei"), "Scenario: Chinese company"
    assert _is_valid_company_name("Siemens"), "Scenario: German company"
    
    print("✅ All real-world scenario tests passed!")


if __name__ == "__main__":
    print("🧪 Running company name validation tests...\n")
    
    test_garbage_company_names()
    print()
    
    test_valid_company_names()
    print()
    
    test_edge_cases()
    print()
    
    test_real_world_scenarios()
    print()
    
    print("🎉 All tests passed! Company name validation is working correctly.")
