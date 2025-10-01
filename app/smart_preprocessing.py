"""
Smart Preprocessing Module for PDF Summaries

Generates structured summaries using LLM during ingestion, with duplicate detection,
SQLite storage, and risk mitigations.
"""

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from app.config import get_settings
from app.openrouter_wrapper import OpenRouterWrapper
from app.role_category_lexicon import extract_candidate_categories
from app.rag import EmbeddingBackend


@dataclass
class DocumentSummary:
    """Structured summary of a document."""
    key_skills: List[str]
    specializations: List[str]
    companies: List[str]
    salary_info: Dict[str, Any]
    quality_score: float


class SmartPreprocessor:
    """Smart preprocessor for generating and managing document summaries."""

    def __init__(self, db_path: str = "data/smart_preprocessing.db"):
        self.db_path = db_path
        self._init_database()
        self.llm_wrapper = OpenRouterWrapper()
        self.embedder = EmbeddingBackend(get_settings().EMBED_MODEL)
        self.settings = get_settings()

    def _init_database(self):
        """Initialize database tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Document summaries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_hash TEXT UNIQUE NOT NULL,
                    file_path TEXT,
                    summary_json TEXT NOT NULL,
                    embedding BLOB,  -- Serialized numpy array
                    quality_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_hash ON document_summaries(file_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_score ON document_summaries(quality_score)")

            conn.commit()

    def _compute_hash(self, text: str) -> str:
        """Compute SHA256 hash of text for duplicate detection."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _generate_summary_prompt(self, text: str, candidate_categories: set) -> str:
        """Create grounded prompt for summary generation."""
        categories_str = ", ".join(sorted(candidate_categories)) if candidate_categories else "General"

        return f"""You are an expert at extracting structured information from job descriptions.

TASK: Analyze the following job description text and extract ONLY the information that is explicitly mentioned. Do NOT hallucinate, infer, or add information that isn't directly stated in the text.

REQUIRED OUTPUT FORMAT: Return ONLY a valid JSON object with this exact structure:
{{
    "key_skills": ["skill1", "skill2", ...],
    "specializations": ["specialization1", "specialization2", ...],
    "companies": ["company1", "company2", ...],
    "salary_info": {{
        "min_lpa": number or null,
        "max_lpa": number or null,
        "currency": "INR" or "USD" or null,
        "additional_info": "string or null"
    }},
    "quality_score": 0.0 to 1.0
}}

EXTRACTION RULES:
1. key_skills: Only extract skills explicitly mentioned as requirements or desired. Use exact terms from text.
2. specializations: Map to MBA specializations based on content. Valid options: Marketing, Finance, HR, Operations, Analytics, Strategy, IT. Only include if clearly indicated.
3. companies: Only companies explicitly mentioned as employers or offering the role. Do NOT include client companies or partners.
4. salary_info: Extract exact salary figures mentioned. Use null if not specified.
5. quality_score: Rate how complete and clear the JD is (0.0 = poor, 1.0 = excellent).

CANDIDATE CATEGORIES FROM TEXT: {categories_str}

JOB DESCRIPTION TEXT:
{text}

OUTPUT ONLY THE JSON OBJECT:"""

    def _parse_summary_response(self, response: str) -> Optional[DocumentSummary]:
        """Parse LLM response into DocumentSummary."""
        try:
            # Extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start == -1 or end == 0:
                return None

            json_str = response[start:end]
            data = json.loads(json_str)

            return DocumentSummary(
                key_skills=data.get('key_skills', []),
                specializations=data.get('specializations', []),
                companies=data.get('companies', []),
                salary_info=data.get('salary_info', {}),
                quality_score=data.get('quality_score', 0.5)
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def _validate_summary(self, summary: DocumentSummary, candidate_categories: set) -> DocumentSummary:
        """Validate and clean summary against lexicons."""
        # Validate specializations against known categories
        valid_specs = {"Marketing", "Finance", "HR", "Operations", "Analytics", "Strategy", "IT"}
        summary.specializations = [s for s in summary.specializations if s in valid_specs]

        # Validate skills against candidate categories (basic check)
        # Could be enhanced with more sophisticated validation

        return summary

    def _compute_embedding(self, summary: DocumentSummary) -> bytes:
        """Compute embedding for semantic similarity."""
        # Create a text representation of the summary
        summary_text = f"Skills: {' '.join(summary.key_skills)} Specializations: {' '.join(summary.specializations)} Companies: {' '.join(summary.companies)}"
        embedding = self.embedder.embed([summary_text])[0]
        return embedding.tobytes()

    def _check_semantic_similarity(self, embedding: bytes, threshold: float = 0.85) -> bool:
        """Check if embedding is too similar to existing summaries."""
        import numpy as np

        new_emb = np.frombuffer(embedding, dtype=np.float32)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT embedding FROM document_summaries WHERE embedding IS NOT NULL")
            rows = cursor.fetchall()

            for row in rows:
                if row[0]:
                    existing_emb = np.frombuffer(row[0], dtype=np.float32)
                    similarity = np.dot(new_emb, existing_emb) / (np.linalg.norm(new_emb) * np.linalg.norm(existing_emb))
                    if similarity > threshold:
                        return True  # Too similar, consider duplicate

        return False

    def generate_summary(self, text: str) -> Optional[DocumentSummary]:
        """Generate structured summary using LLM."""
        # Extract candidate categories for grounding
        candidate_categories = extract_candidate_categories(text)

        # Create prompt
        prompt = self._generate_summary_prompt(text, candidate_categories)

        try:
            # Call LLM
            messages = [
                {"role": "system", "content": "You are a precise information extraction assistant. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ]

            response = self.llm_wrapper.get_completion(messages, model=self.settings.OPENROUTER_UNSTRUCTURED_MODEL)
            if not response or not response.choices:
                return None

            content = response.choices[0].message.content.strip()

            # Parse response
            summary = self._parse_summary_response(content)
            if not summary:
                return None

            # Validate
            summary = self._validate_summary(summary, candidate_categories)

            return summary

        except Exception as e:
            print(f"Error generating summary: {e}")
            return None

    def store_summary(self, file_hash: str, file_path: str, summary: DocumentSummary) -> bool:
        """Store summary in database."""
        try:
            embedding = self._compute_embedding(summary)

            # Check semantic similarity
            if self._check_semantic_similarity(embedding):
                print(f"⚠️ Near-duplicate detected for {file_path}, skipping storage")
                return False

            summary_json = json.dumps({
                "key_skills": summary.key_skills,
                "specializations": summary.specializations,
                "companies": summary.companies,
                "salary_info": summary.salary_info,
                "quality_score": summary.quality_score
            })

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO document_summaries
                    (file_hash, file_path, summary_json, embedding, quality_score)
                    VALUES (?, ?, ?, ?, ?)
                """, (file_hash, file_path, summary_json, embedding, summary.quality_score))
                conn.commit()

            return True

        except Exception as e:
            print(f"Error storing summary: {e}")
            return False

    def process_text(self, text: str, file_path: str) -> Optional[DocumentSummary]:
        """Main processing method: check duplicate, generate summary, store."""
        # Check exact duplicate
        file_hash = self._compute_hash(text)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM document_summaries WHERE file_hash = ?", (file_hash,))
            if cursor.fetchone():
                print(f"✅ Exact duplicate found for {file_path}, skipping")
                return None

        # Generate summary
        summary = self.generate_summary(text)
        if not summary:
            print(f"❌ Failed to generate summary for {file_path}")
            return None

        # Store summary
        if self.store_summary(file_hash, file_path, summary):
            print(f"💾 Stored summary for {file_path}")
            return summary
        else:
            return None

    def get_summary(self, file_hash: str) -> Optional[DocumentSummary]:
        """Retrieve summary by hash."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT summary_json FROM document_summaries WHERE file_hash = ?", (file_hash,))
                row = cursor.fetchone()
                if row:
                    data = json.loads(row[0])
                    return DocumentSummary(**data)
        except Exception as e:
            print(f"Error retrieving summary: {e}")
        return None

    def batch_process(self, texts_and_paths: List[Tuple[str, str]]) -> List[Tuple[str, Optional[DocumentSummary]]]:
        """Process multiple texts in batch."""
        results = []
        for text, path in texts_and_paths:
            summary = self.process_text(text, path)
            results.append((path, summary))
        return results