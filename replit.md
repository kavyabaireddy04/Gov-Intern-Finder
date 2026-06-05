# GovIntern India

AI-powered Government Internship Recommendation System for Indian students — no API keys, 100% free.

## Run & Operate

- `cd gov_internship && python app.py` — run the Flask app (port 5000)
- Workflow "GovIntern App" starts it automatically

## Stack

- Python 3.11, Flask, SQLite
- scikit-learn (TF-IDF + Cosine Similarity)
- pandas, BeautifulSoup4, requests (scraping)
- pdfplumber (PDF extraction)
- Pure HTML/CSS/JS frontend (no React)

## Where things live

- `gov_internship/app.py` — Flask application entry point
- `gov_internship/modules/recommendation.py` — TF-IDF scoring + eligibility engine
- `gov_internship/modules/data_cleaner.py` — CSV parsing and data normalization
- `gov_internship/modules/scraper.py` — Government portal scrapers
- `gov_internship/modules/database.py` — SQLite CRUD operations
- `gov_internship/db/internships.db` — SQLite database
- `gov_internship/data/` — CSV files (sources + processed)
- `gov_internship/templates/` — Jinja2 HTML templates
- `gov_internship/static/` — CSS and JS

## Architecture decisions

- SQLite chosen over PostgreSQL for zero-config free-tier compatibility
- TF-IDF + Cosine Similarity replaces any LLM — fully offline, no API keys
- Weighted scoring: Skills 40%, GPA 25%, Qualification 20%, Location 15%
- Each internship gets a unique computed score (no shared scores)
- Eligibility scoring is separate from match scoring for clarity
- Government org detection uses keyword matching against india_gov_internship_sources.csv

## Product

- Dashboard with live stats (total, open, closing soon, orgs, sources)
- Quick match form on homepage
- Browse/search with keyword, location, qualification, status filters
- Personalized recommendation engine returning Top 10 ranked internships
- Per-recommendation breakdown: skill bar, GPA, qualification, location scores
- Missing skills identified per recommendation
- Apply Now links to official government portals
- Admin panel: run scrapers, rebuild dataset, upload CSVs, export data
- CSV export of full dataset

## Gotchas

- Flask must be started from the `gov_internship/` directory (cd is important for relative paths)
- After uploading new CSVs, click "Rebuild Dataset" in Admin panel to re-process
- The workflow "GovIntern App" must be running for the site to be accessible
- Government scraper uses polite delays (0.5s between requests) to avoid being blocked

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
