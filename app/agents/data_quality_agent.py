"""
Data Quality Agent - Validates retrieval results and detects inconsistencies.
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class QualityReport:
    """Report on retrieved data quality."""
    total_snippets: int
    snippets_per_source: Dict[str, int]
    companies_found: List[str]
    data_gaps_confirmed: List[str]
    inconsistencies: List[str]
    confidence_score: float
    recommendations: List[str]


class DataQualityAgent:
    """Validates retrieval results and provides recommendations."""
    
    def validate(
        self,
        retrieval_results: Dict,
        expected_companies: List[str],
        expected_sources: List[str]
    ) -> QualityReport:
        """
        Validate retrieval results quality.
        
        Args:
            retrieval_results: Results from retrieval agent
            expected_companies: Companies we expected to find
            expected_sources: Sources we expected to query
        
        Returns:
            QualityReport with validation results
        """
        
        # Count snippets per source
        snippets_per_source = {}
        total_snippets = 0
        companies_found = set()
        
        for source_type, result in retrieval_results.items():
            count = result.count if hasattr(result, 'count') else len(result.get('snippets', []))
            snippets_per_source[source_type] = count
            total_snippets += count
            
            # Extract companies from snippets
            snippets = result.snippets if hasattr(result, 'snippets') else result.get('snippets', [])
            for snippet in snippets:
                company = snippet.get('metadata', {}).get('company', '')
                if company:
                    companies_found.add(company.lower())
        
        # Identify data gaps
        data_gaps_confirmed = []
        for source in expected_sources:
            if source not in snippets_per_source or snippets_per_source[source] == 0:
                data_gaps_confirmed.append(f"{source.replace('_', ' ').title()} data not available")
        
        # Check for company mismatches
        inconsistencies = []
        if expected_companies and expected_companies[0] != '*':
            expected_set = set(c.lower() for c in expected_companies)
            found_set = companies_found
            
            extra_companies = found_set - expected_set
            if extra_companies:
                inconsistencies.append(
                    f"Found unexpected companies: {', '.join(extra_companies)}"
                )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(
            total_snippets=total_snippets,
            expected_sources=len(expected_sources),
            found_sources=len([s for s in snippets_per_source.values() if s > 0]),
            data_gaps=len(data_gaps_confirmed),
            inconsistencies=len(inconsistencies)
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            data_gaps_confirmed=data_gaps_confirmed,
            inconsistencies=inconsistencies,
            total_snippets=total_snippets
        )
        
        report = QualityReport(
            total_snippets=total_snippets,
            snippets_per_source=snippets_per_source,
            companies_found=list(companies_found),
            data_gaps_confirmed=data_gaps_confirmed,
            inconsistencies=inconsistencies,
            confidence_score=confidence_score,
            recommendations=recommendations
        )
        
        print(f"🔍 Data Quality Report:")
        print(f"   Total snippets: {total_snippets}")
        print(f"   Confidence: {confidence_score:.0%}")
        if data_gaps_confirmed:
            print(f"   Gaps: {len(data_gaps_confirmed)} confirmed")
        if inconsistencies:
            print(f"   ⚠️  Issues: {len(inconsistencies)} found")
        
        return report
    
    def _calculate_confidence(
        self,
        total_snippets: int,
        expected_sources: int,
        found_sources: int,
        data_gaps: int,
        inconsistencies: int
    ) -> float:
        """Calculate confidence score (0-1)."""
        
        # Base confidence from snippet count
        if total_snippets == 0:
            return 0.0
        
        confidence = min(total_snippets / 20.0, 1.0)  # 20 snippets = 100%
        
        # Penalize for missing sources
        if expected_sources > 0:
            source_coverage = found_sources / expected_sources
            confidence *= source_coverage
        
        # Penalize for data gaps
        confidence *= (1.0 - min(data_gaps * 0.1, 0.3))
        
        # Penalize for inconsistencies
        confidence *= (1.0 - min(inconsistencies * 0.15, 0.4))
        
        return max(confidence, 0.1)  # Minimum 10% confidence
    
    def _generate_recommendations(
        self,
        data_gaps_confirmed: List[str],
        inconsistencies: List[str],
        total_snippets: int
    ) -> List[str]:
        """Generate recommendations based on quality issues."""
        
        recommendations = []
        
        if total_snippets < 5:
            recommendations.append("Low data volume - response may lack detail")
        
        if data_gaps_confirmed:
            recommendations.append(
                f"Missing data sources: {', '.join(data_gaps_confirmed[:2])}"
            )
            recommendations.append("Synthesis should acknowledge data limitations")
        
        if inconsistencies:
            recommendations.append("Company filtering may need adjustment")
            recommendations.append("Validate synthesis for cross-contamination")
        
        if total_snippets > 50:
            recommendations.append("High data volume - prioritize most relevant snippets")
        
        return recommendations


# Global instance
data_quality_agent = DataQualityAgent()
