"""
Prompt template: Forensic ESG Audit
Output keys: reported_emissions, greenwashing_score, risk_score, explanation, extracted_entities
"""


def build_esg_analysis_prompt(extracted_text: str) -> str:
    return f"""You are an expert ESG forensic auditor with deep knowledge of sustainability reporting standards
(GRI, SASB, TCFD, CDP) and carbon accounting methodologies.

Analyze the following ESG report text and perform a comprehensive forensic audit.

ESG REPORT TEXT:
\"\"\"
{extracted_text}
\"\"\"

Your task:
1. Extract all reported emissions figures (Scope 1, 2, 3 if present).
2. Identify inconsistencies, vague language, missing data, or signs of greenwashing.
3. Assign a greenwashing score (0–100, where 100 = severe greenwashing).
4. Assign a risk score (0–100, where 100 = highest ESG risk).
5. List all extracted entities (companies, locations, certifications, metrics).
6. Provide a clear forensic explanation of your findings.

Respond ONLY with valid JSON in exactly this structure:
{{
  "reported_emissions": {{
    "scope1_tco2e": <number or null>,
    "scope2_tco2e": <number or null>,
    "scope3_tco2e": <number or null>,
    "total_tco2e": <number or null>,
    "reporting_year": <string or null>
  }},
  "greenwashing_score": <integer 0-100>,
  "risk_score": <integer 0-100>,
  "explanation": "<detailed forensic explanation>",
  "extracted_entities": {{
    "companies": [<list of company names>],
    "locations": [<list of locations>],
    "certifications": [<list of certifications>],
    "key_metrics": [<list of key metric strings>],
    "red_flags": [<list of specific greenwashing red flags found>]
  }}
}}

Do not include any text outside the JSON object.
"""
