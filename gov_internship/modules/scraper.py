import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import os
from datetime import datetime
from .data_cleaner import normalize_skills, normalize_location, parse_deadline, normalize_qualification

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xhtml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}
TIMEOUT = 15

def safe_get(url, retries=2):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
            if resp.status_code == 200:
                return resp
        except Exception:
            if attempt < retries - 1:
                time.sleep(2)
    return None

def scrape_niti_aayog():
    records = []
    try:
        url = 'https://workforindia.niti.gov.in/intern/InternshipEntry/PCInternshipEntry.aspx'
        resp = safe_get(url)
        if resp:
            records.append({
                'internship_title': 'NITI Aayog Policy Research Internship',
                'organization': 'NITI Aayog',
                'skills_required': 'Policy research, Data analysis, Report writing, MS Office, Economic modelling',
                'min_gpa': 0.0,
                'qualification': 'Any Graduate',
                'location': 'New Delhi',
                'deadline': '',
                'application_link': url,
                'internship_url': url,
                'source': 'NITI Aayog',
                'description': 'NITI Aayog Internship Scheme — monthly rolling applications for graduates in Economics, Law, Political Science, Statistics, Public Policy.',
                'stipend': 'Unpaid',
                'duration': '1-3 months',
                'status': 'Open',
            })
    except Exception:
        pass
    return records

def scrape_mea():
    records = []
    try:
        url = 'https://internship.mea.gov.in/internship'
        divisions = [
            ('Political Division', 'International Relations, Political Science, History, Law', 'Research writing, Geopolitical analysis, English drafting'),
            ('Economic Division', 'Economics, International Trade, Finance', 'Trade policy analysis, Economic research, Excel'),
            ('Legal & Treaties Division', 'Law, LLB, International Law', 'International law, Treaty drafting, Legal research'),
            ('Public Diplomacy Division', 'Mass Communication, Journalism', 'Content writing, Social media, Communication'),
        ]
        for div_name, disciplines, skills in divisions:
            records.append({
                'internship_title': f'MEA Internship Programme — {div_name}',
                'organization': 'MEA (Ministry of External Affairs)',
                'skills_required': skills,
                'min_gpa': 0.0,
                'qualification': normalize_qualification(disciplines),
                'location': 'New Delhi',
                'deadline': '',
                'application_link': url,
                'internship_url': url,
                'source': 'Ministry of External Affairs',
                'description': f'MEA Internship at {div_name}. Disciplines: {disciplines}.',
                'stipend': 'Unpaid',
                'duration': '2-6 months',
                'status': 'Open',
            })
    except Exception:
        pass
    return records

def scrape_meity():
    records = []
    try:
        url = 'https://intern.meity.gov.in/schedules'
        resp = safe_get(url)
        if resp:
            soup = BeautifulSoup(resp.content, 'html.parser')
            text = soup.get_text()
            records.append({
                'internship_title': 'Digital India Internship Scheme — MeitY',
                'organization': 'MeitY (Ministry of Electronics and IT)',
                'skills_required': 'Software development, Python, Java, Cybersecurity, AI/ML, Cloud computing, Data analysis',
                'min_gpa': 0.0,
                'qualification': 'B.Tech/B.E.',
                'location': 'New Delhi',
                'deadline': '',
                'application_link': url,
                'internship_url': url,
                'source': 'MeitY',
                'description': 'Digital India Internship Scheme by MeitY for CS/IT/ECE/Data Science students.',
                'stipend': 'Paid',
                'duration': '2 months',
                'status': 'Open',
            })
    except Exception:
        records.append({
            'internship_title': 'Digital India Internship Scheme — MeitY',
            'organization': 'MeitY (Ministry of Electronics and IT)',
            'skills_required': 'Software development, Python, Java, Cybersecurity, AI/ML, Cloud computing',
            'min_gpa': 0.0,
            'qualification': 'B.Tech/B.E.',
            'location': 'New Delhi',
            'deadline': '',
            'application_link': 'https://intern.meity.gov.in/schedules',
            'internship_url': 'https://intern.meity.gov.in/schedules',
            'source': 'MeitY',
            'description': 'Digital India Internship Scheme for CS/IT/ECE/Data Science students.',
            'stipend': 'Paid',
            'duration': '2 months',
            'status': 'Open',
        })
    return records

def scrape_isro():
    records = []
    url = 'https://www.isro.gov.in/InternshipAndProjects.html'
    centres = [
        ('VSSC Thiruvananthapuram', 'Aerospace Engineering, Mechanical Engineering, Electronics, CS', 'Aerodynamics, Structural analysis, Propulsion, Embedded systems, C/C++, MATLAB'),
        ('SAC Ahmedabad', 'Electronics, CS, Remote Sensing, Physics', 'Satellite communications, Antenna design, Remote sensing, GIS, Python/MATLAB'),
        ('URSC Bangalore', 'Electronics, Electrical, CS, Mechanical, Aerospace', 'Spacecraft systems, Satellite integration, PCB design, Embedded systems'),
        ('NRSC Hyderabad', 'Remote Sensing, GIS, Geography, CS', 'GIS/Remote Sensing, Python, QGIS/ArcGIS, Image processing'),
        ('ISTRAC Bangalore', 'CS, Electronics, Electrical, Networking', 'Networking, Software development, Signal processing, RF systems, Python/C++'),
    ]
    for centre, disciplines, skills in centres:
        records.append({
            'internship_title': f'ISRO Student Project Trainee — {centre}',
            'organization': 'ISRO',
            'skills_required': skills,
            'min_gpa': 0.0,
            'qualification': normalize_qualification(disciplines),
            'location': centre.split(' ', 1)[1] if ' ' in centre else 'India',
            'deadline': '',
            'application_link': url,
            'internship_url': url,
            'source': 'ISRO',
            'description': f'ISRO Internship at {centre}. Disciplines: {disciplines}.',
            'stipend': 'Unpaid',
            'duration': '1-6 months',
            'status': 'Open',
        })
    return records

def scrape_drdo():
    records = []
    url = 'https://drdo.gov.in/drdo/en/search/node?keys=Internship'
    labs = [
        ('CAIR Bangalore', 'CS, AI/ML, Robotics, Electronics', 'AI/ML, Python, TensorFlow/PyTorch, Robotics, Computer vision, NLP, C++'),
        ('SAG Delhi', 'CS, Mathematics, Cryptography', 'Cryptography, Cybersecurity, Network security, Algorithms, Python/C++'),
        ('DRDL Hyderabad', 'Aerospace, Mechanical, Chemical, Electronics', 'Aerodynamics, Missile systems, Propulsion, CFD, MATLAB'),
        ('NPOL Kochi', 'Electronics, Acoustics, Mechanical, CS', 'Sonar systems, Underwater acoustics, Signal processing, MATLAB'),
        ('HEMRL Pune', 'Chemical Engineering, Chemistry, Materials Science', 'Energetic materials, Chemistry synthesis, Chemical analysis'),
    ]
    for lab, disciplines, skills in labs:
        records.append({
            'internship_title': f'DRDO Project Trainee — {lab}',
            'organization': 'DRDO',
            'skills_required': skills,
            'min_gpa': 0.0,
            'qualification': normalize_qualification(disciplines),
            'location': lab.split(' ', 1)[1] if ' ' in lab else 'India',
            'deadline': '',
            'application_link': url,
            'internship_url': url,
            'source': 'DRDO',
            'description': f'DRDO Internship/Project Trainee at {lab}.',
            'stipend': 'Unpaid / ₹5,000–₹10,000',
            'duration': '4-6 months',
            'status': 'Open',
        })
    return records

def run_all_scrapers():
    all_records = []
    scrapers = [
        ('NITI Aayog', scrape_niti_aayog),
        ('MEA', scrape_mea),
        ('MeitY', scrape_meity),
        ('ISRO', scrape_isro),
        ('DRDO', scrape_drdo),
    ]
    results = {}
    for name, fn in scrapers:
        try:
            records = fn()
            all_records.extend(records)
            results[name] = {'status': 'success', 'count': len(records)}
        except Exception as e:
            results[name] = {'status': 'error', 'message': str(e)}
        time.sleep(0.5)

    return pd.DataFrame(all_records) if all_records else pd.DataFrame(), results
