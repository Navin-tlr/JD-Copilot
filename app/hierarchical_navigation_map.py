"""
Enhanced Navigation Map with Hierarchical Industry Support
Stores: Specialization → Level 1 → Level 2 mappings per company
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
import json
from pathlib import Path
from datetime import datetime


@dataclass
class IndustryHierarchy:
    """Industry classification hierarchy for a role/company"""
    specialization: str  # Marketing, Finance, Operations, HR, Analytics
    level1: str  # FMCG, Investment Banking, Supply Chain, etc.
    level2: str  # Beauty & Personal Care, M&A Capital Markets, etc.
    
    def to_dict(self) -> dict:
        return {
            'specialization': self.specialization,
            'level1': self.level1,
            'level2': self.level2
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'IndustryHierarchy':
        return cls(
            specialization=data['specialization'],
            level1=data['level1'],
            level2=data['level2']
        )
    
    def __hash__(self):
        return hash((self.specialization, self.level1, self.level2))
    
    def __eq__(self, other):
        if not isinstance(other, IndustryHierarchy):
            return False
        return (self.specialization == other.specialization and 
                self.level1 == other.level1 and 
                self.level2 == other.level2)


@dataclass
class CompanyEntry:
    """Enhanced company entry with hierarchical industry data"""
    display_name: str
    company_norm: str
    specializations: Set[str]  # Top-level: Marketing, Finance, etc.
    industry_hierarchies: Set[IndustryHierarchy]  # Full hierarchy data
    role_count: int
    sources: Dict[str, int] = field(default_factory=dict)
    is_general: bool = False
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            'display_name': self.display_name,
            'company_norm': self.company_norm,
            'specializations': sorted(list(self.specializations)),
            'industry_hierarchies': [h.to_dict() for h in self.industry_hierarchies],
            'role_count': self.role_count,
            'sources': self.sources,
            'is_general': self.is_general,
            'last_updated': self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CompanyEntry':
        hierarchies = set()
        for h_data in data.get('industry_hierarchies', []):
            hierarchies.add(IndustryHierarchy.from_dict(h_data))
        
        return cls(
            display_name=data['display_name'],
            company_norm=data['company_norm'],
            specializations=set(data['specializations']),
            industry_hierarchies=hierarchies,
            role_count=data['role_count'],
            sources=data.get('sources', {}),
            is_general=data.get('is_general', False),
            last_updated=data.get('last_updated', datetime.now().isoformat())
        )


class HierarchicalNavigationMap:
    """
    Enhanced navigation map with full industry hierarchy support.
    
    Structure:
        Specialization (Marketing, Finance, Operations, HR, Analytics)
            └── Level 1 (FMCG, Investment Banking, Supply Chain, etc.)
                └── Level 2 (Beauty & Personal Care, M&A Capital Markets, etc.)
    """
    
    # Fixed specialization taxonomy (use DB canonical values)
    VALID_SPECIALIZATIONS = {
        "Marketing",
        "Finance",
        "LEAN OPERATION AND SYSTEMS",
        "Analytics",
        "HR",
        "General"
    }
    
    # Level 1 options per specialization
    LEVEL1_OPTIONS = {
        "Marketing": [
            "FMCG", "B2B Sales", "Market Research", "Digital Marketing",
            "Content Creation", "Retail & E-Commerce"
        ],
        "Finance": [
            "Asset Management", "Portfolio Management", "Retail Banking",
            "Investment Banking", "Corporate Finance", "Wealth Management"
        ],
        "LEAN OPERATION AND SYSTEMS": [
            "IT & Technology", "Supply Chain", "Logistics", "Process Management",
            "Project Management", "ERP", "Manufacturing"
        ],
        "HR": [
            "Talent Acquisition", "People Operations", "Organizational Development",
            "Employee Relations", "Compensation & Benefits", "Learning & Development"
        ],
        "Analytics": [
            "Business Analytics", "Data Science", "Business Intelligence",
            "Predictive Analytics", "Data Engineering", "Reporting & Insights"
        ]
    }
    
    def __init__(self, cache_path: str = "data/hierarchical_navigation_map.json"):
        self.cache_path = Path(cache_path)
        self.map: Dict[str, CompanyEntry] = {}
        self._load_from_cache()
    
    def add_entry(
        self,
        company_name: str,
        company_norm: str,
        specialization: str,
        level1: str,
        level2: str,
        source: str = "jd"
    ):
        """
        Add or update company with full hierarchy.
        
        Args:
            company_name: Display name
            company_norm: Normalized name
            specialization: Marketing, Finance, Operations, HR, Analytics
            level1: Industry subcategory (FMCG, Investment Banking, etc.)
            level2: Specific details (Beauty & Personal Care, etc.)
            source: Data source
        """
        # Validate specialization
        if specialization not in self.VALID_SPECIALIZATIONS:
            print(f"⚠️ Invalid specialization '{specialization}', defaulting to General")
            specialization = "General"
        
        # Create hierarchy object
        hierarchy = IndustryHierarchy(
            specialization=specialization,
            level1=level1,
            level2=level2
        )
        
        if company_norm not in self.map:
            # New entry
            self.map[company_norm] = CompanyEntry(
                display_name=company_name,
                company_norm=company_norm,
                specializations={specialization},
                industry_hierarchies={hierarchy},
                role_count=1,
                sources={source: 1},
                is_general=(specialization == "General")
            )
            print(f"✅ Navigation Map: Added {company_name} → {specialization} > {level1} > {level2}")
        else:
            # Update existing
            entry = self.map[company_norm]
            entry.specializations.add(specialization)
            entry.industry_hierarchies.add(hierarchy)
            entry.role_count += 1
            entry.sources[source] = entry.sources.get(source, 0) + 1
            entry.is_general = entry.is_general or (specialization == "General")
            entry.last_updated = datetime.now().isoformat()
            print(f"🔄 Navigation Map: Updated {company_name} → {specialization} > {level1} > {level2}")
    
    def get_companies_by_hierarchy(
        self,
        specialization: Optional[str] = None,
        level1: Optional[str] = None,
        level2: Optional[str] = None
    ) -> List[str]:
        """
        Get companies matching hierarchy filter.
        
        Args:
            specialization: Filter by specialization
            level1: Filter by Level 1 category
            level2: Filter by Level 2 (partial match)
        
        Returns:
            List of company names
        """
        matches = []
        
        for entry in self.map.values():
            # Check if entry matches filters
            for hierarchy in entry.industry_hierarchies:
                if specialization and hierarchy.specialization != specialization:
                    continue
                if level1 and hierarchy.level1.lower() != level1.lower():
                    continue
                if level2 and level2.lower() not in hierarchy.level2.lower():
                    continue
                
                matches.append(entry.display_name)
                break  # Don't add same company multiple times
        
        return sorted(set(matches))
    
    def get_hierarchy_options(self, specialization: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get available Level 1 options, optionally filtered by specialization.
        
        Returns:
            {specialization: [level1_options]}
        """
        if specialization:
            return {specialization: self.LEVEL1_OPTIONS.get(specialization, [])}
        
        return self.LEVEL1_OPTIONS.copy()
    
    def get_company_hierarchies(self, company: str) -> List[IndustryHierarchy]:
        """Get all industry hierarchies for a company"""
        company_norm = self._normalize_company(company)
        if company_norm in self.map:
            return sorted(
                list(self.map[company_norm].industry_hierarchies),
                key=lambda h: (h.specialization, h.level1, h.level2)
            )
        return []
    
    def get_stats(self) -> Dict:
        """Get navigation map statistics with hierarchy breakdown"""
        stats = {
            'total_companies': len(self.map),
            'by_specialization': {},
            'by_level1': {},
            'sources': {}
        }
        
        # Count by specialization
        for entry in self.map.values():
            for spec in entry.specializations:
                stats['by_specialization'][spec] = stats['by_specialization'].get(spec, 0) + 1
            
            # Count by Level 1
            for hierarchy in entry.industry_hierarchies:
                key = f"{hierarchy.specialization} > {hierarchy.level1}"
                stats['by_level1'][key] = stats['by_level1'].get(key, 0) + 1
            
            # Count sources
            for source, count in entry.sources.items():
                stats['sources'][source] = stats['sources'].get(source, 0) + count
        
        return stats
    
    def save_to_cache(self):
        """Persist enhanced navigation map"""
        cache_data = {
            company_norm: entry.to_dict()
            for company_norm, entry in self.map.items()
        }
        
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        print(f"💾 Hierarchical Navigation Map saved: {len(self.map)} companies")
    
    def _load_from_cache(self):
        """Load navigation map from disk"""
        if not self.cache_path.exists():
            print("📍 No hierarchical navigation map cache found. Will build during ingestion.")
            return
        
        try:
            with open(self.cache_path, 'r') as f:
                cache_data = json.load(f)
            
            for company_norm, data in cache_data.items():
                self.map[company_norm] = CompanyEntry.from_dict(data)
            
            print(f"✅ Hierarchical Navigation Map loaded: {len(self.map)} companies")
        except Exception as e:
            print(f"⚠️ Failed to load hierarchical navigation map: {e}")
            self.map = {}
    
    def print_summary(self):
        """Print human-readable summary"""
        print("\n" + "="*70)
        print("📍 HIERARCHICAL NAVIGATION MAP SUMMARY")
        print("="*70)
        
        stats = self.get_stats()
        print(f"\n📊 Total Companies: {stats['total_companies']}")
        
        print("\n🏢 Companies by Specialization:")
        for spec, count in sorted(stats['by_specialization'].items()):
            print(f"  • {spec}: {count} companies")
        
        print("\n🏭 Top Industries (Specialization > Level 1):")
        sorted_level1 = sorted(stats['by_level1'].items(), key=lambda x: x[1], reverse=True)[:10]
        for industry, count in sorted_level1:
            print(f"  • {industry}: {count} roles")
        
        print("\n📁 Data Sources:")
        for source, count in sorted(stats['sources'].items()):
            print(f"  • {source}: {count} documents")
        
        print("\n" + "="*70 + "\n")
    
    def _normalize_company(self, company: str) -> str:
        """Normalize company name for consistent lookup"""
        return company.lower().replace(" ", "").replace("'", "").replace("-", "")


# Global instance
hierarchical_navigation_map = HierarchicalNavigationMap()
