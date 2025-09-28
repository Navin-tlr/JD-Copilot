#!/usr/bin/env python3
"""Check if role_types are stored in database"""

import sys
import sqlite3
sys.path.insert(0, '.')

from app.database import PlacementDatabase

db = PlacementDatabase()

# Query roles to see if role_types are stored
with sqlite3.connect(db.db_path) as conn:
    cursor = conn.cursor()
    roles = cursor.execute("""
        SELECT id, title, specialization, role_types 
        FROM roles 
        ORDER BY id DESC 
        LIMIT 10
    """).fetchall()

print("Recent roles in database:")
for role in roles:
    role_id, title, specialization, role_types = role
    print(f"ID: {role_id}")
    print(f"Title: {title}")
    print(f"Specialization: {specialization}")
    print(f"Role Types: {role_types}")
    print("-" * 40)
