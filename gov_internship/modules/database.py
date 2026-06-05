import sqlite3
import os
import pandas as pd
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'internships.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS internships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        internship_title TEXT NOT NULL,
        organization TEXT NOT NULL,
        skills_required TEXT DEFAULT '',
        min_gpa REAL DEFAULT 0.0,
        qualification TEXT DEFAULT '',
        location TEXT DEFAULT '',
        deadline TEXT DEFAULT '',
        application_link TEXT DEFAULT '',
        internship_url TEXT DEFAULT '',
        source TEXT DEFAULT '',
        description TEXT DEFAULT '',
        stipend TEXT DEFAULT '',
        duration TEXT DEFAULT '',
        status TEXT DEFAULT 'Open',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        gpa REAL,
        qualification TEXT,
        skills TEXT,
        location TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        internship_id INTEGER,
        match_score REAL,
        eligibility_score REAL,
        skill_score REAL,
        gpa_score REAL,
        qualification_score REAL,
        location_score REAL,
        missing_skills TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(internship_id) REFERENCES internships(id)
    )''')
    conn.commit()
    conn.close()

def upsert_internships(df):
    conn = get_connection()
    c = conn.cursor()
    inserted = 0
    for _, row in df.iterrows():
        c.execute('''SELECT id FROM internships 
                     WHERE internship_title=? AND organization=?''',
                  (str(row.get('internship_title','')), str(row.get('organization',''))))
        existing = c.fetchone()
        if not existing:
            c.execute('''INSERT INTO internships 
                (internship_title, organization, skills_required, min_gpa, qualification,
                 location, deadline, application_link, internship_url, source, description,
                 stipend, duration, status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                str(row.get('internship_title','')),
                str(row.get('organization','')),
                str(row.get('skills_required','')),
                float(row.get('min_gpa', 0.0) or 0.0),
                str(row.get('qualification','')),
                str(row.get('location','')),
                str(row.get('deadline','')),
                str(row.get('application_link','')),
                str(row.get('internship_url','')),
                str(row.get('source','')),
                str(row.get('description','')),
                str(row.get('stipend','')),
                str(row.get('duration','')),
                str(row.get('status','Open')),
            ))
            inserted += 1
    conn.commit()
    conn.close()
    return inserted

def get_all_internships(status_filter=None, location_filter=None, keyword=None, qualification_filter=None):
    conn = get_connection()
    c = conn.cursor()
    query = 'SELECT * FROM internships WHERE 1=1'
    params = []
    if status_filter and status_filter != 'All':
        query += ' AND status=?'
        params.append(status_filter)
    if location_filter:
        query += ' AND (location LIKE ? OR location LIKE ?)'
        params.extend([f'%{location_filter}%', '%Pan India%'])
    if keyword:
        query += ' AND (internship_title LIKE ? OR organization LIKE ? OR skills_required LIKE ? OR description LIKE ?)'
        params.extend([f'%{keyword}%']*4)
    if qualification_filter:
        query += ' AND qualification LIKE ?'
        params.append(f'%{qualification_filter}%')
    query += ' ORDER BY id DESC'
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_internship_by_id(internship_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM internships WHERE id=?', (internship_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_stats():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) as total FROM internships')
    total = c.fetchone()['total']
    c.execute("SELECT COUNT(*) as open FROM internships WHERE status='Open'")
    open_count = c.fetchone()['open']
    c.execute("SELECT COUNT(*) as closing FROM internships WHERE status='Closing Soon'")
    closing = c.fetchone()['closing']
    c.execute("SELECT COUNT(DISTINCT organization) as orgs FROM internships")
    orgs = c.fetchone()['orgs']
    c.execute("SELECT COUNT(DISTINCT source) as sources FROM internships")
    sources = c.fetchone()['sources']
    conn.close()
    return {
        'total': total,
        'open': open_count,
        'closing_soon': closing,
        'organizations': orgs,
        'sources': sources
    }

def export_to_csv(output_path):
    conn = get_connection()
    df = pd.read_sql_query('SELECT * FROM internships', conn)
    conn.close()
    df.to_csv(output_path, index=False)
    return len(df)
