from flask import Flask, request, jsonify
import sqlite3
import json
import os
from google import genai
from flask_cors import CORS


# ---------------------------
# App setup
# ---------------------------
app = Flask(__name__)
CORS(app)


# ---------------------------
# Gemini AI setup
# ---------------------------
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)

# ---------------------------
# Database setup
# ---------------------------
def init_db():
    conn = sqlite3.connect("offers.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            offer_text TEXT,
            company_name TEXT,
            verdict TEXT,
            risk_score INTEGER,
            reasons TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def extract_company_name(text):
    companies = ["Google", "Microsoft", "Amazon", "Infosys", "TCS", "Wipro"]
    for company in companies:
        if company.lower() in text.lower():
            return company
    return "Unknown"


def save_offer(offer_text, verdict, risk_score, reasons):
    company_name = extract_company_name(offer_text)

    conn = sqlite3.connect("offers.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO offers (offer_text, company_name, verdict, risk_score, reasons)
        VALUES (?, ?, ?, ?, ?)
    """, (
        offer_text,
        company_name,
        verdict,
        risk_score,
        ", ".join(reasons)
    ))

    conn.commit()
    conn.close()


def get_all_offers():
    conn = sqlite3.connect("offers.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM offers")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_offers_by_company(company_name):
    conn = sqlite3.connect("offers.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM offers WHERE company_name = ?",
        (company_name,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


# ---------------------------
# Routes / APIs
# ---------------------------
@app.route("/")
def home():
    return "Community Scam Detector Backend Running"

@app.route("/analyze_offer", methods=["POST"])
def analyze_offer():
    data = request.get_json()
    offer_text = data.get("offer_text", "")

    prompt = f"""
Analyze the job/internship offer below and respond ONLY in valid JSON.

Format:
{{
  "verdict": "Fake or Real or Suspicious",
  "risk_score": number,
  "reasons": ["reason1", "reason2"]
}}

Offer:
{offer_text}
"""

    response = client.models.generate_content(
        model="models/gemini-flash-latest",
        contents=prompt
    )

    raw_text = response.text.strip()
    print("AI RAW RESPONSE:", raw_text)

    try:
        ai_result = json.loads(raw_text)
    except json.JSONDecodeError:
        ai_result = {
            "verdict": "SUSPICIOUS",
            "risk_score": 50,
            "reasons": ["AI response could not be parsed reliably"]
        }


    verdict = ai_result["verdict"]
    risk_score = ai_result["risk_score"]
    reasons = ai_result["reasons"]

    save_offer(offer_text, verdict, risk_score, reasons)

    return jsonify({
        "verdict": verdict,
        "risk_score": risk_score,
        "reasons": reasons
    })
    
@app.route("/offers", methods=["GET"])
def view_offers():
    offers = get_all_offers()
    result = []

    for offer in offers:
        result.append({
            "id": offer[0],
            "offer_text": offer[1],
            "company_name": offer[2],
            "verdict": offer[3],
            "risk_score": offer[4],
            "reasons": offer[5],
            "timestamp": offer[6]
        })

    return jsonify(result)


@app.route("/offers/company/<company_name>", methods=["GET"])
def offers_by_company(company_name):
    offers = get_offers_by_company(company_name)
    result = []

    for offer in offers:
        result.append({
            "id": offer[0],
            "offer_text": offer[1],
            "company_name": offer[2],
            "verdict": offer[3],
            "risk_score": offer[4],
            "reasons": offer[5],
            "timestamp": offer[6]
        })

    return jsonify({
        "company": company_name,
        "count": len(result),
        "offers": result
    })


def summarize_with_rules(company_name, offers):
    total = len(offers)

    fake = 0
    suspicious = 0

    for o in offers:
        verdict = o[3].upper()
        if verdict == "FAKE":
            fake += 1
        elif verdict == "SUSPICIOUS":
            suspicious += 1

    if fake > suspicious:
        final_verdict = "FAKE"
    elif suspicious > 0:
        final_verdict = "SUSPICIOUS"
    else:
        final_verdict = "REAL"

    summary = (
        f"Based on {total} community reports for {company_name}, "
        f"the overall trust level is {final_verdict.lower()}. "
        f"Multiple students reported similar patterns."
    )

    return final_verdict, summary


@app.route("/summary/<company_name>", methods=["GET"])
def company_summary(company_name):
    offers = get_offers_by_company(company_name)

    if not offers:
        return jsonify({
            "company": company_name,
            "message": "No community data available yet."
        })

    final_verdict, summary = summarize_with_rules(company_name, offers)

    return jsonify({
        "company": company_name,
        "reports_count": len(offers),
        "final_verdict": final_verdict,
        "summary": summary
    })


# ---------------------------
# Run app
# ---------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
