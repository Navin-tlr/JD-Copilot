"""
Industry Validator Service
Provides database-based and LLM-based industry validation with confidence scoring
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import re
from .database import PlacementDatabase
from .llm_client import get_gemini_client
from .config import get_settings


@dataclass
class IndustryValidationResult:
    """Result of industry validation"""
    industry: str
    confidence: float
    source: str  # 'database', 'llm', or 'hybrid'
    normalized_industry: str
    alternatives: List[str] = None

    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []


class IndustryValidator:
    """Validates and normalizes industry classifications"""

    # Industry synonym mapping for normalization
    INDUSTRY_SYNONYMS = {
        # Technology
        'technology': ['tech', 'information technology', 'it', 'software', 'computing', 'digital'],
        'software': ['saas', 'software as a service', 'application development', 'programming'],
        'internet': ['web', 'online', 'e-commerce', 'digital commerce'],
        'mobile': ['app development', 'mobile apps', 'smartphone'],
        'ai': ['artificial intelligence', 'machine learning', 'ml', 'deep learning', 'neural networks'],
        'cloud computing': ['cloud', 'aws', 'azure', 'gcp', 'cloud services'],
        'cybersecurity': ['security', 'infosec', 'cyber', 'data protection'],
        'blockchain': ['crypto', 'cryptocurrency', 'distributed ledger'],
        'iot': ['internet of things', 'connected devices', 'smart devices'],
        'big data': ['data analytics', 'data science', 'business intelligence', 'bi'],

        # Finance
        'finance': ['financial services', 'banking', 'investment', 'wealth management'],
        'fintech': ['financial technology', 'digital banking', 'payment solutions'],
        'investment banking': ['ib', 'investment', 'm&a', 'mergers and acquisitions'],
        'private equity': ['pe', 'venture capital', 'vc', 'private investment'],
        'insurance': ['reinsurance', 'underwriting', 'risk management'],
        'wealth management': ['asset management', 'portfolio management', 'financial planning'],

        # Healthcare
        'healthcare': ['health', 'medical', 'pharma', 'pharmaceuticals', 'biotech', 'biotechnology'],
        'life sciences': ['biotech', 'pharmaceuticals', 'medical research'],
        'telemedicine': ['digital health', 'remote healthcare', 'virtual care'],
        'medical devices': ['medtech', 'medical equipment', 'healthtech'],

        # Consumer Goods
        'consumer goods': ['cpg', 'fast moving consumer goods', 'fmcg', 'retail'],
        'e-commerce': ['online retail', 'digital commerce', 'marketplace'],
        'fashion': ['apparel', 'clothing', 'textiles', 'luxury goods'],
        'food & beverage': ['food', 'beverage', 'nutrition', 'agritech'],

        # Manufacturing
        'manufacturing': ['industrial', 'production', 'engineering', 'automotive'],
        'automotive': ['cars', 'vehicles', 'mobility', 'transportation'],
        'aerospace': ['aviation', 'defense', 'space', 'aeronautics'],
        'chemicals': ['chemical', 'materials science', 'specialty chemicals'],

        # Energy
        'energy': ['oil & gas', 'renewable energy', 'utilities', 'power'],
        'renewable energy': ['solar', 'wind', 'clean energy', 'sustainable energy'],
        'oil & gas': ['petroleum', 'upstream', 'downstream', 'energy production'],

        # Real Estate
        'real estate': ['property', 'construction', 'realty', 'proptech'],
        'proptech': ['property technology', 'real estate tech', 'smart buildings'],

        # Education
        'education': ['edtech', 'learning', 'training', 'higher education'],
        'edtech': ['education technology', 'online learning', 'e-learning'],

        # Media & Entertainment
        'media': ['entertainment', 'content', 'publishing', 'advertising'],
        'gaming': ['video games', 'esports', 'interactive entertainment'],

        # Transportation & Logistics
        'logistics': ['supply chain', 'transportation', 'shipping', 'warehousing'],
        'aviation': ['airlines', 'airport', 'air transport'],

        # Professional Services
        'consulting': ['advisory', 'management consulting', 'strategy consulting'],
        'legal': ['law', 'legal services', 'law firm'],
        'accounting': ['audit', 'tax', 'financial reporting'],

        # Other common industries
        'nonprofit': ['ngo', 'charity', 'social enterprise'],
        'government': ['public sector', 'defense', 'public administration'],
        'agriculture': ['farming', 'agritech', 'food production']
    }

    def __init__(self):
        self.db = PlacementDatabase()
        self.llm_client = get_gemini_client()
        self.settings = get_settings()

        # Create reverse mapping for synonym lookup
        self.synonym_to_canonical = {}
        for canonical, synonyms in self.INDUSTRY_SYNONYMS.items():
            for synonym in synonyms:
                self.synonym_to_canonical[synonym.lower()] = canonical
            # Also map the canonical name to itself
            self.synonym_to_canonical[canonical.lower()] = canonical

    def normalize_industry(self, industry: str) -> str:
        """Normalize industry name using synonym mapping"""
        if not industry:
            return ""

        # Clean and lowercase
        cleaned = industry.lower().strip()

        # Check for exact synonym match
        if cleaned in self.synonym_to_canonical:
            return self.synonym_to_canonical[cleaned]

        # Check for partial matches in synonyms
        for synonym, canonical in self.synonym_to_canonical.items():
            if synonym in cleaned or cleaned in synonym:
                return canonical

        # Return original if no match found
        return industry.strip()

    def validate_database(self, industry: str) -> Tuple[bool, float, List[str]]:
        """Database-based industry validation"""
        if not industry:
            return False, 0.0, []

        try:
            # Query database for existing industries
            companies = self.db.get_companies()

            # Extract unique industries from database
            db_industries = set()
            for company in companies:
                if company.get('industry'):
                    db_industries.add(company['industry'].lower())

            normalized_input = self.normalize_industry(industry).lower()

            # Check for exact matches
            if normalized_input in db_industries:
                return True, 1.0, [industry]

            # Check for partial matches
            matches = []
            for db_industry in db_industries:
                if normalized_input in db_industry or db_industry in normalized_input:
                    matches.append(db_industry)

            if matches:
                confidence = 0.8 if len(matches) == 1 else 0.6
                return True, confidence, matches

            # No matches found
            return False, 0.0, []

        except Exception as e:
            print(f"Database validation error: {e}")
            return False, 0.0, []

    def validate_llm(self, industry: str, context: str = "") -> Tuple[str, float, List[str]]:
        """LLM-based semantic industry validation"""
        if not industry:
            return "", 0.0, []

        try:
            prompt = f"""
You are an expert in industry classification. Analyze the following industry term and provide:

1. A normalized/standardized industry name
2. A confidence score (0.0-1.0) indicating how well this fits standard industry classifications
3. Alternative industry names that could be related or synonymous

Industry term: "{industry}"
Context: "{context[:500]}"  # Truncated for brevity

Respond in this exact format:
NORMALIZED: [standardized industry name]
CONFIDENCE: [0.0-1.0]
ALTERNATIVES: [comma-separated list of alternatives]

Examples:
NORMALIZED: Information Technology
CONFIDENCE: 0.95
ALTERNATIVES: Technology, IT, Software, Computing

NORMALIZED: Financial Services
CONFIDENCE: 0.88
ALTERNATIVES: Finance, Banking, FinTech
"""

            messages = [{"role": "user", "content": prompt}]
            response = self.llm_client.chat(messages, max_tokens=200, temperature=0.1)

            if not response:
                return industry, 0.5, []

            # Parse response
            lines = response.strip().split('\n')
            normalized = industry
            confidence = 0.5
            alternatives = []

            for line in lines:
                line = line.strip()
                if line.startswith('NORMALIZED:'):
                    normalized = line.replace('NORMALIZED:', '').strip()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.replace('CONFIDENCE:', '').strip())
                        confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
                    except ValueError:
                        confidence = 0.5
                elif line.startswith('ALTERNATIVES:'):
                    alt_text = line.replace('ALTERNATIVES:', '').strip()
                    if alt_text and alt_text.lower() != 'none':
                        alternatives = [alt.strip() for alt in alt_text.split(',') if alt.strip()]

            return normalized, confidence, alternatives

        except Exception as e:
            print(f"LLM validation error: {e}")
            return industry, 0.3, []

    def validate_industry(self, industry: str, context: str = "", use_llm: bool = True) -> IndustryValidationResult:
        """Comprehensive industry validation combining database and LLM approaches"""
        if not industry:
            return IndustryValidationResult("", 0.0, "none", "")

        # Step 1: Database validation
        db_valid, db_confidence, db_matches = self.validate_database(industry)

        # Step 2: LLM validation (if enabled and needed)
        llm_normalized = ""
        llm_confidence = 0.0
        llm_alternatives = []

        if use_llm:
            llm_normalized, llm_confidence, llm_alternatives = self.validate_llm(industry, context)

        # Step 3: Combine results
        if db_valid and db_confidence >= 0.8:
            # Strong database match - use database result
            final_industry = db_matches[0] if db_matches else industry
            final_normalized = self.normalize_industry(final_industry)
            final_confidence = min(1.0, db_confidence + 0.1)  # Slight boost
            source = "database"
            alternatives = db_matches[1:] + llm_alternatives  # Combine alternatives

        elif llm_confidence >= 0.7:
            # Strong LLM match - use LLM result
            final_industry = llm_normalized
            final_normalized = self.normalize_industry(llm_normalized)
            final_confidence = llm_confidence
            source = "llm"
            alternatives = llm_alternatives

        elif db_valid:
            # Weak database match but better than LLM
            final_industry = db_matches[0] if db_matches else industry
            final_normalized = self.normalize_industry(final_industry)
            final_confidence = db_confidence
            source = "database"
            alternatives = db_matches[1:] + llm_alternatives

        else:
            # Use LLM result or fallback to normalized input
            final_industry = llm_normalized if llm_normalized else industry
            final_normalized = self.normalize_industry(final_industry)
            final_confidence = llm_confidence if llm_confidence > 0 else 0.4
            source = "llm" if llm_normalized else "fallback"
            alternatives = llm_alternatives

        # Ensure we have a valid normalized industry
        if not final_normalized:
            final_normalized = final_industry

        return IndustryValidationResult(
            industry=final_industry,
            confidence=final_confidence,
            source=source,
            normalized_industry=final_normalized,
            alternatives=alternatives[:5]  # Limit to top 5 alternatives
        )

    def validate_industries_batch(self, industries: List[str], context: str = "", use_llm: bool = True) -> List[IndustryValidationResult]:
        """Batch validate multiple industries"""
        results = []
        for industry in industries:
            result = self.validate_industry(industry, context, use_llm)
            results.append(result)
        return results

    def get_industry_suggestions(self, partial: str, limit: int = 5) -> List[str]:
        """Get industry suggestions based on partial input"""
        if not partial:
            return []

        partial_lower = partial.lower()
        suggestions = set()

        # Check database industries
        try:
            companies = self.db.get_companies()
            for company in companies:
                industry = company.get('industry', '')
                if industry and partial_lower in industry.lower():
                    suggestions.add(industry)
        except Exception:
            pass

        # Check synonym mappings
        for canonical, synonyms in self.INDUSTRY_SYNONYMS.items():
            if partial_lower in canonical.lower():
                suggestions.add(canonical)
            for synonym in synonyms:
                if partial_lower in synonym.lower():
                    suggestions.add(canonical)

        return list(suggestions)[:limit]

    def get_related_industries(self, industry: str, limit: int = 5) -> List[str]:
        """Get related industries based on semantic similarity"""
        if not industry:
            return []

        normalized = self.normalize_industry(industry)
        related = []

        # Find industries with shared synonyms
        for canonical, synonyms in self.INDUSTRY_SYNONYMS.items():
            if canonical == normalized:
                continue
            # Check if they share synonyms
            if any(syn in self.INDUSTRY_SYNONYMS.get(normalized, []) for syn in synonyms):
                related.append(canonical)

        return related[:limit]