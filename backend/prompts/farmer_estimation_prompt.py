"""
Prompt template: Farmer Carbon Sequestration Estimation
Output keys: sequestration_capacity_tons, credibility_score, yearly_credit_potential, explanation
"""


def build_farmer_estimation_prompt(farmer_profile: dict) -> str:
    return f"""You are an agricultural carbon credit expert specializing in sequestration estimation
and Verified Carbon Standard (VCS) / Gold Standard methodologies.

Estimate the carbon sequestration capacity and credit potential for the following farmer profile.

FARMER PROFILE:
- Land Size: {farmer_profile.get('land_size_hectares', 'N/A')} hectares
- Crop Type: {farmer_profile.get('crop_type', 'N/A')}
- Soil Type: {farmer_profile.get('soil_type', 'N/A')}
- Irrigation Method: {farmer_profile.get('irrigation_method', 'N/A')}
- Farming Practices: {farmer_profile.get('farming_practices', [])}
- Location: {farmer_profile.get('location', {})}
- Years Farming: {farmer_profile.get('years_farming', 'N/A')}
- Current Certifications: {farmer_profile.get('certifications', [])}

Your tasks:
1. Estimate annual carbon sequestration capacity in tCO2e based on land, crop, and practices.
2. Assign a credibility score (0–100) based on verifiability of practices and data completeness.
3. Calculate yearly carbon credit potential (sellable credits after buffer/uncertainty deduction).
4. Provide a detailed explanation of your estimation methodology.

Respond ONLY with valid JSON in exactly this structure:
{{
  "sequestration_capacity_tons": <number>,
  "credibility_score": <integer 0-100>,
  "yearly_credit_potential": {{
    "gross_sequestration_tco2e": <number>,
    "buffer_deduction_pct": <number>,
    "net_sellable_credits_tco2e": <number>,
    "estimated_revenue_usd_low": <number>,
    "estimated_revenue_usd_high": <number>
  }},
  "improvement_recommendations": [
    "<recommendation to increase sequestration or credibility>"
  ],
  "eligible_standards": [<list of applicable carbon credit standards>],
  "explanation": "<detailed explanation of estimation methodology and assumptions>"
}}

Do not include any text outside the JSON object.
"""
