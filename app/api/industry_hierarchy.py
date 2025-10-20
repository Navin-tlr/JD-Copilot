"""
Industry Hierarchy Selector API
Provides endpoints for > trigger UI to show hierarchical industry selection
"""

from typing import Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.hierarchical_navigation_map import hierarchical_navigation_map

router = APIRouter(prefix="/api/industry-hierarchy", tags=["industry-hierarchy"])


class HierarchyLevel1Response(BaseModel):
    """Level 1 options under a specialization"""
    specialization: str
    level1_options: List[str]
    company_count: int


class HierarchySelectionResponse(BaseModel):
    """Response for hierarchy selection"""
    specialization: Optional[str] = None
    level1: Optional[str] = None
    level2: Optional[str] = None
    companies: List[str]
    count: int


@router.get("/specializations")
async def get_specializations() -> Dict[str, int]:
    """
    Get all available specializations with company counts.
    
    Used for initial > trigger menu.
    
    Returns:
        {
            "Marketing": 25,
            "Finance": 18,
            "LEAN OPERATION AND SYSTEMS": 30,
            ...
        }
    """
    stats = hierarchical_navigation_map.get_stats()
    return stats.get('by_specialization', {})


@router.get("/level1-options/{specialization}")
async def get_level1_options(specialization: str) -> HierarchyLevel1Response:
    """
    Get Level 1 options for a specialization.
    
    Example:
        GET /api/industry-hierarchy/level1-options/Marketing
        
        Returns:
        {
            "specialization": "Marketing",
            "level1_options": ["FMCG", "B2B Sales", "Digital Marketing", ...],
            "company_count": 25
        }
    """
    options = hierarchical_navigation_map.get_hierarchy_options(specialization)
    level1_list = options.get(specialization, [])
    
    # Get company count for this specialization
    companies = hierarchical_navigation_map.get_companies_by_hierarchy(
        specialization=specialization
    )
    
    return HierarchyLevel1Response(
        specialization=specialization,
        level1_options=level1_list,
        company_count=len(companies)
    )


@router.get("/companies")
async def get_companies_by_hierarchy(
    specialization: Optional[str] = None,
    level1: Optional[str] = None,
    level2: Optional[str] = None
) -> HierarchySelectionResponse:
    """
    Get companies matching hierarchy filters.
    
    Query parameters:
        - specialization: Marketing, Finance, LEAN OPERATION AND SYSTEMS, HR, Analytics
        - level1: FMCG, Investment Banking, Supply Chain, etc.
        - level2: Partial match on Level 2 (e.g., "Beauty")
    
    Example:
        GET /api/industry-hierarchy/companies?specialization=Marketing&level1=FMCG
        
        Returns companies in FMCG Marketing category
    """
    companies = hierarchical_navigation_map.get_companies_by_hierarchy(
        specialization=specialization,
        level1=level1,
        level2=level2
    )
    
    return HierarchySelectionResponse(
        specialization=specialization,
        level1=level1,
        level2=level2,
        companies=companies,
        count=len(companies)
    )


@router.get("/company/{company_name}/hierarchies")
async def get_company_hierarchies(company_name: str) -> List[Dict[str, str]]:
    """
    Get all industry hierarchies for a specific company.
    
    Example:
        GET /api/industry-hierarchy/company/Honasa Consumer Limited/hierarchies
        
        Returns:
        [
            {
                "specialization": "Marketing",
                "level1": "FMCG",
                "level2": "Beauty & Personal Care"
            }
        ]
    """
    hierarchies = hierarchical_navigation_map.get_company_hierarchies(company_name)
    return [h.to_dict() for h in hierarchies]


@router.get("/stats")
async def get_hierarchy_stats() -> Dict:
    """
    Get comprehensive statistics about industry hierarchies.
    
    Returns:
        {
            "total_companies": 75,
            "by_specialization": {...},
            "by_level1": {...},
            "sources": {...}
        }
    """
    return hierarchical_navigation_map.get_stats()
