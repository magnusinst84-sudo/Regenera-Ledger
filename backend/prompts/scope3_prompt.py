"""
Prompt template: Cross-Doc Supply Chain Scope 3 Reasoning
Output keys: hidden_suppliers, emission_discrepancy, network_graph, forensic_explanation
"""


def build_scope3_prompt(esg_text: str, supplier_data: str) -> str:
    return f"""You are a Scope 3 supply chain emissions expert with forensic accounting skills.

You have been given two documents:
1. A company's ESG report (primary document)
2. Shipping manifest / supplier data (secondary document)

Your task is to cross-reference these documents to uncover hidden or undisclosed Scope 3 emissions,
identify discrepancies, and map the supply chain network.

ESG REPORT:
\"\"\"
{esg_text}
\"\"\"

SUPPLIER / MANIFEST DATA:
\"\"\"
{supplier_data}
\"\"\"

Analysis tasks:
1. Identify suppliers mentioned in manifest data but NOT disclosed in the ESG report.
2. Calculate emission discrepancies between reported and detected supply chain emissions.
3. Build a supplier network graph (nodes + edges).
4. Provide a forensic explanation of your cross-document findings.

Respond ONLY with valid JSON in exactly this structure:
{{
  "hidden_suppliers": [
    {{
      "supplier_name": "<name>",
      "estimated_emissions_tco2e": <number>,
      "evidence": "<brief evidence from manifest>",
      "risk_level": "<low|medium|high>"
    }}
  ],
  "emission_discrepancy": {{
    "reported_scope3_tco2e": <number or null>,
    "detected_scope3_tco2e": <number>,
    "discrepancy_tco2e": <number>,
    "discrepancy_percentage": <number>
  }},
  "network_graph": {{
    "nodes": [
      {{"id": "<id>", "label": "<name>", "type": "<company|disclosed|hidden>"}}
    ],
    "edges": [
      {{"source": "<id>", "target": "<id>", "label": "<tier1|subcontract|logistics>"}}
    ]
  }},
  "forensic_explanation": "<detailed cross-document forensic explanation>"
}}

Do not include any text outside the JSON object.
"""
