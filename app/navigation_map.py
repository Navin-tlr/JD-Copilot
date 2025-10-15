"""
Navigation Map - Fast in-memory index of Company → Specializations mappings.
Built during ingestion, used by agents for instant validation and suggestions.
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
import json
from pathlib import Path
from datetime import datetime


@dataclass
class CompanyEntry:
    """Company entry in navigation map."""
    display_name: str
    company_norm: str
    specializations: Set[str]
    role_count: int
    sources: Dict[str, int] = field(default_factory=dict)
    is_general: bool = False
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            'display_name': self.display_name,
            'company_norm': self.company_norm,
            'specializations': sorted(list(self.specializations)),
            'role_count': self.role_count,
            'sources': self.sources,
            'is_general': self.is_general,
            'last_updated': self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CompanyEntry':
        return cls(
            display_name=data['display_name'],
            company_norm=data['company_norm'],
            specializations=set(data['specializations']),
            role_count=data['role_count'],
            sources=data.get('sources', {}),
            is_general=data.get('is_general', False),
            last_updated=data.get('last_updated', datetime.now().isoformat())
        )


class NavigationMap:
    """
    In-memory index of Company → [Specializations] mappings.
    Provides instant validation and smart suggestions.
    
    Specializations (Fixed Taxonomy):
    - Marketing
    - Finance
    - Operations
    - Analytics
    - HR
    - General (open to all specializations)
    """
    
    # Fixed specialization taxonomy
    VALID_SPECIALIZATIONS = {
        "Marketing",
        "Finance",
        "Operations",
        "Analytics",
        "HR",
        "General"
    }
    
    def __init__(self, cache_path: str = "data/navigation_map.json"):
        self.cache_path = Path(cache_path)
        self.map: Dict[str, CompanyEntry] = {}
        self._load_from_cache()
    
    def normalize_company(self, company: Optional[str]) -> str:
        """Public helper so other modules can share normalization strategy."""
        return self._normalize_company(company) if company else ""

    def add_entry(
        self,
        company_name: str,
        company_norm: str,
        specializations: List[str],
        source: str = "jd"
    ):
        """
        Add or update company entry with specializations.
        
        Args:
            company_name: Display name (e.g., "Honasa Consumer Limited")
            company_norm: Normalized name (e.g., "honasaconsumerlimited")
            specializations: List like ["Marketing", "Operations"] or ["General"]
            source: Data source (jd, interview, alumni, gd_topic)
        """
        # Validate and normalize specializations (CASE-INSENSITIVE)
        validated_specs = set()
        for spec in specializations:
            # Normalize casing - handle special cases
            spec_normalized = spec.strip()
            
            # Case-insensitive matching against valid specializations
            matched = False
            for valid_spec in self.VALID_SPECIALIZATIONS:
                if spec_normalized.lower() == valid_spec.lower():
                    validated_specs.add(valid_spec)  # Use the canonical form
                    matched = True
                    break
            
            if not matched:
                print(f"⚠️ Invalid specialization '{spec}' for {company_name}, ignoring")
        
        # FALLBACK TO GENERAL if no valid specializations
        if not validated_specs:
            print(f"⚠️ No valid specializations for {company_name}, defaulting to General")
            validated_specs = {"General"}
        
        # Check if General
        is_general = "General" in validated_specs
        
        if company_norm not in self.map:
            # New entry
            self.map[company_norm] = CompanyEntry(
                display_name=company_name,
                company_norm=company_norm,
                specializations=validated_specs,
                role_count=1,
                sources={source: 1},
                is_general=is_general
            )
            spec_display = ', '.join(sorted(validated_specs))
            print(f"✅ Navigation Map: Added {company_name} → [{spec_display}]")
        else:
            # Update existing entry
            entry = self.map[company_norm]
            entry.specializations.update(validated_specs)
            entry.role_count += 1
            entry.sources[source] = entry.sources.get(source, 0) + 1
            entry.is_general = entry.is_general or is_general
            entry.last_updated = datetime.now().isoformat()
            spec_display = ', '.join(sorted(entry.specializations))
            print(f"🔄 Navigation Map: Updated {company_name} → [{spec_display}]")
    
    def exists(
        self,
        company: str,
        specialization: Optional[str] = None
    ) -> bool:
        """
        Check if company has roles for this specialization.
        
        Returns True if:
        1. Company has exact specialization match
        2. Company has "General" roles (matches all queries)
        
        Args:
            company: Company name (normalized internally)
            specialization: Target specialization or None
        """
        company_norm = self._normalize_company(company)
        
        if company_norm not in self.map:
            return False
        
        entry = self.map[company_norm]
        
        # Company exists without specialization check
        if not specialization:
            return True
        
        # General roles match all specializations
        if entry.is_general:
            return True
        
        # Case-insensitive specialization match
        spec_lower = specialization.strip().lower()
        for entry_spec in entry.specializations:
            if entry_spec.lower() == spec_lower:
                return True
        
        return False
    
    def get_specializations(self, company: str) -> List[str]:
        """Get all specializations for a company."""
        company_norm = self._normalize_company(company)
        if company_norm in self.map:
            return sorted(self.map[company_norm].specializations)
        return []
    
    def get_companies_by_specialization(
        self,
        specialization: str,
        source: Optional[str] = None
    ) -> List[str]:
        """
        Get all companies hiring for a specialization.
        Includes companies with "General" roles.
        
        Args:
            specialization: Target specialization
            source: Optional filter by source (jd, interview, etc.)
        """
        # Case-insensitive specialization matching
        spec_lower = specialization.strip().lower()
        matches = []
        
        for entry in self.map.values():
            # Skip if source filter doesn't match
            if source and (source not in entry.sources or entry.sources[source] == 0):
                continue
            
            # Match if has spec OR is General (case-insensitive)
            has_spec = any(s.lower() == spec_lower for s in entry.specializations)
            if entry.is_general or has_spec:
                matches.append(entry.display_name)
        
        return sorted(matches)
    
    def suggest_alternatives(
        self,
        company: str,
        specialization: str
    ) -> Dict[str, any]:
        """
        Suggest alternatives if company+specialization doesn't exist.
        
        Returns:
            {
                'exists': bool,
                'company_exists': bool,
                'alternatives': {
                    'same_company_other_specs': [...],
                    'other_companies_same_spec': [...]
                }
            }
        """
        company_norm = self._normalize_company(company)
        # Case-insensitive specialization matching
        spec_lower = specialization.strip().lower()
        
        result = {
            'exists': False,
            'company_exists': company_norm in self.map,
            'alternatives': {}
        }
        
        # Check if company exists
        if company_norm in self.map:
            entry = self.map[company_norm]
            
            # If General, it matches everything
            if entry.is_general:
                result['exists'] = True
                return result
            
            # Case-insensitive exact spec match
            has_spec = any(s.lower() == spec_lower for s in entry.specializations)
            if has_spec:
                result['exists'] = True
                return result
            
            # Suggest other specializations from same company
            result['alternatives']['same_company_other_specs'] = sorted(
                list(entry.specializations)
            )
        
        # Find other companies with this specialization (case-insensitive)
        other_companies = self.get_companies_by_specialization(specialization)
        if other_companies:
            # Exclude the queried company
            display_name = self.map[company_norm].display_name if company_norm in self.map else company
            other_companies = [c for c in other_companies if c != display_name]
            if other_companies:
                result['alternatives']['other_companies_same_spec'] = other_companies[:5]
        
        return result
    
    def get_all_companies(self) -> List[str]:
        """Get all companies in the map."""
        return sorted([entry.display_name for entry in self.map.values()])
    
    def get_all_specializations(self) -> List[str]:
        """Get all unique specializations across all companies."""
        all_specs = set()
        for entry in self.map.values():
            all_specs.update(entry.specializations)
        return sorted(all_specs)
    
    def get_stats(self) -> Dict:
        """Get navigation map statistics."""
        return {
            'total_companies': len(self.map),
            'total_specializations': len(self.get_all_specializations()),
            'companies_by_specialization': {
                spec: len(self.get_companies_by_specialization(spec))
                for spec in self.VALID_SPECIALIZATIONS
            },
            'sources': self._get_source_stats()
        }
    
    def _get_source_stats(self) -> Dict[str, int]:
        """Get total counts per source."""
        stats = {}
        for entry in self.map.values():
            for source, count in entry.sources.items():
                stats[source] = stats.get(source, 0) + count
        return stats
    
    def save_to_cache(self):
        """Persist navigation map to disk."""
        cache_data = {
            company_norm: entry.to_dict()
            for company_norm, entry in self.map.items()
        }
        
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        print(f"💾 Navigation Map saved: {len(self.map)} companies")
    
    def _load_from_cache(self):
        """Load navigation map from disk."""
        if not self.cache_path.exists():
            print("📍 No navigation map cache found. Will build during ingestion.")
            return
        
        try:
            with open(self.cache_path, 'r') as f:
                cache_data = json.load(f)
            
            for company_norm, data in cache_data.items():
                self.map[company_norm] = CompanyEntry.from_dict(data)
            
            print(f"✅ Navigation Map loaded: {len(self.map)} companies")
        except Exception as e:
            print(f"⚠️ Failed to load navigation map: {e}")
            self.map = {}
    
    def print_summary(self):
        """Print human-readable summary."""
        print("\n" + "="*70)
        print("📍 NAVIGATION MAP SUMMARY")
        print("="*70)
        
        stats = self.get_stats()
        print(f"\n📊 Total Companies: {stats['total_companies']}")
        print(f"📊 Active Specializations: {stats['total_specializations']}")
        
        print("\n🏢 Companies by Specialization:")
        for spec in sorted(self.VALID_SPECIALIZATIONS):
            count = stats['companies_by_specialization'].get(spec, 0)
            if count > 0:
                companies = self.get_companies_by_specialization(spec)[:3]
                print(f"  • {spec}: {count} companies")
                if companies:
                    print(f"    → {', '.join(companies)}" + 
                          (f" (+{count-len(companies)} more)" if count > len(companies) else ""))
        
        print("\n📁 Data Sources:")
        for source, count in sorted(stats['sources'].items()):
            print(f"  • {source}: {count} documents")
        
        print("\n" + "="*70 + "\n")
    
    def _normalize_company(self, company: str) -> str:
        """Normalize company name for consistent lookup."""
        return company.lower().replace(" ", "").replace("'", "").replace("-", "")


# Global instance
navigation_map = NavigationMap()
