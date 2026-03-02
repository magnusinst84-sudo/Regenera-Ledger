"""
Prompt template: Company-Farmer Carbon Credit Matching
Output keys: ranked_matches: [{farmer_id, coverage_pct, suitability_score, reasoning}]
"""


def build_matching_prompt(company_gap: dict, farmers: list) -> str:
    farmers_json = "\n".join([
        f"  Farmer {i+1}: ID={f.get('farmer_id')}, Land={f.get('land_size_hectares')}ha, "
        f"Crop={f.get('crop_type')}, Sequestration={f.get('sequestration_capacity_tons')}tCO2e/yr, "
        f"Credibility={f.get('credibility_score')}/100, Location={f.get('location', {})}"
        for i, f in enumerate(farmers)
    ])

    return f"""You are a carbon credit marketplace expert specializing in matching corporate carbon buyers
with agricultural carbon credit sellers.

A company needs to offset their carbon gap. Match them with the most suitable farmers from the
available pool, ranked by suitability.

COMPANY CARBON GAP:
- Required Offset: {company_gap.get('credits_needed_tco2e', 0)} tCO2e
- Company Location: {company_gap.get('company_location', 'N/A')}
- Urgency: {company_gap.get('urgency', 'N/A')}
- Budget Range (USD): {company_gap.get('budget_usd', 'N/A')}
- Preferred Crop Types: {company_gap.get('preferred_crop_types', [])}

AVAILABLE FARMERS:
{farmers_json}

Your tasks:
1. Rank farmers by suitability for this company's needs.
2. Calculate what percentage of the company's carbon gap each farmer can cover.
3. Assign a suitability score (0–100) considering: sequestration capacity, credibility, location proximity, crop type alignment.
4. Provide clear reasoning for each match.

Respond ONLY with valid JSON in exactly this structure:
{{
  "ranked_matches": [
    {{
      "farmer_id": <integer>,
      "coverage_pct": <number 0-100>,
      "suitability_score": <integer 0-100>,
      "credits_available_tco2e": <number>,
      "estimated_cost_usd": <number>,
      "reasoning": "<detailed reasoning for this match ranking>"
    }}
  ],
  "matching_summary": {{
    "total_coverage_achievable_pct": <number>,
    "recommended_combination": [<list of farmer_ids for optimal portfolio>],
    "recommendation_explanation": "<why this combination is recommended>"
  }}
}}

Do not include any text outside the JSON object.
"""
