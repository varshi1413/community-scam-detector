# Community Scam Detector

An AI-powered web application that helps students detect fake or suspicious
job and internship offers using Google Gemini.

## Features (Phase 1)
- Paste job/internship offer text
- AI-based scam detection
- Verdict: Fake / Real / Suspicious
- Risk score and explanation
- Stores analyzed offers in database

## Tech Stack
- Frontend: HTML, CSS, JavaScript
- Backend: Python, Flask
- Database: SQLite
- AI: Google Gemini API

## Future Enhancements
- Community-based reviews
- Company-level trust scoring
- AI-generated community summaries

## How to Run
1. Set `GEMINI_API_KEY` environment variable
2. Run backend:
   ```bash
   python backend/app.py
