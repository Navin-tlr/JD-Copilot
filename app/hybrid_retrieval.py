"""
Hybrid Retrieval System - Combines BM25 (keyword) and dense vector (semantic) search
Implements reciprocal rank fusion for optimal results
"""

import sqlite3
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import re
import json
import hashlib
import os
from datetime import datetime

class HybridRetriever:
    """Hybrid retrieval system combining BM25 and dense vector search"""

    def __init__(self, db_path: str = "data/hybrid_retrieval.db"):
        self.db_path = db_path
        self._init_database()

        # Initialize models
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.vectorizer = None
        self.bm25 = None
        self.documents = []

    def _init_database(self):
        """Initialize database for hybrid retrieval system"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create tables for hybrid retrieval
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hybrid_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_file TEXT NOT NULL,
                    content_hash TEXT UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Index for faster retrieval
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_hash
                ON hybrid_documents(content_hash)
            """)

            conn.commit()

    def add_document(self, content: str, source_file: str, summary: str = None, metadata: Dict = None):
        """Add a document to the hybrid retrieval system"""
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        # Check if document already exists
        if self._document_exists(content_hash):
            return False

        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO hybrid_documents (source_file, content_hash, content, summary, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                source_file,
                content_hash,
                content,
                summary,
                json.dumps(metadata or {})
            ))
            conn.commit()

        # Add to in-memory index
        self.documents.append({
            'content': content,
            'summary': summary or content,
            'source_file': source_file,
            'metadata': metadata or {}
        })

        # Rebuild indexes
        self._rebuild_indexes()

        return True

    def _document_exists(self, content_hash: str) -> bool:
        """Check if document already exists"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM hybrid_documents WHERE content_hash = ?", (content_hash,))
            return cursor.fetchone() is not None

    def _rebuild_indexes(self):
        """Rebuild BM25 and TF-IDF indexes"""
        if not self.documents:
            return

        # Prepare documents for BM25
        corpus = []
        for doc in self.documents:
            # Use summary if available, otherwise content
            text = doc.get('summary') or doc.get('content', '')
            # Tokenize (simple whitespace split for BM25)
            tokens = re.findall(r'\b\w+\b', text.lower())
            corpus.append(tokens)

        # Build BM25 index
        self.bm25 = BM25Okapi(corpus)

        # Build TF-IDF vectorizer
        summaries = [doc.get('summary') or doc.get('content', '') for doc in self.documents]
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        self.vectorizer.fit(summaries)

    def hybrid_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Combine BM25 and semantic search with reciprocal rank fusion"""
        if not self.documents or not self.bm25 or not self.vectorizer:
            return []

        # BM25 search
        bm25_scores = self._bm25_search(query, limit * 2)

        # Semantic search
        semantic_scores = self._semantic_search(query, limit * 2)

        # Combine using Reciprocal Rank Fusion
        combined_results = self._reciprocal_rank_fusion(bm25_scores, semantic_scores, limit)

        return combined_results

    def _bm25_search(self, query: str, limit: int) -> List[Tuple[int, float]]:
        """Perform BM25 search"""
        query_tokens = re.findall(r'\b\w+\b', query.lower())
        doc_scores = self.bm25.get_scores(query_tokens)

        # Get top results with scores
        top_indices = np.argsort(doc_scores)[::-1][:limit]
        return [(int(idx), float(doc_scores[idx])) for idx in top_indices if doc_scores[idx] > 0]

    def _semantic_search(self, query: str, limit: int) -> List[Tuple[int, float]]:
        """Perform semantic search using dense vectors"""
        # Encode query
        query_embedding = self.encoder.encode([query])[0]

        # Get document embeddings
        summaries = [doc.get('summary') or doc.get('content', '') for doc in self.documents]
        doc_embeddings = self.encoder.encode(summaries)

        # Calculate cosine similarities
        similarities = np.dot(doc_embeddings, query_embedding) / (
            np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Get top results
        top_indices = np.argsort(similarities)[::-1][:limit]
        return [(int(idx), float(similarities[idx])) for idx in top_indices if similarities[idx] > 0]

    def _reciprocal_rank_fusion(self, bm25_results: List[Tuple[int, float]],
                               semantic_results: List[Tuple[int, float]],
                               limit: int) -> List[Dict[str, Any]]:
        """Combine BM25 and semantic results using Reciprocal Rank Fusion"""
        # RRF parameters
        k = 60  # Constant for RRF

        # Collect all unique document indices
        all_indices = set()
        for idx, _ in bm25_results + semantic_results:
            all_indices.add(idx)

        # Calculate RRF scores
        rrf_scores = {}
        for idx in all_indices:
            score = 0

            # BM25 contribution
            bm25_rank = None
            for rank, (doc_idx, _) in enumerate(bm25_results, 1):
                if doc_idx == idx:
                    bm25_rank = rank
                    break
            if bm25_rank:
                score += 1 / (k + bm25_rank)

            # Semantic contribution
            semantic_rank = None
            for rank, (doc_idx, _) in enumerate(semantic_results, 1):
                if doc_idx == idx:
                    semantic_rank = rank
                    break
            if semantic_rank:
                score += 1 / (k + semantic_rank)

            rrf_scores[idx] = score

        # Sort by RRF score
        sorted_indices = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:limit]

        # Format results
        results = []
        for idx, score in sorted_indices:
            doc = self.documents[idx]
            results.append({
                'content': doc['content'],
                'summary': doc.get('summary'),
                'source_file': doc['source_file'],
                'metadata': doc.get('metadata', {}),
                'score': score,
                'rank': len(results) + 1
            })

        return results

    def load_documents_from_db(self):
        """Load documents from database into memory"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT source_file, content, summary, metadata
                FROM hybrid_documents
                ORDER BY created_at
            """)

            self.documents = []
            for row in cursor.fetchall():
                self.documents.append({
                    'source_file': row[0],
                    'content': row[1],
                    'summary': row[2],
                    'metadata': json.loads(row[3] or '{}')
                })

        # Rebuild indexes
        self._rebuild_indexes()

    def get_document_count(self) -> int:
        """Get total number of documents"""
        return len(self.documents)

    def clear_documents(self):
        """Clear all documents from memory and database"""
        self.documents = []
        self.bm25 = None
        self.vectorizer = None

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hybrid_documents")
            conn.commit()