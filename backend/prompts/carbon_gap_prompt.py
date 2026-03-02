"""
Prompt template: Carbon Gap Analysis (Claimed vs Actual Emissions)
Output keys: emission_gap, offset_required, financial_risk_exposure, explanation
"""


def build_carbon_gap_prompt(analysis_result: dict) -> str:
    reported = analysis_result.get("reported_emissions", {})
    greenwashing_score = analysis_result.get("greenwashing_score", 0)
    risk_score = analysis_result.get("risk_score", 0)
    entities = analysis_result.get("extracted_entities", {})
    explanation = analysis_result.get("explanation", "")

    return f"""You are a carbon accounting and financial risk expert specializing in carbon gap analysis.

Based on the following ESG forensic analysis results, calculate the true carbon gap between
what a company claims and what they are likely emitting, then assess the financial risk exposure.

FORENSIC ANALYSIS RESULTS:
- Reported Emissions: {reported}
- Greenwashing Score: {greenwashing_score}/100
- Risk Score: {risk_score}/100
- Key Red Flags: {entities.get('red_flags', [])}
- Forensic Explanation: {explanation}

Your tasks:
1. Estimate the actual emissions based on greenwashing score and reported figures.
2. Calculate the carbon gap (actual - reported).
3. Determine how many carbon offset credits are required to neutralize the gap.
4. Estimate financial risk exposure using current carbon credit market pricing (~$15-50/tCO2e).
5. Provide a detailed explanation.

Respond ONLY with valid JSON in exactly this structure:
{{
  "emission_gap": {{
    "reported_total_tco2e": <number>,
    "estimated_actual_tco2e": <number>,
    "gap_tco2e": <number>,
    "gap_percentage": <number>,
    "confidence_level": "<low|medium|high>"
  }},
  "offset_required": {{
    "credits_needed_tco2e": <number>,
    "recommended_offset_types": [<list of offset type strings>],
    "urgency": "<immediate|within_1_year|within_3_years>"
  }},
  "financial_risk_exposure": {{
    "low_estimate_usd": <number>,
    "mid_estimate_usd": <number>,
    "high_estimate_usd": <number>,
    "carbon_price_range_per_tco2e": {{"low": 15, "mid": 30, "high": 50}},
    "regulatory_risk_level": "<low|medium|high|critical>"
  }},
  "explanation": "<detailed carbon gap and financial risk explanation>"
}}

Do not include any text outside the JSON object.
"""
