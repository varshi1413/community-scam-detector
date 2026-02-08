from google import genai

client = genai.Client(api_key="AIzaSyD2tDHIx3eAf73nJcoq0DC-zJxfnGjMFww")

job_post = """
We are hiring freshers.
Salary: 45,000 per month.
No interview required.
Contact HR on WhatsApp: +91 9XXXXXXXXX
"""

prompt = f"""
You are a scam detection assistant.

Analyze the job post below and respond in this format:

Verdict: Fake or Real
Reason: One short explanation
Confidence: Percentage

Job Post:
{job_post}
"""

response = client.models.generate_content(
    model="models/gemini-flash-latest",
    contents=prompt
)

print(response.text)
