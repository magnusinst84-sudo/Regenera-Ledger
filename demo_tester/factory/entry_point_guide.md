# Factory User Entry Point - Demo Guide

This folder contains the entry point documents for a **Company/Factory** user testing the Regenera Ledger platform.

## Test Workflow:

1. **Upload ESG Report**: 
   - Use `esg_report_2024.txt` in the **ESG Analysis** section of the dashboard.
   - The AI will extract the Scope 1/2/3 data and calculate your current ESG score.

2. **Map Supply Chain**:
   - Use `supplier_manifest.csv` in the **Scope 3 Mapping** section. 
   - This will populate your supplier graph and identify high-emission partners.

3. **Carbon Gap & Matching**:
   - Once the AI identifies your 3,000 tCO2e gap, navigate to the **Marketplace**.
   - You will see matched farmers (like those using the sample farmer docs) who can provide credits to offset your gap.

## Files:
- `esg_report_2024.txt`: Sample text for AI analysis.
- `supplier_manifest.csv`: Structured data for supply chain mapping.
