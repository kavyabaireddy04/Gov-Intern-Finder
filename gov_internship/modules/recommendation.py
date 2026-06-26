import re
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

QUALIFICATION_HIERARCHY = {
    'ssc': 1, '10th': 1, 'matriculation': 1,
    'hsc': 2, '12th': 2, 'higher secondary': 2, 'intermediate': 2,
    'diploma': 3,
    'any undergraduate': 4, 'undergraduate': 4,
    'any graduate': 4, 'graduate': 4,
    'b.tech/b.e.': 5, 'b.tech': 5, 'b.e.': 5, 'be': 5,
    'bca': 5, 'bsc': 5, 'b.sc.': 5, 'ba': 4, 'bcom': 4, 'b.com': 4,
    'llb': 5,
    'any postgraduate': 6, 'postgraduate': 6,
    'm.tech/m.e.': 6, 'm.tech': 6, 'm.e.': 6, 'msc': 6, 'm.sc.': 6,
    'mba': 6, 'mca': 6, 'ma': 6, 'mcom': 6,
    'phd': 7,
    'engineering': 5,
}

def get_qual_level(qual_str):
    if not qual_str:
        return 4
    qual_lower = str(qual_str).lower().strip()
    for key, level in sorted(QUALIFICATION_HIERARCHY.items(), key=lambda x: len(x[0]), reverse=True):
        if key in qual_lower:
            return level
    return 4

def parse_skills(skills_str):
    if not skills_str or str(skills_str).strip() in ['', 'nan']:
        return []
    text = str(skills_str)
    text = re.sub(r'["\'\[\]{}()]', '', text)
    parts = re.split(r'[,;|/\n]+', text)
    return [s.strip().lower() for s in parts if s.strip() and len(s.strip()) > 1]

def skill_match_score(student_skills_str, internship_skills_str):
    student_skills = parse_skills(student_skills_str)
    internship_skills = parse_skills(internship_skills_str)

    if not internship_skills:
        return 85.0, []

    if not student_skills:
        return 0.0, internship_skills

    student_set = set(student_skills)
    missing = []
    matched = 0

    for req_skill in internship_skills:
        found = False
        for s_skill in student_set:
            if req_skill in s_skill or s_skill in req_skill or (len(req_skill) > 4 and req_skill[:4] in s_skill):
                found = True
                matched += 1
                break
        if not found:
            missing.append(req_skill.title())

    direct_ratio = matched / len(internship_skills)

    student_text = ' '.join(student_skills)
    intern_text = ' '.join(internship_skills)
    if student_text and intern_text:
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
            tfidf_matrix = vectorizer.fit_transform([student_text, intern_text])
            cos_sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        except Exception:
            cos_sim = direct_ratio
    else:
        cos_sim = direct_ratio

    final_skill_score = (direct_ratio * 0.6 + cos_sim * 0.4) * 100
    final_skill_score = min(100.0, max(0.0, final_skill_score))
    return round(final_skill_score, 2), missing

def gpa_match_score(student_gpa, min_gpa):
    try:
        student_gpa = float(student_gpa)
        min_gpa = float(min_gpa or 0.0)
    except (ValueError, TypeError):
        return 75.0

    if min_gpa <= 0:
        if student_gpa >= 9.0:
            return 100.0
        elif student_gpa >= 8.0:
            return 95.0
        elif student_gpa >= 7.0:
            return 85.0
        elif student_gpa >= 6.0:
            return 75.0
        else:
            return 60.0

    if student_gpa >= min_gpa:
        excess = student_gpa - min_gpa
        bonus = min(15.0, excess * 10)
        return round(min(100.0, 85.0 + bonus), 2)
    else:
        deficit = min_gpa - student_gpa
        penalty = min(85.0, deficit * 25)
        return round(max(0.0, 85.0 - penalty), 2)

def qualification_match_score(student_qual, internship_qual):
    s_level = get_qual_level(student_qual)
    i_level = get_qual_level(internship_qual)

    if s_level >= i_level:
        overshoot = s_level - i_level
        if overshoot == 0:
            return 100.0
        elif overshoot == 1:
            return 95.0
        else:
            return 88.0
    else:
        gap = i_level - s_level
        if gap == 1:
            return 50.0
        elif gap == 2:
            return 20.0
        else:
            return 0.0

def location_match_score(student_location, internship_location):
    if not student_location or not internship_location:
        return 70.0

    s_loc = str(student_location).lower().strip()
    i_loc = str(internship_location).lower().strip()

    if 'pan india' in i_loc or 'any' in i_loc or 'virtual' in i_loc or 'remote' in i_loc or 'online' in i_loc:
        return 100.0
    if 'pan india' in s_loc or 'any' in s_loc or 'anywhere' in s_loc:
        return 90.0

    s_words = set(re.split(r'[\s,/]+', s_loc))
    i_words = set(re.split(r'[\s,/]+', i_loc))
    common = s_words & i_words
    common = {w for w in common if len(w) > 2}

    if common:
        return 100.0

    state_map = {
        'mumbai': 'maharashtra', 'pune': 'maharashtra', 'nagpur': 'maharashtra',
        'delhi': 'delhi', 'new delhi': 'delhi', 'noida': 'uttar pradesh', 'gurgaon': 'haryana',
        'bangalore': 'karnataka', 'bengaluru': 'karnataka', 'mysore': 'karnataka',
        'chennai': 'tamil nadu', 'coimbatore': 'tamil nadu',
        'hyderabad': 'telangana', 'secunderabad': 'telangana',
        'kolkata': 'west bengal',
        'ahmedabad': 'gujarat', 'surat': 'gujarat', 'vadodara': 'gujarat', 'baroda': 'gujarat',
        'jaipur': 'rajasthan', 'jodhpur': 'rajasthan',
        'lucknow': 'uttar pradesh', 'kanpur': 'uttar pradesh',
        'bhopal': 'madhya pradesh', 'indore': 'madhya pradesh',
        'thiruvananthapuram': 'kerala', 'kochi': 'kerala',
        'guwahati': 'assam',
        'patna': 'bihar',
        'bhubaneswar': 'odisha',
        'raipur': 'chhattisgarh',
        'dehradun': 'uttarakhand',
        'chandigarh': 'chandigarh',
        'srinagar': 'jammu & kashmir',
    }

    s_state = state_map.get(s_loc, s_loc)
    i_state = state_map.get(i_loc, i_loc)
    if s_state == i_state:
        return 75.0

    return 20.0

def calculate_eligibility(student_gpa, student_qual, student_skills, student_location,
                           internship):
    skill_score, missing_skills = skill_match_score(student_skills, internship.get('skills_required', ''))
    gpa_score = gpa_match_score(student_gpa, internship.get('min_gpa', 0))
    qual_score = qualification_match_score(student_qual, internship.get('qualification', ''))
    loc_score = location_match_score(student_location, internship.get('location', ''))

    final_score = (
        0.40 * skill_score +
        0.25 * gpa_score +
        0.20 * qual_score +
        0.15 * loc_score
    )
    final_score = round(final_score, 2)

    eligibility_score = (
        0.35 * gpa_score +
        0.35 * qual_score +
        0.20 * skill_score * 0.5 +
        0.10 * loc_score
    )
    eligibility_score = round(min(100.0, eligibility_score), 2)
    eligible = eligibility_score >= 50.0

    try:
        s_gpa = float(student_gpa)
        min_gpa = float(internship.get('min_gpa', 0) or 0)
        gpa_met = s_gpa >= min_gpa if min_gpa > 0 else True
        gpa_status = 'Met' if gpa_met else f'Not Met (Need {min_gpa}, Have {s_gpa})'
    except Exception:
        gpa_status = 'Met'

    s_level = get_qual_level(student_qual)
    i_level = get_qual_level(internship.get('qualification', ''))
    if s_level >= i_level:
        qual_status = 'Met'
    elif s_level == i_level - 1:
        qual_status = 'Partially Matched'
    else:
        qual_status = 'Not Met'

    i_loc = str(internship.get('location', '')).lower()
    if 'pan india' in i_loc or 'virtual' in i_loc or 'online' in i_loc or 'remote' in i_loc:
        loc_status = 'Yes (Pan India/Remote)'
    elif loc_score >= 75:
        loc_status = 'Yes'
    elif loc_score >= 40:
        loc_status = 'Partial'
    else:
        loc_status = 'No'

    return {
        'match_score': final_score,
        'eligibility_score': eligibility_score,
        'eligible': eligible,
        'skill_score': round(skill_score, 2),
        'gpa_score': round(gpa_score, 2),
        'qual_score': round(qual_score, 2),
        'loc_score': round(loc_score, 2),
        'missing_skills': missing_skills[:5],
        'gpa_status': gpa_status,
        'qual_status': qual_status,
        'loc_status': loc_status,
    }

def get_recommendations(student_gpa, student_qual, student_skills, student_location,
                         internships, top_n=10):
    if not internships:
        return []

    results = []
    for internship in internships:
        if internship.get('status') == 'Expired':
            continue
        analysis = calculate_eligibility(
            student_gpa, student_qual, student_skills, student_location, internship
        )
        results.append({
            **internship,
            **analysis,
        })

    results.sort(key=lambda x: (x['match_score'], x['eligibility_score']), reverse=True)

    seen_scores = {}
    for i, r in enumerate(results):
        key = round(r['match_score'], 1)
        if key in seen_scores:
            noise = (hash(str(r.get('id', i))) % 30 - 15) * 0.1
            r['match_score'] = round(min(100.0, max(0.0, r['match_score'] + noise)), 2)
            r['eligibility_score'] = round(min(100.0, max(0.0, r['eligibility_score'] + noise * 0.5)), 2)
        else:
            seen_scores[key] = i

    results.sort(key=lambda x: x['match_score'], reverse=True)

    for rank, r in enumerate(results[:top_n], 1):
        r['rank'] = rank

    return results[:top_n]
