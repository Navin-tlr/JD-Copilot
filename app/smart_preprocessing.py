"""
Smart Preprocessing Module - Generate summaries and extract key insights during PDF ingestion
Implements batch processing, intelligent content analysis, and duplicate detection for 1000+ PDF corpus
"""

import json
import logging
import requests
import hashlib
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import re

@dataclass
class DocumentSummary:
    """Structured summary of a PDF document"""
    source_file: str
    file_hash: str
    company_name: str
    summary: str
    key_skills: List[str]
    specializations: List[str]
    salary_info: Dict[str, Any]
    role_count: int
    batch_year: str
    content_type: str  # "job_description", "company_profile", "mixed"
    quality_score: float  # 0-1 content quality assessment

@dataclass
class BatchProcessingResult:
    """Result of batch processing operation"""
    processed_files: int
    skipped_duplicates: int
    failed_files: int
    total_summaries: int
    processing_time: float
    errors: List[str]

class SmartPreprocessor:
    """Smart preprocessing with summarization and duplicate detection"""

    def __init__(self, db_path: str = "data/smart_preprocessing.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database with advanced duplicate detection"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Document summaries with comprehensive duplicate tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_file TEXT NOT NULL,
                    file_hash TEXT UNIQUE NOT NULL, -- Prevents hash duplicates
                    company_name TEXT,
                    summary TEXT,
                    key_skills TEXT, -- JSON array
                    specializations TEXT, -- JSON array
                    salary_info TEXT, -- JSON object
                    role_count INTEGER,
                    batch_year TEXT,
                    content_type TEXT,
                    quality_score REAL,
                    embedding BLOB, -- For semantic similarity
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Duplicate tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS duplicate_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_hash TEXT UNIQUE NOT NULL,
                    semantic_hash TEXT, -- For near-duplicate detection
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    def process_text(self, text: str, file_path: str) -> Optional[DocumentSummary]:
        """Process text and generate summary with duplicate detection"""
        try:
            # Generate file hash
            file_hash = self._generate_file_hash(text)

            # Check for duplicates
            if self._is_duplicate(file_hash, text):
                print(f"⚠️ Skipping duplicate document: {file_path}")
                return None

            # Generate summary using LLM
            summary_data = self._generate_summary(text)

            # Create summary object
            summary = DocumentSummary(
                source_file=file_path,
                file_hash=file_hash,
                company_name=summary_data.get('company_name', ''),
                summary=summary_data.get('summary', ''),
                key_skills=summary_data.get('key_skills', []),
                specializations=summary_data.get('specializations', []),
                salary_info=summary_data.get('salary_info', {}),
                role_count=summary_data.get('role_count', 0),
                batch_year=summary_data.get('batch_year', str(datetime.now().year)),
                content_type=summary_data.get('content_type', 'job_description'),
                quality_score=summary_data.get('quality_score', 0.8)
            )

            # Store in database
            self._store_summary(summary)

            return summary

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return None

    def _generate_file_hash(self, text: str) -> str:
        """Generate SHA256 hash of text content"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _is_duplicate(self, file_hash: str, text: str) -> bool:
        """Check for duplicates using hash and semantic similarity"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check exact hash match
            cursor.execute("SELECT id FROM duplicate_tracking WHERE file_hash = ?", (file_hash,))
            if cursor.fetchone():
                return True

            # TODO: Add semantic similarity check using embeddings
            # For now, just check hash
            return False

    def _generate_summary(self, text: str) -> Dict[str, Any]:
        """Generate structured summary using LLM"""
        try:
            from app.openrouter_wrapper import OpenRouterWrapper

            wrapper = OpenRouterWrapper()

            prompt = f"""
            Analyze this job description text and extract key information in JSON format:

            TEXT: {text[:4000]}... (truncated for brevity)

            Return a JSON object with these fields:
            {{
                "company_name": "extracted company name",
                "summary": "2-3 sentence summary of the role/company",
                "key_skills": ["skill1", "skill2", "skill3"],
                "specializations": ["marketing", "finance", "hr", "operations", "sales", "consulting"],
                "salary_info": {{"min": 500000, "max": 1000000, "currency": "INR"}},
                "role_count": number of roles mentioned,
                "batch_year": "2024",
                "content_type": "job_description",
                "quality_score": 0.0-1.0
            }}

            Focus on marketing roles and skills. Be precise and factual.
            """

            messages = [
                {"role": "system", "content": "You are a precise job description analyzer. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ]

            response = wrapper.get_completion(messages)

            if response.choices:
                content = response.choices[0].message.content.strip()
                # Clean up response (remove markdown code blocks if present)
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()

                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    print(f"❌ Failed to parse LLM response as JSON: {content[:200]}...")
                    return self._fallback_summary(text)

            return self._fallback_summary(text)

        except Exception as e:
            print(f"❌ LLM summary generation failed: {e}")
            return self._fallback_summary(text)

    def _fallback_summary(self, text: str) -> Dict[str, Any]:
        """Fallback summary generation using regex patterns"""
        # Extract company name
        company_patterns = [
            r'(?:company|organization|employer)[\s:]+([A-Za-z0-9&\-\. ]{2,50})',
            r'^([A-Z][A-Za-z0-9&\-\. ]{2,50})(?:\s|$)',
        ]

        company_name = "Unknown"
        for pattern in company_patterns:
            match = re.search(pattern, text[:1000], re.MULTILINE | re.IGNORECASE)
            if match:
                company_name = match.group(1).strip()
                break

        # Extract skills (simple keyword matching)
        skill_keywords = ['marketing', 'digital marketing', 'content creation', 'social media',
                         'SEO', 'analytics', 'campaign management', 'brand management']

        found_skills = [skill for skill in skill_keywords if skill.lower() in text.lower()]

        return {
            "company_name": company_name,
            "summary": f"Job description from {company_name} with focus on marketing roles",
            "key_skills": found_skills[:5],  # Limit to 5 skills
            "specializations": ["marketing"],
            "salary_info": {},
            "role_count": 1,
            "batch_year": str(datetime.now().year),
            "content_type": "job_description",
            "quality_score": 0.5  # Lower quality for fallback
        }

    def _store_summary(self, summary: DocumentSummary):
        """Store summary in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO document_summaries
                (source_file, file_hash, company_name, summary, key_skills, specializations,
                 salary_info, role_count, batch_year, content_type, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                summary.source_file,
                summary.file_hash,
                summary.company_name,
                summary.summary,
                json.dumps(summary.key_skills),
                json.dumps(summary.specializations),
                json.dumps(summary.salary_info),
                summary.role_count,
                summary.batch_year,
                summary.content_type,
                summary.quality_score
            ))

            # Update duplicate tracking
            cursor.execute("""
                INSERT OR IGNORE INTO duplicate_tracking (file_hash)
                VALUES (?)
            """, (summary.file_hash,))

            conn.commit()

    def get_summary_by_hash(self, file_hash: str) -> Optional[DocumentSummary]:
        """Retrieve summary by file hash"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT source_file, file_hash, company_name, summary, key_skills,
                       specializations, salary_info, role_count, batch_year,
                       content_type, quality_score
                FROM document_summaries WHERE file_hash = ?
            """, (file_hash,))

            row = cursor.fetchone()
            if row:
                return DocumentSummary(
                    source_file=row[0],
                    file_hash=row[1],
                    company_name=row[2] or "",
                    summary=row[3] or "",
                    key_skills=json.loads(row[4] or "[]"),
                    specializations=json.loads(row[5] or "[]"),
                    salary_info=json.loads(row[6] or "{}"),
                    role_count=row[7] or 0,
                    batch_year=row[8] or str(datetime.now().year),
                    content_type=row[9] or "job_description",
                    quality_score=row[10] or 0.0
                )
        return None

    def batch_process_summaries(self, summaries: List[DocumentSummary]) -> BatchProcessingResult:
        """Process multiple summaries in batch"""
        start_time = datetime.now()
        processed = 0
        skipped = 0
        failed = 0
        errors = []

        for summary in summaries:
            try:
                if self._is_duplicate(summary.file_hash, ""):
                    skipped += 1
                    continue

                self._store_summary(summary)
                processed += 1

            except Exception as e:
                failed += 1
                errors.append(f"Failed to process {summary.source_file}: {str(e)}")

        processing_time = (datetime.now() - start_time).total_seconds()

        return BatchProcessingResult(
            processed_files=processed,
            skipped_duplicates=skipped,
            failed_files=failed,
            total_summaries=len(summaries),
            processing_time=processing_time,
            errors=errors
        )