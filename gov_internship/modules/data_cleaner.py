import pandas as pd
import os
import re
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
SOURCES_CSV = os.path.join(DATA_DIR, 'india_gov_internship_sources.csv')
FINAL_CSV = os.path.join(DATA_DIR, 'final_government_internships.csv')

GOV_KEYWORDS = [
    'government', 'govt', 'ministry', 'isro', 'drdo', 'niti', 'aayog', 'mea', 'meity',
    'dpiit', 'nicsi', 'nic', 'iit', 'nit', 'iisc', 'iiser', 'aiims', 'municipal',
    'corporation', 'vadodara smart', 'smart city', 'aicte', 'ugc', 'csir', 'barc',
    'dae', 'hal', 'bhel', 'sail', 'ntpc', 'ongc', 'indian oil', 'nhpc', 'national',
    'central', 'state', 'public sector', 'psu', 'district', 'collector', 'panchayat',
    'urban development', 'rural development', 'forest', 'police', 'army', 'navy',
    'air force', 'railways', 'rbi', 'sebi', 'nabard', 'sidbi', 'exim bank',
    'pm internship', 'pmip', 'mca.gov', 'gov.in', 'nic.in', 'india.gov',
    'sure trust', 'beeskilled', 'ymca', 'kvic', 'khadi', 'weavespin'
]

QUALIFICATION_MAP = {
    'btech': 'B.Tech/B.E.',
    'b.tech': 'B.Tech/B.E.',
    'be ': 'B.Tech/B.E.',
    'mtech': 'M.Tech/M.E.',
    'm.tech': 'M.Tech/M.E.',
    'mba': 'MBA',
    'bsc': 'B.Sc.',
    'b.sc': 'B.Sc.',
    'msc': 'M.Sc.',
    'm.sc': 'M.Sc.',
    'phd': 'PhD',
    'llb': 'LLB',
    'bca': 'BCA',
    'mca': 'MCA',
    'diploma': 'Diploma',
    'engineering': 'Engineering',
    'graduate': 'Any Graduate',
    'postgraduate': 'Any Postgraduate',
    'undergraduate': 'Any Undergraduate',
}

def load_gov_sources():
    try:
        df = pd.read_csv(SOURCES_CSV)
        orgs = set()
        for col in ['Organization', 'organization', 'org']:
            if col in df.columns:
                orgs.update(df[col].dropna().str.lower().tolist())
        return orgs
    except Exception:
        return set()

def is_government_org(org_name, gov_orgs):
    if not org_name:
        return False
    org_lower = str(org_name).lower()
    for kw in GOV_KEYWORDS:
        if kw in org_lower:
            return True
    for org in gov_orgs:
        if org and (org in org_lower or org_lower in org):
            return True
    return False

def parse_deadline(deadline_str):
    if not deadline_str or str(deadline_str).strip() in ['', 'nan', 'N/A']:
        return '', 'Open'
    deadline_str = str(deadline_str).strip()
    formats = ['%d-%b-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%b %d, %Y', '%d %b %Y']
    for fmt in formats:
        try:
            dt = datetime.strptime(deadline_str, fmt)
            today = datetime.now()
            if dt < today:
                return deadline_str, 'Expired'
            elif dt <= today + timedelta(days=7):
                return deadline_str, 'Closing Soon'
            else:
                return deadline_str, 'Open'
        except ValueError:
            continue
    return deadline_str, 'Open'

def normalize_skills(skills_str):
    if not skills_str or str(skills_str).strip() in ['', 'nan']:
        return ''
    skills = str(skills_str)
    skills = re.sub(r'["\'\[\]{}]', '', skills)
    parts = re.split(r'[,;|/\n]+', skills)
    cleaned = [s.strip() for s in parts if s.strip() and len(s.strip()) > 1]
    return ', '.join(cleaned[:15])

def normalize_location(loc_str):
    if not loc_str or str(loc_str).strip() in ['', 'nan']:
        return 'Pan India'
    loc = str(loc_str).strip()
    if 'pan india' in loc.lower() or 'virtual' in loc.lower() or 'remote' in loc.lower() or 'wfh' in loc.lower():
        return 'Pan India'
    loc = re.sub(r'\s+', ' ', loc).strip().strip(',')
    return loc[:100]

def normalize_qualification(qual_str):
    if not qual_str or str(qual_str).strip() in ['', 'nan']:
        return 'Any Graduate'
    qual = str(qual_str).lower()
    for key, val in QUALIFICATION_MAP.items():
        if key in qual:
            return val
    return str(qual_str).strip()[:100]

def process_aicte_csv(filepath):
    try:
        df = pd.read_csv(filepath, on_bad_lines='skip')
    except Exception:
        return pd.DataFrame()

    records = []
    col_map = {c.lower().strip(): c for c in df.columns}

    title_col = next((col_map[k] for k in col_map if 'job-title' in k or 'title' in k), None)
    org_col = next((col_map[k] for k in col_map if 'company' in k or 'organization' in k), None)
    loc_col = next((col_map[k] for k in col_map if 'location' in k), None)
    deadline_col = next((col_map[k] for k in col_map if 'apply-by' in k or 'deadline' in k), None)
    url_col = next((col_map[k] for k in col_map if 'btn href' in k or 'url' in k or 'href' in k), None)
    duration_col = next((col_map[k] for k in col_map if 'duration' in k), None)
    stipend_col = next((col_map[k] for k in col_map if 'stipend' in k), None)
    skill_col = next((col_map[k] for k in col_map if 'skill' in k), None)

    for _, row in df.iterrows():
        title = str(row.get(title_col, '') if title_col else '').strip()
        if not title or title == 'nan' or len(title) < 3:
            continue
        org = str(row.get(org_col, '') if org_col else '').strip()
        loc = normalize_location(row.get(loc_col, '') if loc_col else '')
        deadline_raw = str(row.get(deadline_col, '') if deadline_col else '').strip()
        deadline, status = parse_deadline(deadline_raw)
        url = str(row.get(url_col, '') if url_col else '').strip()
        duration = str(row.get(duration_col, '') if duration_col else '').strip()
        stipend = str(row.get(stipend_col, '') if stipend_col else '').strip()
        skills = normalize_skills(row.get(skill_col, '') if skill_col else '')

        if not skills:
            title_lower = title.lower()
            inferred = []
            if 'python' in title_lower: inferred.append('Python')
            if 'data' in title_lower: inferred.extend(['Data Analysis', 'Excel'])
            if 'web' in title_lower or 'mern' in title_lower: inferred.extend(['HTML', 'CSS', 'JavaScript'])
            if 'java' in title_lower: inferred.append('Java')
            if 'ai' in title_lower or 'machine learning' in title_lower or 'ml' in title_lower: inferred.extend(['Python', 'Machine Learning'])
            if 'cloud' in title_lower or 'devops' in title_lower or 'aws' in title_lower: inferred.extend(['Cloud Computing', 'Linux'])
            if 'cyber' in title_lower or 'security' in title_lower: inferred.extend(['Network Security', 'Linux'])
            if 'content' in title_lower or 'writing' in title_lower: inferred.extend(['Content Writing', 'English'])
            skills = ', '.join(inferred) if inferred else 'Communication, MS Office'

        records.append({
            'internship_title': title,
            'organization': org if org != 'nan' else 'AICTE Listed',
            'skills_required': skills,
            'min_gpa': 0.0,
            'qualification': 'Any Graduate',
            'location': loc,
            'deadline': deadline,
            'application_link': url if url != 'nan' else '',
            'internship_url': url if url != 'nan' else '',
            'source': 'AICTE Internship Portal',
            'description': f"{title} internship at {org}. Duration: {duration}. Stipend: {stipend}.",
            'stipend': stipend if stipend != 'nan' else 'Unpaid',
            'duration': duration if duration != 'nan' else '',
            'status': status,
        })
    return pd.DataFrame(records)

def process_gov_sources_csv(filepath):
    try:
        df = pd.read_csv(filepath, on_bad_lines='skip')
    except Exception:
        return pd.DataFrame()

    records = []
    for _, row in df.iterrows():
        org = str(row.get('Organization', row.get('organization', ''))).strip()
        program = str(row.get('Program / Scheme Name', row.get('program', ''))).strip()
        title = program if program and program != 'nan' else f"{org} Internship"
        skills = normalize_skills(row.get('Skills Required', row.get('skills_required', '')))
        location_raw = str(row.get('Mode', row.get('location', ''))).strip()
        if 'offline' in location_raw.lower():
            unit = str(row.get('Unit / Centre / Division', '')).strip()
            location = unit if unit and unit != 'nan' else 'New Delhi'
        else:
            location = normalize_location(location_raw)
        disciplines = str(row.get('Disciplines Eligible', '')).strip()
        qual = normalize_qualification(disciplines)
        deadline_raw = str(row.get('Status (Jun 2026)', row.get('deadline', ''))).strip()
        if 'open' in deadline_raw.lower():
            deadline, status = '', 'Open'
        elif 'check' in deadline_raw.lower():
            deadline, status = '', 'Open'
        else:
            deadline, status = parse_deadline(deadline_raw)
        url = str(row.get('Direct URL', row.get('Website', ''))).strip()
        stipend = str(row.get('Stipend', 'Unpaid')).strip()
        duration = str(row.get('Duration', '')).strip()
        notes = str(row.get('Notes', '')).strip()

        if not org or org == 'nan':
            continue

        records.append({
            'internship_title': title,
            'organization': org,
            'skills_required': skills,
            'min_gpa': 0.0,
            'qualification': qual,
            'location': location if location != 'nan' else 'New Delhi',
            'deadline': deadline,
            'application_link': url if url != 'nan' else '',
            'internship_url': url if url != 'nan' else '',
            'source': str(row.get('Category', 'Direct Government')).strip(),
            'description': f"{title} at {org}. {notes}",
            'stipend': stipend if stipend != 'nan' else 'Unpaid',
            'duration': duration if duration != 'nan' else '1-3 months',
            'status': status,
        })
    return pd.DataFrame(records)

def build_final_dataset(uploaded_files=None):
    gov_orgs = load_gov_sources()
    all_frames = []

    gov_sources_path = os.path.join(DATA_DIR, 'india_gov_internship_sources.csv')
    if os.path.exists(gov_sources_path):
        df_gov = process_gov_sources_csv(gov_sources_path)
        if not df_gov.empty:
            all_frames.append(df_gov)

    aicte_path = os.path.join(DATA_DIR, 'aicte_internships.csv')
    if os.path.exists(aicte_path):
        df_aicte = process_aicte_csv(aicte_path)
        if not df_aicte.empty:
            gov_df = df_aicte[df_aicte['organization'].apply(lambda x: is_government_org(x, gov_orgs))]
            if gov_df.empty:
                gov_df = df_aicte.head(50)
            all_frames.append(gov_df)

    if uploaded_files:
        for f in uploaded_files:
            try:
                df_up = pd.read_csv(f, on_bad_lines='skip')
                if 'job-title' in ' '.join(df_up.columns).lower() or 'internship-primary-info' in ' '.join(df_up.columns).lower():
                    processed = process_aicte_csv(f)
                else:
                    processed = process_gov_sources_csv(f)
                if not processed.empty:
                    all_frames.append(processed)
            except Exception:
                continue

    if not all_frames:
        return pd.DataFrame()

    final_df = pd.concat(all_frames, ignore_index=True)

    required_cols = ['internship_title', 'organization', 'skills_required', 'min_gpa',
                     'qualification', 'location', 'deadline', 'application_link',
                     'internship_url', 'source', 'description']
    for col in required_cols:
        if col not in final_df.columns:
            final_df[col] = ''

    final_df = final_df.drop_duplicates(subset=['internship_title', 'organization'], keep='first')
    final_df = final_df[final_df['internship_title'].str.len() > 2]
    final_df = final_df.reset_index(drop=True)

    os.makedirs(DATA_DIR, exist_ok=True)
    final_df.to_csv(FINAL_CSV, index=False)
    return final_df
