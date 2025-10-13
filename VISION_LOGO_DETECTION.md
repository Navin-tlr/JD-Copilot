# Vision-Based Logo Detection

## Overview

The ingestion pipeline now includes **vision-based logo recognition** as a final fallback method for company name extraction. This feature uses AI vision models to identify company logos in PDF documents when all text-based methods fail.

## Company Detection Priority

The system uses a 4-tier detection strategy (in order of priority):

1. **Structured Extraction** (Highest Priority)
   - LLM-based extraction from document text
   - Most reliable when company name appears in text
   
2. **Content Analysis**
   - Regex pattern matching in document text
   - Detects explicit company name mentions
   
3. **Filename Detection**
   - Extracts company name from filename
   - Works when you name files like `Google_SDE_2024.pdf`
   
4. **Vision-Based Logo Detection** (Final Fallback)
   - Uses Claude 3.5 Sonnet vision model via OpenRouter
   - Analyzes first page of PDF for company logos
   - **Only triggered if all text-based methods fail**

## How It Works

```python
# When all text-based methods fail:
if path.suffix.lower() == ".pdf":
    vision_company = await _extract_company_from_logo_vision(path)
    # Returns: "Google" (from logo) or None
```

### Vision Model Behavior

The vision model:
- Converts PDF first page to image (150 DPI)
- Sends image to Claude 3.5 Sonnet via OpenRouter API
- Returns company name from visible branding/logos
- Returns "NONE" if no clear branding found

### Garbage Detection

The system validates all extracted company names to prevent false positives:

**Rejected patterns:**
- File-related: `pdf`, `pdf_123`, `document`, `file`
- Numbers: `123`, `456`
- Generic: `company`, `organization`, `test`, `sample`
- Incomplete: Single letters, pure numbers
- Number-heavy: More digits than letters (e.g., `123abc`)

**Example:**
```python
_is_valid_company_name("pdf_123")    # ❌ False (garbage)
_is_valid_company_name("Google")     # ✅ True (valid)
_is_valid_company_name("document")   # ❌ False (generic)
_is_valid_company_name("Microsoft")  # ✅ True (valid)
```

## Setup

### 1. Install Optional Dependencies

Vision-based detection requires `pdf2image`:

```bash
# Install Python package
pip install pdf2image pillow

# Install system dependency (macOS)
brew install poppler

# Install system dependency (Ubuntu/Debian)
sudo apt-get install poppler-utils

# Install system dependency (Windows)
# Download poppler binaries from: https://github.com/oschwartz10612/poppler-windows/releases
```

### 2. Configure OpenRouter API Key

The vision model uses OpenRouter's Claude 3.5 Sonnet:

```bash
# Add to .env file
OPENROUTER_API_KEY=your_api_key_here
```

Get your API key from: https://openrouter.ai/

### 3. Verify Installation

```bash
# Test if pdf2image is working
python -c "import pdf2image; print('✅ pdf2image installed')"

# If not installed, the system will gracefully skip vision detection
```

## Usage

### Automatic Detection

Vision detection happens automatically during ingestion:

```bash
python -m ingest.pipeline --pdf_dir data/jds
```

**Console output:**
```
🎯 Company Name Resolution:
   1. Structured extraction: None
   2. Content extraction: None
   3. Filename suggests: Unknown
   ⚠️ All text-based methods failed. Attempting vision-based logo detection...
   🔍 Attempting vision-based logo recognition for Mystery_Company.pdf...
   🤖 Calling vision model to analyze logo...
   ✅ Vision model identified company logo: Deloitte
   ✅ Using vision-detected logo: Deloitte
   🏢 Final canonicalized company: Deloitte
```

### Testing Vision Detection

Create test cases with logo-only PDFs:

```bash
# Test 1: PDF with logo but no text mention
# File: test_logo_only.pdf
# Expected: Company name from logo

# Test 2: PDF with no logo, bad filename
# File: unknown_123.pdf
# Expected: Fallback to "unknown_123" or "Unknown"

# Test 3: PDF with logo + filename
# File: Google_JD_2024.pdf (logo present)
# Expected: Uses filename (higher priority than vision)
```

## Performance

- **Speed:** Vision detection adds ~3-5 seconds per PDF
- **Accuracy:** High accuracy for clear, standard company logos
- **Cost:** ~$0.003 per image (OpenRouter Claude 3.5 Sonnet pricing)
- **Trigger Rate:** Only runs when all text-based methods fail

## Limitations

1. **PDF Only:** Vision detection only works for `.pdf` files (not `.docx`, `.txt`)
2. **First Page Only:** Only analyzes the first page (logos typically on page 1)
3. **Clear Logos Required:** Works best with standard, recognizable company logos
4. **API Dependency:** Requires OpenRouter API key and internet connectivity
5. **Optional Dependency:** Requires `pdf2image` and `poppler` system library

## Troubleshooting

### Vision detection not running

**Problem:** Vision detection is skipped

**Solution:**
```bash
# Check if pdf2image is installed
pip install pdf2image

# Check system dependencies
# macOS:
brew list poppler  # Should show installed

# Linux:
dpkg -l | grep poppler-utils
```

### "Failed to convert PDF to image"

**Problem:** `pdf2image.exceptions.PDFInfoNotInstalledError`

**Solution:**
```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows - add poppler bin folder to PATH
```

### "OPENROUTER_API_KEY not set"

**Problem:** Vision model cannot be called

**Solution:**
```bash
# Add to .env file
echo "OPENROUTER_API_KEY=sk-or-v1-..." >> .env
```

### False positives (garbage company names)

**Problem:** Vision model returns "document" or "pdf_123"

**Solution:** The validation system should catch these automatically. If not, they will be logged:

```
⚠️ Rejected garbage company name: 'pdf_123' (matched pattern: ^pdf\b)
```

If validation fails, report the false positive pattern for addition to the garbage detection rules.

## Best Practices

1. **Name your files properly:** Use descriptive filenames like `Google_SDE_2024.pdf`
   - This avoids unnecessary vision API calls
   - Filename detection is faster and more reliable

2. **Monitor vision detection logs:** Check console output for vision trigger frequency
   - High frequency = need better filename conventions
   - Low frequency = system is working efficiently

3. **Batch processing:** Vision detection is async and won't block the ingestion pipeline
   - Failed vision attempts fall back gracefully to filename

4. **Cost optimization:** Vision detection adds cost (~$0.003/image)
   - Use filename-based naming to minimize vision API calls
   - Vision is only called as last resort

## Example Scenarios

### Scenario 1: Filename-based (No Vision)
```
File: Google_Software_Engineer_2024.pdf
Content: "We are hiring..." (no company mention)

Result: Uses "Google" from filename (no vision needed)
Cost: $0
```

### Scenario 2: Vision Fallback
```
File: JD_Final_Version_2.pdf
Content: "Join our team..." (no company mention)
Logo: [Deloitte logo visible]

Result: Vision detects "Deloitte" from logo
Cost: ~$0.003
```

### Scenario 3: Complete Failure
```
File: unknown_document.pdf
Content: "Hiring for multiple roles..." (no company mention)
Logo: None visible

Result: Falls back to "unknown_document" or "Unknown"
Cost: ~$0.003 (vision attempted but found nothing)
```

## API Configuration

Vision detection uses Claude 3.5 Sonnet via OpenRouter:

```python
{
  "model": "anthropic/claude-3.5-sonnet",
  "max_tokens": 50,
  "temperature": 0.1  # Low temp for factual extraction
}
```

**Why Claude 3.5 Sonnet?**
- Best-in-class vision capabilities
- High accuracy for logo recognition
- Supports detailed instructions for garbage filtering

## Future Enhancements

Potential improvements:

1. **Local Vision Models:** Use local models (e.g., LLaVA) to eliminate API costs
2. **Multi-page Analysis:** Scan all pages for logos (currently first page only)
3. **Logo Database:** Cache known logos for faster recognition
4. **OCR Fallback:** Extract text from images before vision (cheaper)
5. **Confidence Scoring:** Return confidence level with company name

## Related Files

- `ingest/pipeline.py` - Main ingestion logic with vision integration
- `ingest/company_extractor.py` - Text-based company extraction
- `ingest/structured_extractor.py` - LLM-based structured extraction
- `app/config.py` - OpenRouter API configuration

## Support

For issues or questions:
1. Check console logs for detailed error messages
2. Verify `pdf2image` and `poppler` are installed correctly
3. Ensure `OPENROUTER_API_KEY` is set in `.env`
4. Review validation logs for garbage detection patterns
