from __future__ import annotations

import argparse
import json
import os
import re
import base64
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime

import certifi
import ssl
import urllib3
import httpx
from llama_parse import LlamaParse
from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm

from app.config import get_settings
from app.rag import EmbeddingBackend
from app.database import PlacementDatabase
from app.utils import stable_chunk_id
from ingest.company_extractor import extract_company
from ingest.structured_extractor import StructuredExtractor
from ingest.specialization_detector import detect_specializations
from ingest.level1_mapper import map_level1_roles
from ingest.level2_extractor import extract_level2_roles
from app.role_type_classifier import classify_role_types as classify_role_types_rule
from app.llm_role_type_classifier import classify_role_types_llm
from ingest.metadata_normalize import canonicalize_company
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---------------------------------------------------------------------------
# Canonical specialization mapping & predefined Level 1 role sets
# (Single source of truth so SQL + Pinecone use identical naming)
# ---------------------------------------------------------------------------
CANONICAL_SPECIALIZATION_MAP = {
    # Normalizations / aliases
    'marketing': 'Marketing',
    'marketing and sales': 'Marketing',
    'human resources': 'Human Resources',
    'hr': 'Human Resources',
    'lean operation and systems': 'Lean Operations & Systems',
    'operations': 'Lean Operations & Systems',
    'finance': 'Finance',
    'business analytics': 'Business Analytics',
    'analytics': 'Business Analytics',
}



HYBRID_TERMS = {
    # Hybrid specialization phrase -> component specializations
    'financial analytics': ['Finance', 'Business Analytics'],
    'marketing analytics': ['Marketing', 'Business Analytics'],
    'operations analytics': ['Lean Operations & Systems', 'Business Analytics'],
    'hr analytics': ['Human Resources', 'Business Analytics'],
}

def canonicalize_specialization(raw: str) -> str:
    if not raw:
        return raw
    return CANONICAL_SPECIALIZATION_MAP.get(raw.lower().strip(), raw.strip())

def expand_hybrids(jd_text: str, specs: list[str]) -> list[str]:
    text_lower = jd_text.lower()
    augmented = set(specs)
    for term, components in HYBRID_TERMS.items():
        if term in text_lower:
            for c in components:
                augmented.add(c)
    return list(augmented)


def _load_repo_dotenv(dotenv_path: str | Path = None) -> None:
    """Load a simple .env file into os.environ if variables are not already set.

    - Does not overwrite existing environment variables.
    - Supports KEY=VALUE with optional quoted values. Ignores comments and blank lines.
    """
    try:
        if dotenv_path is None:
            dotenv_path = Path(".env")
        if isinstance(dotenv_path, str):
            dotenv_path = Path(dotenv_path)
        if not dotenv_path.exists():
            return
        for raw in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip()
            # strip surrounding quotes
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            if k and os.getenv(k) is None:
                os.environ[k] = v
    except Exception:
        # Best-effort only
        pass


# Auto-load repository .env so CLI runs pick up keys without manual export
_load_repo_dotenv()

# Import modules that need env variables AFTER loading .env
from app.navigation_map import navigation_map  # Legacy map
from app.hierarchical_navigation_map import hierarchical_navigation_map  # Enhanced map
from app.specialization_classifier import specialization_classifier

def normalize_company_name(name: str) -> str:
    """Normalize company name for consistent matching: lowercase, alphanumeric only."""
    if not name:
        return ""
    return "".join(c for c in name.lower() if c.isalnum())


_PLACEHOLDER_COMPANY_SLUGS: Set[str] = {
    "organisation",
    "organization",
    "company",
    "department",
    "purposeofthejob",
    "jobtitle",
    "na",
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


async def _extract_company_from_logo_vision(pdf_path: Path) -> Optional[str]:
    """
    Use vision model to recognize company logo in PDF.
    Only called as last resort when all other methods fail.
    Returns company name or None.
    """
    try:
        # Check if pdf2image is available
        try:
            import pdf2image
        except ImportError:
            print("⚠️ pdf2image not installed, skipping vision-based logo detection")
            print("   Install with: pip install pdf2image")
            return None
        
        print(f"🔍 Attempting vision-based logo recognition for {pdf_path.name}...")
        
        # Convert first page to image (logos typically on page 1)
        try:
            images = pdf2image.convert_from_path(
                pdf_path,
                first_page=1,
                last_page=1,
                dpi=150,  # Good balance between quality and file size
                fmt='PNG'
            )
        except Exception as e:
            print(f"⚠️ Failed to convert PDF to image: {e}")
            return None
        
        if not images:
            print("⚠️ No images extracted from PDF")
            return None
        
        # Save image to temporary file and encode to base64
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            images[0].save(tmp_path, 'PNG')
        
        try:
            with open(tmp_path, 'rb') as img_file:
                image_b64 = base64.b64encode(img_file.read()).decode('utf-8')
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        # Call OpenRouter with vision-capable model
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("⚠️ OPENROUTER_API_KEY not set, cannot use vision model")
            return None
        
        print("🤖 Calling vision model to analyze logo...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "anthropic/claude-3.5-sonnet",  # Vision-capable model
                    "messages": [{
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this job description document and identify the company name from any logos, headers, or branding.

CRITICAL RULES:
1. Return ONLY the company name, nothing else
2. If you see a company logo, return the company name
3. If no clear company branding is visible, return "NONE"
4. Do NOT return generic words like "document", "pdf", "file", "company"
5. Do NOT return file naming patterns like "pdf_123", "doc_456"
6. Do NOT make up or guess company names
7. Only return real, identifiable company names from visible branding

Examples of VALID responses:
- Google
- Microsoft
- Deloitte
- KPMG

Examples of INVALID responses (return "NONE" instead):
- document
- pdf
- company
- file_123
- unknown

Return ONLY the company name or "NONE":"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}"
                                }
                            }
                        ]
                    }],
                    "max_tokens": 50,
                    "temperature": 0.1  # Low temperature for factual extraction
                },
            )
        
        if response.status_code != 200:
            print(f"⚠️ Vision API returned status {response.status_code}: {response.text[:200]}")
            return None
        
        result = response.json()
        company = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
        # Validate the response
        if not company or company.upper() == "NONE":
            print("❌ Vision model found no company logo")
            return None
        
        # Additional validation against garbage responses
        if not _is_valid_company_name(company):
            print(f"❌ Vision model returned invalid company name: '{company}'")
            return None
        
        print(f"✅ Vision model identified company logo: {company}")
        return company
        
    except Exception as e:
        print(f"❌ Vision-based logo recognition failed: {e}")
        return None


def _fallback_company_from_filename(path: Path) -> str:
    stem = path.stem.replace("_", " ")
    # Drop common noise tokens that appear in filenames
    stem = re.sub(r"\b(copy of|jd|job description|campus|final)\b", " ", stem, flags=re.I)
    stem = re.sub(r"\s+", " ", stem).strip(" -_")
    if not stem:
        return "Unknown"
    primary = re.split(r"[-–—|]", stem)[0].strip()
    candidate = primary or stem
    return canonicalize_company(candidate) or candidate.title()


def _extract_specialization_from_text(text: str) -> Optional[str]:
    """
    Extract specialization from chunk text based on keywords.
    Returns: Marketing, Finance, Operations, Data Analytics, HR, or None
    """
    text_lower = text.lower()
    
    # Specialization keyword patterns (weighted by specificity)
    specializations = {
        'Marketing': [
            # Strong indicators
            ('digital marketing', 3), ('brand management', 3), ('marketing strategy', 3),
            ('content marketing', 3), ('social media marketing', 3), ('seo', 3), ('sem', 3),
            # Medium indicators
            ('marketing', 2), ('brand', 2), ('advertising', 2), ('campaign', 2),
            ('growth hacking', 2), ('customer acquisition', 2)
        ],
        'Finance': [
            # Strong indicators
            ('financial analyst', 3), ('chartered accountant', 3), ('ca', 3), ('cma', 3),
            ('financial planning', 3), ('audit', 3), ('taxation', 3), ('treasury', 3),
            # Medium indicators
            ('finance', 2), ('accounting', 2), ('financial', 2), ('investment', 2),
            ('budget', 2), ('revenue', 2)
        ],
        'LEAN OPERATION AND SYSTEMS': [
            # Strong indicators
            ('supply chain', 3), ('operations management', 3), ('logistics', 3),
            ('procurement', 3), ('inventory management', 3), ('process optimization', 3),
            # Medium indicators
            ('operations', 2), ('ops', 2), ('production', 2), ('manufacturing', 2),
            ('warehouse', 2)
        ],
        'Data Analytics': [
            # Strong indicators
            ('data analytics', 3), ('data science', 3), ('business intelligence', 3),
            ('data analyst', 3), ('data engineer', 3), ('machine learning', 3),
            ('sql', 3), ('python', 3), ('tableau', 3), ('power bi', 3),
            # Medium indicators
            ('analytics', 2), ('data', 2), ('reporting', 2), ('dashboard', 2)
        ],
        'HR': [
            # Strong indicators
            ('human resources', 3), ('talent acquisition', 3), ('recruitment', 3),
            ('employee relations', 3), ('learning and development', 3), ('l&d', 3),
            # Medium indicators
            ('hr', 2), ('people', 2), ('hiring', 2), ('onboarding', 2)
        ]
    }
    
    # Calculate scores for each specialization
    scores = {}
    for specialization, patterns in specializations.items():
        score = 0
        for keyword, weight in patterns:
            # Use word boundaries for accurate matching
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                score += weight
        scores[specialization] = score
    
    # Return specialization with highest score (if score > 2)
    if scores:
        best_match = max(scores.items(), key=lambda x: x[1])
        if best_match[1] >= 2:  # Minimum threshold
            return best_match[0]
    
    return None


def _read_text_from_path(path: Path) -> str:
    """
    Return raw text for a file. Supports .txt, .pdf, .docx, .doc
    For PDFs and Office docs, use LlamaParse (LLAMA_CLOUD_API_KEY).
    """
    suffix = path.suffix.lower()
    
    # Plain text files - direct read
    if suffix == ".txt":
        txt = path.read_text(errors="ignore")
        if not txt.strip():
            raise RuntimeError(f"Empty text in {path}")
        return txt

    # For PDF, DOCX, DOC - use LlamaParse which supports all formats
    supported_formats = {".pdf", ".docx", ".doc"}
    if suffix not in supported_formats:
        raise RuntimeError(f"Unsupported file format: {suffix}. Supported: .txt, .pdf, .docx, .doc")

    # Prefer LLAMA_CLOUD_API_KEY; fallback to LLAMAPARSE_API_KEY if present
    api_key = os.getenv("LLAMA_CLOUD_API_KEY") or os.getenv("LLAMAPARSE_API_KEY") or get_settings().LLAMAPARSE_API_KEY
    if not api_key:
        raise RuntimeError("LLAMA_CLOUD_API_KEY is required for PDF/DOCX ingestion with LlamaParse")

    print(f"📄 Parsing {suffix} file with LlamaParse: {path.name}")
    
    parser = LlamaParse(
        api_key=api_key,
        result_type="markdown",
        use_vendor_multimodal_model=True,
        num_workers=4,
        verbose=True,
        check_local_models=False,
    )
    
    # Harden SSL with certifi
    try:
        urllib3.util.ssl_.DEFAULT_CIPHERS += "HIGH:!DH:!aNULL"
        ssl.create_default_context(cafile=certifi.where())
        urllib3.PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=certifi.where())
    except Exception:
        pass

    docs = parser.load_data(str(path))
    if not docs:
        raise RuntimeError(f"LlamaParse produced no documents for {path}")
    
    parts: List[str] = []
    for d in docs:
        t = (getattr(d, "text", None) or "").strip()
        if t:
            parts.append(t)
    
    text = "\n\n".join(parts).strip()
    if not text:
        raise RuntimeError(f"LlamaParse returned empty text for {path}")
    
    print(f"✅ Successfully parsed {len(text)} characters from {path.name}")
    return text


def upsert_chunks_pinecone(chunks: List[Dict[str, Any]], source_file: str) -> int:
    settings = get_settings()
    if not settings.PINECONE_API_KEY or not settings.PINECONE_INDEX_NAME:
        # No Pinecone creds; skip upsert
        return len(chunks)

    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    embedder = EmbeddingBackend(settings.EMBED_MODEL)
    dim = embedder.dim

    existing = {i.name for i in pc.list_indexes()}
    if settings.PINECONE_INDEX_NAME not in existing:
        pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=dim,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.PINECONE_CLOUD, region=settings.PINECONE_REGION),
        )
    else:
        info = pc.describe_index(settings.PINECONE_INDEX_NAME)
        if info.dimension != dim:
            raise RuntimeError(f"Pinecone index dim={info.dimension} != embedding dim={dim}. Recreate index with {dim}.")

    index = pc.Index(settings.PINECONE_INDEX_NAME)

    documents = [c["chunk_text"] for c in chunks]
    embeddings = embedder.embed(documents)
    ids = [c["_id"] for c in chunks]
    metadatas = []
    for c in chunks:
        meta = {k: v for k, v in c.items() if k not in {"_id"}}
        meta["chunk_id"] = c.get("_id")
        meta["page_number"] = c.get("page_number", None)
        # sanitize: remove None values and coerce simple types only
        clean_meta: Dict[str, Any] = {}
        for k, v in meta.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                clean_meta[k] = v
            elif isinstance(v, list):
                clean_meta[k] = [x for x in v if isinstance(x, (str, int, float, bool))]
        metadatas.append(clean_meta)

    vectors = [
        {"id": id_, "values": vec.tolist(), "metadata": meta}
        for id_, vec, meta in zip(ids, embeddings, metadatas)
    ]
    try:
        index.upsert(vectors=vectors)
    except Exception as e:
        # Pinecone may return 403 Forbidden if API key or project is not authorized; don't abort ingestion
        try:
            from pinecone.core.openapi.shared.exceptions import ForbiddenException
            if isinstance(e, ForbiddenException):
                print("⚠️ Pinecone upsert forbidden (403). Continuing without vector upsert.")
                return len(ids)
        except Exception:
            pass
        # For other exceptions, log and re-raise so caller can decide
        print(f"❌ Pinecone upsert failed: {e}")
        raise
    return len(ids)


def extract_company_name(text: str) -> Optional[str]:
    """Heuristic company extractor without external LLMs.

    Strategy:
    1) Look for explicit labels like "Company:", "Employer:", "Organization:" early in the text
    2) Look for a heading like "About <Company>" (but not "About Us")
    3) Fallback: first all-uppercase heading line near the top (1–2 words)
    Returns canonicalized name or None.
    """
    import re

    head = text[:3000]  # focus on the start of the document
    lines = [ln.strip() for ln in head.splitlines() if ln.strip()]

    # 1) Labeled patterns
    labeled_patterns = [
        r"(?i)^(?:company|company name|employer|organization)\s*[:\-]\s*(.+)$",
        r"(?i)^\*?\s*(?:company|employer)\s*[:\-]\s*(.+)$",
    ]
    for pat in labeled_patterns:
        for ln in lines[:50]:  # scan first 50 non-empty lines
            m = re.match(pat, ln)
            if m:
                raw = m.group(1).strip(" \t\n\r-–—|,:;()[]{}\"'")
                if raw and len(raw) >= 2:
                    return canonicalize_company(raw)

    # 2) "About <Company>" heading (avoid "About Us")
    about_patterns = [
        r"(?i)^about\s+(?!us\b)([A-Za-z0-9&.,'\- ]{2,})\s*:?$",
        r"(?i)\babout\s+(?!us\b)([A-Za-z0-9&.,'\- ]{2,})\b",
    ]
    for pat in about_patterns:
        for ln in lines[:80]:
            m = re.search(pat, ln)
            if m:
                raw = m.group(1).strip(" \t\n\r-–—|,:;()[]{}\"'")
                # Avoid capturing generic words
                if raw.lower() not in {"company", "organization", "employer", "academy"}:
                    return canonicalize_company(raw)

    # 3) First all-uppercase heading (1-2 words)
    def is_all_caps_heading(s: str) -> bool:
        # consider only A–Z and common punctuation
        if len(s) < 3 or len(s) > 50:
            return False
        words = [w for w in re.split(r"\s+", s) if w]
        if not (1 <= len(words) <= 3):
            return False
        if any(w.lower() in {"about", "job", "description", "role", "department", "experience", "education", "join", "apprentice", "program"} for w in words):
            return False
        # 80% or more uppercase or punctuation
        letters = [ch for ch in s if ch.isalpha()]
        if not letters:
            return False
        upper = sum(1 for ch in letters if ch.isupper())
        return upper / max(1, len(letters)) >= 0.8

    for ln in lines[:40]:
        if is_all_caps_heading(ln):
            return canonicalize_company(ln)

    return None


def _split_into_chunks(text: str, chunk_size: int, chunk_overlap: int) -> List[Tuple[int, str]]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max(100, chunk_size),
        chunk_overlap=max(0, min(chunk_overlap, chunk_size // 2)),
        separators=["\n\n", "\n", ". ", "? ", "! ", "; ", ": ", ", ", " ", ""],
    )
    chunks = splitter.split_text(text)
    return list(enumerate(chunks))


def process_file(path: Path) -> Tuple[int, Optional[str]]:
    """Parse → extract company → structured extraction → chunk → embed → upsert. Returns (num_chunks, company)."""
    settings = get_settings()
    text = _read_text_from_path(path)
    preview = text[:500]
    print(f"Preview for {path.name}:\n{preview}\n{'-'*80}")

    # PRIORITY 1: Try to get company from filename first (most reliable for user-named files)
    filename_company = _fallback_company_from_filename(path)
    print(f"📝 Filename suggests company: {filename_company}")

    # PRIORITY 2: Structured extraction using LLM
    print(f"🔍 Performing structured extraction for {path.name}...")
    structured_extractor = StructuredExtractor()
    extraction = structured_extractor.extract_structured_data(text)
    
    # Initialize with safe defaults to prevent UnboundLocalError
    extraction_dict: Dict[str, Any] = {
        'specializations': [],
        'level1_roles': [],
        'level2_roles': [],
        'hierarchy_confidence': 0.0,
        'is_hybrid': False,
        'roles': []
    }
    
    structured_company: Optional[str] = None
    if extraction and extraction.company_name:
        structured_company = extraction.company_name
        print(f"✅ Structured extraction successful: {structured_company}")
        # Save structured data to JSON to get the base dictionary
        json_path = structured_extractor.save_structured_data(extraction, path.name)
        if json_path:
            print(f"💾 Saved structured data to: {json_path}")
            with open(json_path, 'r', encoding='utf-8') as jf:
                extraction_dict = json.load(jf) # Overwrite with loaded data
    else:
        print(f"⚠️ Structured extraction failed for {path.name}")

    # ALWAYS perform dynamic hierarchy extraction, even if company name extraction failed.
    # This ensures the hierarchy is processed and `extraction_dict` is populated.
    try:
        print("   🚀 Using dynamic LLM-driven hierarchy extraction...")
        # 1. Detect raw specializations
        raw_specs = detect_specializations(text)
        print(f"   📊 Raw detected specializations: {[s['specialization'] for s in raw_specs]}")

        # 2. Canonicalize & hybrid expansion
        canonical_specs = [canonicalize_specialization(s['specialization']) for s in raw_specs if s.get('specialization')]
        canonical_specs = expand_hybrids(text, canonical_specs)
        print(f"   ✅ Canonical / expanded specializations: {canonical_specs}")

        # 3. Level 1 roles
        # Use LLM-based mapper to select relevant candidates instead of all possible ones
        level1_roles = map_level1_roles(canonical_specs, text)
        print(f"   🏢 Level 1 role set (LLM selected): {level1_roles}")

        # 4. Dynamic Level 2 roles
        level2_objs = extract_level2_roles(text, level1_roles)
        level2_roles = sorted(set(o.get('level2') for o in level2_objs if o.get('level2')))
        print(f"   🔍 Level 2 dynamic roles: {level2_roles}")

        # 5. Confidence and hybrid status
        hierarchy_confidence = round(sum(s.get('confidence', 0) for s in raw_specs) / len(raw_specs), 2) if raw_specs else 0.0
        is_hybrid = len(canonical_specs) > 1
        specializations = [{"specialization": s, "confidence": None} for s in canonical_specs]

        # Augment extraction_dict with new dynamic fields
        extraction_dict['specializations'] = specializations
        extraction_dict['level1_roles'] = level1_roles
        extraction_dict['level2_roles'] = level2_roles
        extraction_dict['hierarchy_confidence'] = hierarchy_confidence
        extraction_dict['is_hybrid'] = is_hybrid

        # Augment roles with role_types (multi-label) before DB insert
        try:
            llm_map = classify_role_types_llm(extraction_dict.get("roles", []), text)
        except Exception as e:
            print(f"⚠️ LLM role type batch classification failed: {e}")
            llm_map = {}

        for role_obj in extraction_dict.get("roles", []):
            title = role_obj.get("title", "")
            specialization = role_obj.get("specialization", "")
            desc_parts = [str(role_obj.get(k, '')) for k in ("role_description", "responsibilities", "requirements")]
            description = "\n".join(desc_parts)

            # Augment with dynamic hierarchy fields
            role_obj['specializations'] = specializations
            role_obj['level1_roles'] = level1_roles
            role_obj['level2_roles'] = level2_roles
            role_obj['hierarchy_confidence'] = hierarchy_confidence
            role_obj['is_hybrid'] = is_hybrid

            role_types = llm_map.get(title)
            source = "llm"
            if not role_types:
                classifications = classify_role_types_rule(title, specialization, description)
                role_types = [c["classification"] for c in classifications]
                source = "rules" if role_types else None
                if role_types:
                    role_obj.setdefault("_role_type_debug", classifications)
            if role_types:
                role_obj["role_types"] = role_types
                if source:
                    role_obj.setdefault("_role_type_source", source)
        
        # If structured extraction was successful, insert into DB
        if structured_company:
            db = PlacementDatabase()
            success = db.insert_company_extraction(extraction_dict)
            if success:
                print(f"🗄️ Inserted structured extraction into DB: {structured_company}")
            else:
                print(f"⚠️ Failed to insert structured extraction into DB for: {structured_company}")

    except Exception as e:
        print(f"❌ Error during dynamic hierarchy extraction: {e}")
        # Ensure safe defaults on error
        extraction_dict.setdefault('specializations', [])
        extraction_dict.setdefault('level1_roles', [])
        extraction_dict.setdefault('level2_roles', [])
        extraction_dict.setdefault('hierarchy_confidence', 0.0)
        extraction_dict.setdefault('is_hybrid', False)

    # SMART COMPANY NAME RESOLUTION
    # Priority order: Structured > Filename > Vision (Logo Detection)
    # Use the most reliable source available
    
    print("\n🎯 Company Name Resolution:")
    print(f"   1. Structured extraction: {structured_company or 'None'}")
    print(f"   2. Filename suggests: {filename_company}")
    
    # Decide final company name with priority logic
    final_company_name = None
    
    # If structured extraction succeeded, trust it most (it's LLM-verified)
    if structured_company and not _is_placeholder_company(structured_company):
        final_company_name = structured_company
        print(f"   ✅ Using structured extraction: {final_company_name}")
    
    # Try filename if it looks valid (not "Unknown" or placeholder)
    elif filename_company and not _is_placeholder_company(filename_company) and filename_company.lower() != "unknown":
        final_company_name = filename_company
        print(f"   ✅ Using filename fallback: {final_company_name}")
    
    # LAST RESORT: Vision-based logo detection (only for PDFs)
    # Only attempt if all other methods failed or returned placeholders
    else:
        if path.suffix.lower() == ".pdf":
            print(f"   ⚠️ All text-based methods failed. Attempting vision-based logo detection...")
            import asyncio
            try:
                # Run async vision extraction
                vision_company = asyncio.run(_extract_company_from_logo_vision(path))
                if vision_company and _is_valid_company_name(vision_company):
                    final_company_name = vision_company
                    print(f"   ✅ Using vision-detected logo: {final_company_name}")
                else:
                    # Ultimate fallback: use filename even if it's "Unknown"
                    final_company_name = filename_company
                    print(f"   ⚠️ Vision detection failed. Using filename: {final_company_name}")
            except Exception as e:
                print(f"   ❌ Vision detection error: {e}")
                final_company_name = filename_company
                print(f"   ⚠️ Falling back to filename: {final_company_name}")
        else:
            # Non-PDF files: use filename as final fallback
            final_company_name = filename_company
            print(f"   ✅ Using filename fallback: {final_company_name}")
    
    # Canonicalize for consistency
    final_company_name = canonicalize_company(final_company_name) or final_company_name
    company_norm = normalize_company_name(final_company_name)
    print(f"   🏢 Final canonicalized company: {final_company_name}\n")

    # Specializations now handled in dynamic hierarchy above; skip duplicate extraction
    specializations = extraction_dict.get('specializations', [{'specialization': 'General'}])
    is_general = len(specializations) == 1 and specializations[0].get('specialization') == 'General'
    print(f"   ✅ Specializations (from dynamic): {[s.get('specialization') for s in specializations]}")
    
    # Hierarchical classification now dynamic via new modules; use from extraction_dict
    industry_level1 = ", ".join(extraction_dict.get('level1_roles', []) or []) or "General"
    industry_level2 = ", ".join(extraction_dict.get('level2_roles', []) or []) or "General"
    industry_full = f"{', '.join([s.get('specialization') for s in specializations])} > {industry_level1} > {industry_level2}"
    
    print(f"   ✅ Dynamic hierarchy extracted (see above)")

    # ADD TO NAVIGATION MAPS
    print("📍 Updating Navigation Maps...")
    
    # Update legacy navigation map (for backward compatibility)
    navigation_map.add_entry(
        company_name=final_company_name,
        company_norm=company_norm,
        specializations=specializations,
        source='jd'
    )
    
    # Update enhanced hierarchical navigation map
    if not is_general and industry_level1 != "General":
        primary_specialization = specializations[0]['specialization'] if specializations else "General"
        if primary_specialization != "General":
            hierarchical_navigation_map.add_entry(
                company_name=final_company_name,
                company_norm=company_norm,
                specialization=primary_specialization,
                level1=industry_level1,
                level2=industry_level2,
                source='jd'
            )

    # Chunk using RecursiveCharacterTextSplitter
    chunk_size = int(os.getenv("CHUNK_SIZE", "700"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "150"))
    enumerated = _split_into_chunks(text, chunk_size, chunk_overlap)

    # Build chunk dicts expected by upsert_chunks_pinecone
    chunks: List[Dict[str, Any]] = []
    for idx, chunk_text in enumerated:
        chunk_id = stable_chunk_id(
            source_file=path.name,
            section_id="0",
            chunk_idx=idx,
            start_char=0,
            end_char=0,
        )
        
        # Choose a primary specialization (first canonical) for filtering
        primary_specialization = specializations[0]['specialization'] if specializations else "General"

        meta: Dict[str, Any] = {
            "chunk_text": chunk_text,
            "text": chunk_text,
            "source": path.name,
            "chunk_index": idx,
            "company": final_company_name,
            "company_norm": company_norm,
            # For DB/debugging keep the full list, but also store a canonical single field used by retrieval filters
            "specializations": json.dumps(specializations),  # JSON string for DB
            "specialization": primary_specialization,       # Canonical singular for Pinecone filter
            "is_general": is_general,
            "industry_level1": industry_level1,
            "industry_level2": industry_level2,
            "industry_full": industry_full,
            "level1_roles": json.dumps(level1_roles),
            "level2_roles": json.dumps(level2_roles),
            "hierarchy_confidence": hierarchy_confidence,
            "is_hybrid": is_hybrid,
            "year": datetime.now().year,
        }
        chunks.append({"_id": chunk_id, **meta})

    n = upsert_chunks_pinecone(chunks, str(path))
    return n, final_company_name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf_dir", type=str, required=True, help="Directory containing job description files")
    args = parser.parse_args()

    # Support all common document formats
    supported_extensions = [
        "*.pdf", "*.PDF",           # PDF documents
        "*.txt", "*.TXT",           # Plain text
        "*.docx", "*.DOCX",         # Word documents (modern)
        "*.doc", "*.DOC"            # Word documents (legacy)
    ]
    
    files: List[Path] = []
    for ext in supported_extensions:
        found = sorted(Path(args.pdf_dir).glob(ext))
        files.extend(found)
        if found:
            print(f"📁 Found {len(found)} {ext.replace('*', '')} file(s)")
    
    if not files:
        print(f"⚠️ No supported files found in {args.pdf_dir}")
        print(f"Supported formats: PDF, TXT, DOCX, DOC")
        return

    print(f"\n🚀 Starting ingestion of {len(files)} file(s)...")
    print(f"Supported formats: .pdf, .txt, .docx, .doc")
    print(f"Company detection: Structured extraction → Content analysis → Filename fallback\n")

    total_chunks = 0
    companies: Set[str] = set()
    failed_files: List[Tuple[Path, str]] = []
    
    for f in tqdm(files, desc="Ingesting"):
        try:
            n, comp = process_file(f)
            total_chunks += n
            if comp:
                companies.add(comp)
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Failed to process {f.name}: {error_msg}\n")
            failed_files.append((f, error_msg))

    # Write companies.json at project root
    try:
        companies_path = Path("companies.json")
        companies_path.write_text(json.dumps(sorted(companies), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n💾 Saved {len(companies)} companies to {companies_path.resolve()}")
    except Exception as e:
        print(f"\n⚠️ Could not write companies.json: {e}")

    # SAVE NAVIGATION MAPS
    print("\n📍 Saving Navigation Maps...")
    
    # Legacy map
    navigation_map.save_to_cache()
    navigation_map.print_summary()
    
    # Enhanced hierarchical map
    hierarchical_navigation_map.save_to_cache()
    hierarchical_navigation_map.print_summary()

    print(f"\n✅ Successfully upserted {total_chunks} chunks to Pinecone")
    print(f"📊 Processed {len(files) - len(failed_files)}/{len(files)} files")
    
    if failed_files:
        print(f"\n⚠️ {len(failed_files)} file(s) failed:")
        for failed_file, error in failed_files:
            print(f"   - {failed_file.name}: {error[:100]}")


if __name__ == "__main__":
    main()



