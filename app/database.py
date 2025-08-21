"""
Database Module - SQLite database for structured placement data
Handles companies, roles, offers, and skills tables
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import logging

class PlacementDatabase:
    """SQLite database for structured placement data"""
    
    def __init__(self, db_path: str = "data/placement_data.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables with MBA specialization support"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Companies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT UNIQUE NOT NULL,
                    company_type TEXT,
                    industry TEXT,
                    location TEXT,
                    batch_year TEXT DEFAULT '2024-2025',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Roles table with specialization
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    specialization TEXT NOT NULL,
                    location TEXT,
                    role_description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
            """)
            
            # Offers table (salary and placement data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_id INTEGER NOT NULL,
                    batch_year TEXT DEFAULT '2024-2025',
                    salary_min_lpa REAL,
                    salary_max_lpa REAL,
                    expected_hires INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (role_id) REFERENCES roles (id)
                )
            """)
            
            # Skills table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_id INTEGER NOT NULL,
                    skill_name TEXT NOT NULL,
                    skill_type TEXT DEFAULT 'technical',
                    skill_priority INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (role_id) REFERENCES roles (id)
                )
            """)
            
            # Requirements table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS requirements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_id INTEGER NOT NULL,
                    requirement_text TEXT NOT NULL,
                    requirement_type TEXT DEFAULT 'education',
                    requirement_priority INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (role_id) REFERENCES roles (id)
                )
            """)
            
            # Specializations table for MBA domains
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS specializations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(company_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_roles_company ON roles(company_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_roles_specialization ON roles(specialization)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_offers_batch_year ON offers(batch_year)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_skills_role ON skills(role_id)")
            
            # Insert default MBA specializations
            cursor.execute("""
                INSERT OR IGNORE INTO specializations (name, description) VALUES 
                ('Marketing', 'Marketing and Brand Management'),
                ('Finance', 'Finance and Investment Banking'),
                ('HR', 'Human Resources and Organizational Behavior'),
                ('Operations', 'Operations and Supply Chain Management'),
                ('Strategy', 'Strategic Management and Consulting'),
                ('IT', 'Information Technology and Digital Transformation'),
                ('Analytics', 'Business Analytics and Data Science')
            """)
            
            conn.commit()
    
    def insert_company_extraction(self, extraction_data: Dict[str, Any]) -> bool:
        """Insert structured extraction data into database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert company
                company_name = extraction_data.get("company_name", "")
                if not company_name:
                    return False
                
                cursor.execute("""
                    INSERT OR REPLACE INTO companies (company_name, company_type, industry, location)
                    VALUES (?, ?, ?, ?)
                """, (
                    company_name,
                    extraction_data.get("company_type"),
                    extraction_data.get("industry"),
                    extraction_data.get("location")
                ))
                
                company_id = cursor.lastrowid
                
                # Insert roles and related data
                roles = extraction_data.get("roles", [])
                for role_data in roles:
                    # Insert role with specialization
                    cursor.execute("""
                        INSERT INTO roles (company_id, title, specialization, location, role_description)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        company_id, 
                        role_data.get("title", ""), 
                        role_data.get("specialization", "General"),
                        role_data.get("location"),
                        role_data.get("role_description", "")
                    ))
                    
                    role_id = cursor.lastrowid
                    
                    # Insert offer data with batch year
                    if role_data.get("salary_min_lpa") or role_data.get("salary_max_lpa"):
                        cursor.execute("""
                            INSERT INTO offers (role_id, batch_year, salary_min_lpa, salary_max_lpa, expected_hires)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            role_id,
                            extraction_data.get("batch_year", "2024-2025"),
                            role_data.get("salary_min_lpa"),
                            role_data.get("salary_max_lpa"),
                            role_data.get("expected_hires")
                        ))
                    
                    # Insert skills with priority
                    skills = role_data.get("skills", [])
                    for i, skill in enumerate(skills):
                        if skill:
                            cursor.execute("""
                                INSERT INTO skills (role_id, skill_name, skill_priority)
                                VALUES (?, ?, ?)
                            """, (role_id, skill, i + 1))
                    
                    # Insert requirements with priority
                    requirements = role_data.get("requirements", [])
                    for i, req in enumerate(requirements):
                        if req:
                            cursor.execute("""
                                INSERT INTO requirements (role_id, requirement_text, requirement_priority)
                                VALUES (?, ?, ?)
                            """, (role_id, req, i + 1))
                
                conn.commit()
                return True
                
        except Exception as e:
            logging.error(f"Failed to insert company extraction: {e}")
            return False
    
    def get_companies(self) -> List[Dict[str, Any]]:
        """Get all companies with basic info"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.company_name, c.company_type, c.industry, c.location, 
                           COUNT(DISTINCT r.id) as role_count
                    FROM companies c
                    LEFT JOIN roles r ON c.id = r.company_id
                    GROUP BY c.id, c.company_name, c.company_type, c.industry, c.location
                    ORDER BY c.company_name
                """)
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logging.error(f"Failed to get companies: {e}")
            return []
    
    def get_company_roles(self, company_name: str) -> List[Dict[str, Any]]:
        """Get all roles for a specific company"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT r.title, r.specialization, r.location, o.salary_min_lpa, o.salary_max_lpa, o.batch_year,
                           GROUP_CONCAT(DISTINCT s.skill_name) as skills,
                           GROUP_CONCAT(DISTINCT req.requirement_text) as requirements
                    FROM companies c
                    JOIN roles r ON c.id = r.company_id
                    LEFT JOIN offers o ON r.id = o.role_id
                    LEFT JOIN skills s ON r.id = s.role_id
                    LEFT JOIN requirements req ON r.id = req.role_id
                    WHERE c.company_name = ?
                    GROUP BY r.id, r.title, r.specialization, r.location, o.salary_min_lpa, o.salary_max_lpa, o.batch_year
                """, (company_name,))
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logging.error(f"Failed to get company roles: {e}")
            return []
    
    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic statistics without requiring offers data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Company count - just count companies with roles
                cursor.execute("""
                    SELECT COUNT(DISTINCT c.company_name) as company_count
                    FROM companies c
                    JOIN roles r ON c.id = r.company_id
                """)
                company_count = cursor.fetchone()[0]
                
                # Role count
                cursor.execute("""
                    SELECT COUNT(DISTINCT r.id) as role_count
                    FROM roles r
                """)
                role_count = cursor.fetchone()[0]
                
                # Top skills
                cursor.execute("""
                    SELECT s.skill_name, COUNT(*) as count
                    FROM skills s
                    JOIN roles r ON s.role_id = r.id
                    GROUP BY s.skill_name
                    ORDER BY count DESC
                    LIMIT 10
                """)
                top_skills = [{"skill": row[0], "count": row[1]} for row in cursor.fetchall()]
                
                return {
                    "company_count": company_count,
                    "role_count": role_count,
                    "top_skills": top_skills,
                    "has_offers": False
                }
                
        except Exception as e:
            logging.error(f"Failed to get basic stats: {e}")
            return {
                "company_count": 0,
                "role_count": 0,
                "top_skills": [],
                "has_offers": False
            }

    def get_placement_stats(self, specialization: Optional[str] = None, batch_year: str = "2024-2025") -> Dict[str, Any]:
        """Get placement statistics with MBA specialization support"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build filters
                filters = []
                params = []
                
                if specialization:
                    filters.append("r.specialization = ?")
                    params.append(specialization)
                
                filters.append("o.batch_year = ?")
                params.append(batch_year)
                
                where_clause = "WHERE " + " AND ".join(filters) if filters else ""
                
                # Company count
                cursor.execute(f"""
                    SELECT COUNT(DISTINCT c.company_name) as company_count
                    FROM companies c
                    JOIN roles r ON c.id = r.company_id
                    LEFT JOIN offers o ON r.id = o.role_id
                    {where_clause}
                """, params)
                company_count = cursor.fetchone()[0]
                
                # Role count
                cursor.execute(f"""
                    SELECT COUNT(DISTINCT r.id) as role_count
                    FROM roles r
                    LEFT JOIN offers o ON r.id = o.role_id
                    {where_clause}
                """, params)
                role_count = cursor.fetchone()[0]
                
                # Salary statistics
                cursor.execute(f"""
                    SELECT 
                        AVG(o.salary_min_lpa) as avg_min_salary,
                        AVG(o.salary_max_lpa) as avg_max_salary,
                        MIN(o.salary_min_lpa) as min_salary,
                        MAX(o.salary_max_lpa) as max_salary,
                        COUNT(DISTINCT o.id) as total_offers
                    FROM offers o
                    JOIN roles r ON o.role_id = r.id
                    {where_clause}
                    AND o.salary_min_lpa IS NOT NULL
                    AND o.salary_max_lpa IS NOT NULL
                """, params)
                salary_stats = cursor.fetchone()
                
                # Top skills by specialization
                cursor.execute(f"""
                    SELECT s.skill_name, COUNT(*) as count
                    FROM skills s
                    JOIN roles r ON s.role_id = r.id
                    JOIN offers o ON r.id = o.role_id
                    {where_clause}
                    GROUP BY s.skill_name
                    ORDER BY count DESC
                    LIMIT 10
                """, params)
                top_skills = [{"skill": row[0], "count": row[1]} for row in cursor.fetchall()]
                
                # Specialization breakdown
                cursor.execute(f"""
                    SELECT r.specialization, COUNT(DISTINCT r.id) as role_count,
                           AVG(o.salary_min_lpa) as avg_min, AVG(o.salary_max_lpa) as avg_max
                    FROM roles r
                    JOIN offers o ON r.id = o.role_id
                    WHERE o.batch_year = ?
                    GROUP BY r.specialization
                    ORDER BY role_count DESC
                """, [batch_year])
                specialization_stats = [{"specialization": row[0], "role_count": row[1], 
                                       "avg_min": row[2], "avg_max": row[3]} for row in cursor.fetchall()]
                
                return {
                    "company_count": company_count,
                    "role_count": role_count,
                    "avg_min_salary": salary_stats[0],
                    "avg_max_salary": salary_stats[1],
                    "min_salary": salary_stats[2],
                    "max_salary": salary_stats[3],
                    "total_offers": salary_stats[4],
                    "top_skills": top_skills,
                    "specialization_breakdown": specialization_stats,
                    "batch_year": batch_year,
                    "specialization_filter": specialization
                }
                
        except Exception as e:
            logging.error(f"Failed to get placement stats: {e}")
            return {}
    
    def search_skills(self, skill_query: str, company_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for roles by skills"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                company_join = ""
                company_where = ""
                if company_filter:
                    company_join = "JOIN companies c ON r.company_id = c.id"
                    company_where = "AND c.company_name = ?"
                
                cursor.execute(f"""
                    SELECT c.company_name, r.title, r.location, o.salary_min_lpa, o.salary_max_lpa
                    FROM skills s
                    JOIN roles r ON s.role_id = r.id
                    JOIN offers o ON r.id = o.role_id
                    {company_join}
                    WHERE s.skill_name LIKE ? {company_where}
                    ORDER BY o.salary_max_lpa DESC
                """, (f"%{skill_query}%", company_filter) if company_filter else (f"%{skill_query}%",))
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logging.error(f"Failed to search skills: {e}")
            return []

    def get_companies_by_specialization(self, specialization: str, batch_year: str = "2024-2025") -> List[Dict[str, Any]]:
        """Get companies offering roles in a specific specialization"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT c.company_name, c.company_type, c.industry, c.location,
                           COUNT(r.id) as role_count,
                           AVG(o.salary_min_lpa) as avg_min_salary,
                           AVG(o.salary_max_lpa) as avg_max_salary
                    FROM companies c
                    JOIN roles r ON c.id = r.company_id
                    JOIN offers o ON r.id = o.role_id
                    WHERE r.specialization = ? AND o.batch_year = ?
                    GROUP BY c.id, c.company_name, c.company_type, c.industry, c.location
                    ORDER BY role_count DESC, avg_max_salary DESC
                """, (specialization, batch_year))
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logging.error(f"Failed to get companies by specialization: {e}")
            return []

    def compare_company_specializations(self, company_name: str, batch_year: str = "2024-2025") -> Dict[str, Any]:
        """Compare different specializations within a company"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT r.specialization, r.title, r.location,
                           o.salary_min_lpa, o.salary_max_lpa, o.expected_hires,
                           GROUP_CONCAT(DISTINCT s.skill_name) as skills,
                           GROUP_CONCAT(DISTINCT req.requirement_text) as requirements
                    FROM companies c
                    JOIN roles r ON c.id = r.company_id
                    JOIN offers o ON r.id = o.role_id
                    LEFT JOIN skills s ON r.id = s.role_id
                    LEFT JOIN requirements req ON r.id = req.role_id
                    WHERE c.company_name = ? AND o.batch_year = ?
                    GROUP BY r.id, r.specialization, r.title, r.location, o.salary_min_lpa, o.salary_max_lpa, o.expected_hires
                    ORDER BY r.specialization, o.salary_max_lpa DESC
                """, (company_name, batch_year))
                
                columns = [desc[0] for desc in cursor.description]
                roles = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Group by specialization
                specialization_data = {}
                for role in roles:
                    spec = role['specialization']
                    if spec not in specialization_data:
                        specialization_data[spec] = []
                    specialization_data[spec].append(role)
                
                return {
                    "company_name": company_name,
                    "batch_year": batch_year,
                    "specializations": specialization_data,
                    "total_roles": len(roles)
                }
                
        except Exception as e:
            logging.error(f"Failed to compare company specializations: {e}")
            return {}

    def get_specialization_insights(self, specialization: str, batch_year: str = "2024-2025") -> Dict[str, Any]:
        """Get comprehensive insights for a specific specialization"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Basic stats
                cursor.execute("""
                    SELECT COUNT(DISTINCT c.company_name) as company_count,
                           COUNT(DISTINCT r.id) as role_count,
                           AVG(o.salary_min_lpa) as avg_min_salary,
                           AVG(o.salary_max_lpa) as avg_max_salary,
                           MIN(o.salary_min_lpa) as min_salary,
                           MAX(o.salary_max_lpa) as max_salary
                    FROM companies c
                    JOIN roles r ON c.id = r.company_id
                    JOIN offers o ON r.id = o.role_id
                    WHERE r.specialization = ? AND o.batch_year = ?
                """, (specialization, batch_year))
                
                stats = cursor.fetchone()
                
                # Top companies by salary
                cursor.execute("""
                    SELECT c.company_name, AVG(o.salary_max_lpa) as avg_salary,
                           COUNT(r.id) as role_count
                    FROM companies c
                    JOIN roles r ON c.id = r.company_id
                    JOIN offers o ON r.id = o.role_id
                    WHERE r.specialization = ? AND o.batch_year = ?
                    GROUP BY c.id, c.company_name
                    ORDER BY avg_salary DESC
                    LIMIT 5
                """, (specialization, batch_year))
                
                top_companies = [{"company": row[0], "avg_salary": row[1], "role_count": row[2]} 
                                for row in cursor.fetchall()]
                
                # Top skills
                cursor.execute("""
                    SELECT s.skill_name, COUNT(*) as count
                    FROM skills s
                    JOIN roles r ON s.role_id = r.id
                    JOIN offers o ON r.id = o.role_id
                    WHERE r.specialization = ? AND o.batch_year = ?
                    GROUP BY s.skill_name
                    ORDER BY count DESC
                    LIMIT 10
                """, (specialization, batch_year))
                
                top_skills = [{"skill": row[0], "count": row[1]} for row in cursor.fetchall()]
                
                return {
                    "specialization": specialization,
                    "batch_year": batch_year,
                    "stats": {
                        "company_count": stats[0],
                        "role_count": stats[1],
                        "avg_min_salary": stats[2],
                        "avg_max_salary": stats[3],
                        "min_salary": stats[4],
                        "max_salary": stats[5]
                    },
                    "top_companies": top_companies,
                    "top_skills": top_skills
                }
                
        except Exception as e:
            logging.error(f"Failed to get specialization insights: {e}")
            return {}

    def get_median_salary_by_specialization(self, specialization: str, batch_year: str = "2024-2025") -> float:
        """Get median salary for a specific specialization"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT o.salary_max_lpa
                    FROM roles r
                    JOIN offers o ON r.id = o.role_id
                    WHERE r.specialization = ? AND o.batch_year = ?
                    AND o.salary_max_lpa IS NOT NULL
                    ORDER BY o.salary_max_lpa
                """, (specialization, batch_year))
                
                salaries = [row[0] for row in cursor.fetchall()]
                if not salaries:
                    return 0.0
                
                # Calculate median
                n = len(salaries)
                if n % 2 == 0:
                    median = (salaries[n//2 - 1] + salaries[n//2]) / 2
                else:
                    median = salaries[n//2]
                
                return median
                
        except Exception as e:
            logging.error(f"Failed to get median salary: {e}")
            return 0.0

    def get_all_roles(self) -> List[Dict[str, Any]]:
        """Get all roles with company information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT r.title, r.specialization, r.location, c.company_name,
                           o.salary_min_lpa, o.salary_max_lpa, o.batch_year
                    FROM roles r
                    JOIN companies c ON r.company_id = c.id
                    LEFT JOIN offers o ON r.id = o.role_id
                    ORDER BY c.company_name, r.title
                """)
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logging.error(f"Failed to get all roles: {e}")
            return []

    def get_all_skills(self) -> List[Dict[str, Any]]:
        """Get all skills with role information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.skill_name, s.skill_type, s.skill_priority, r.title, c.company_name
                    FROM skills s
                    JOIN roles r ON s.role_id = r.id
                    JOIN companies c ON r.company_id = c.id
                    ORDER BY c.company_name, r.title, s.skill_priority
                """)
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logging.error(f"Failed to get all skills: {e}")
            return []

    def get_all_requirements(self) -> List[Dict[str, Any]]:
        """Get all requirements with role information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT req.requirement_text, req.requirement_type, req.requirement_priority, 
                           r.title, c.company_name
                    FROM requirements req
                    JOIN roles r ON req.role_id = r.id
                    JOIN companies c ON r.company_id = c.id
                    ORDER BY c.company_name, r.title, req.requirement_priority
                """)
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logging.error(f"Failed to get all requirements: {e}")
            return []
