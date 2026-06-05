import os
import json
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import datetime

from modules.database import init_db, upsert_internships, get_all_internships, get_internship_by_id, get_stats, export_to_csv
from modules.data_cleaner import build_final_dataset
from modules.recommendation import get_recommendations
from modules.scraper import run_all_scrapers

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'gov-internship-secret-2024')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'data', 'uploads')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
FINAL_CSV = os.path.join(DATA_DIR, 'final_government_internships.csv')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

init_db()

def seed_initial_data():
    from modules.database import get_stats
    stats = get_stats()
    if stats['total'] == 0:
        try:
            df = build_final_dataset()
            if not df.empty:
                upsert_internships(df)
        except Exception as e:
            print(f"Seed error: {e}")

seed_initial_data()

@app.route('/')
def index():
    stats = get_stats()
    internships = get_all_internships()
    recent = internships[:6]
    return render_template('index.html', stats=stats, recent=recent)

@app.route('/search')
def search():
    keyword = request.args.get('keyword', '').strip()
    location = request.args.get('location', '').strip()
    qualification = request.args.get('qualification', '').strip()
    status = request.args.get('status', 'All').strip()

    internships = get_all_internships(
        status_filter=status if status != 'All' else None,
        location_filter=location or None,
        keyword=keyword or None,
        qualification_filter=qualification or None,
    )

    locations = sorted(set(i['location'] for i in get_all_internships() if i.get('location')))
    qualifications = ['Any Graduate', 'B.Tech/B.E.', 'M.Tech/M.E.', 'MBA', 'B.Sc.', 'M.Sc.', 'PhD', 'Diploma', 'LLB', 'BCA', 'MCA']

    return render_template('search.html',
                           internships=internships,
                           keyword=keyword,
                           location=location,
                           qualification=qualification,
                           status=status,
                           locations=locations[:50],
                           qualifications=qualifications,
                           total=len(internships))

@app.route('/internship/<int:internship_id>')
def internship_detail(internship_id):
    internship = get_internship_by_id(internship_id)
    if not internship:
        flash('Internship not found.', 'error')
        return redirect(url_for('search'))
    return render_template('internship_detail.html', internship=internship)

@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    recommendations = []
    student_data = {}
    error = None

    if request.method == 'POST':
        gpa = request.form.get('gpa', '').strip()
        qualification = request.form.get('qualification', '').strip()
        skills = request.form.get('skills', '').strip()
        location = request.form.get('location', '').strip()
        name = request.form.get('name', '').strip()

        if not gpa or not qualification or not skills:
            error = 'Please fill in GPA, Qualification, and Skills fields.'
        else:
            try:
                gpa_float = float(gpa)
                if not (0 <= gpa_float <= 10):
                    error = 'GPA must be between 0 and 10.'
                else:
                    student_data = {
                        'name': name or 'Student',
                        'gpa': gpa_float,
                        'qualification': qualification,
                        'skills': skills,
                        'location': location or 'Pan India',
                    }
                    internships = get_all_internships()
                    recommendations = get_recommendations(
                        gpa_float, qualification, skills, location or 'Pan India',
                        internships, top_n=10
                    )
            except ValueError:
                error = 'Please enter a valid GPA (e.g., 7.5).'

    qualifications = ['Any Graduate', 'B.Tech/B.E.', 'M.Tech/M.E.', 'MBA', 'B.Sc.', 'M.Sc.',
                      'PhD', 'Diploma', 'LLB', 'BCA', 'MCA', 'Any Postgraduate', 'Any Undergraduate']
    return render_template('recommend.html',
                           recommendations=recommendations,
                           student_data=student_data,
                           error=error,
                           qualifications=qualifications)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    message = None
    error = None
    scrape_results = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'scrape':
            try:
                scraped_df, results = run_all_scrapers()
                if not scraped_df.empty:
                    inserted = upsert_internships(scraped_df)
                    scraped_df_path = os.path.join(DATA_DIR, 'scraped_internships.csv')
                    scraped_df.to_csv(scraped_df_path, index=False)
                    message = f'Scraping complete. Found {len(scraped_df)} internships, inserted {inserted} new records.'
                else:
                    message = 'Scraping complete but no new internships found.'
                scrape_results = results
            except Exception as e:
                error = f'Scraping failed: {str(e)}'

        elif action == 'rebuild':
            try:
                df = build_final_dataset()
                if not df.empty:
                    inserted = upsert_internships(df)
                    message = f'Dataset rebuilt. Processed {len(df)} internships, inserted {inserted} new records.'
                else:
                    error = 'No data found to process.'
            except Exception as e:
                error = f'Rebuild failed: {str(e)}'

        elif action == 'upload':
            files = request.files.getlist('csv_files')
            uploaded_paths = []
            for f in files:
                if f and f.filename.endswith('.csv'):
                    fname = secure_filename(f.filename)
                    fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
                    f.save(fpath)
                    uploaded_paths.append(fpath)

            if uploaded_paths:
                try:
                    df = build_final_dataset(uploaded_files=uploaded_paths)
                    if not df.empty:
                        inserted = upsert_internships(df)
                        message = f'Uploaded and processed {len(uploaded_paths)} file(s). Found {len(df)} internships, inserted {inserted} new records.'
                    else:
                        error = 'Uploaded files processed but no valid internships found.'
                except Exception as e:
                    error = f'Upload processing failed: {str(e)}'
            else:
                error = 'Please upload at least one valid CSV file.'

    stats = get_stats()
    internships = get_all_internships()
    return render_template('admin.html',
                           stats=stats,
                           message=message,
                           error=error,
                           scrape_results=scrape_results,
                           internship_count=len(internships))

@app.route('/export')
def export():
    try:
        export_path = os.path.join(DATA_DIR, 'final_government_internships.csv')
        count = export_to_csv(export_path)
        return send_file(export_path, as_attachment=True,
                         download_name=f'gov_internships_{datetime.now().strftime("%Y%m%d")}.csv',
                         mimetype='text/csv')
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('admin'))

@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

@app.route('/api/internships')
def api_internships():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    keyword = request.args.get('keyword', '')
    location = request.args.get('location', '')
    status = request.args.get('status', '')

    internships = get_all_internships(
        status_filter=status or None,
        location_filter=location or None,
        keyword=keyword or None,
    )
    total = len(internships)
    start = (page - 1) * per_page
    paginated = internships[start:start + per_page]
    return jsonify({'internships': paginated, 'total': total, 'page': page, 'per_page': per_page})

@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    gpa = data.get('gpa', 0)
    qualification = data.get('qualification', '')
    skills = data.get('skills', '')
    location = data.get('location', 'Pan India')

    internships = get_all_internships()
    results = get_recommendations(gpa, qualification, skills, location, internships)
    return jsonify({'recommendations': results, 'total': len(results)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
