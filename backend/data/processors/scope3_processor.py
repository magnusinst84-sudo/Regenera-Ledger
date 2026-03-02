"""
data/processors/scope3_processor.py
Teammate 2 — Data / Matching

Builds a supplier network graph from:
  - ESG report text (extracted by pdf_extractor.py)
  - Shipping manifest DataFrame (produced by manifest_parser.py)

Output (shared with T1 Gemini routes and T3 Leaflet / D3 viz):
{
  "nodes": [
    { "id": "S1", "label": "Supplier A", "type": "disclosed" },
    { "id": "S2", "label": "Supplier B", "type": "hidden" }
  ],
  "edges": [
    { "source": "Company",  "target": "S1", "label": "tier1" },
    { "source": "S1",       "target": "S2", "label": "subcontract" }
  ],
  "summary": {
    "total_suppliers": 5,
    "disclosed": 3,
    "hidden": 2,
    "total_emissions_tco2e": 1234.5
  }
}
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def build_supplier_graph(
    esg_text: str,
    manifest_df: pd.DataFrame,
    company_name: str = "Company",
) -> dict[str, Any]:
    """
    Build a supplier network graph.

    Args:
        esg_text:     Clean text from the company's ESG PDF report.
        manifest_df:  DataFrame from manifest_parser.parse_manifest().
        company_name: Root node label (the reporting company).

    Returns:
        Dict with 'nodes', 'edges', and 'summary' keys matching the
        shared data contract defined in the hackathon plan.
    """
    # 1. Extract suppliers mentioned in the ESG text
    disclosed_suppliers = _extract_disclosed_suppliers(esg_text)

    # 2. Extract suppliers from the manifest data
    manifest_suppliers = _extract_manifest_suppliers(manifest_df)

    # 3. Classify: disclosed vs hidden (in manifest but NOT mentioned in ESG text)
    hidden_suppliers = manifest_suppliers - disclosed_suppliers

    # 4. Build nodes
    nodes: list[dict] = [{"id": "Company", "label": company_name, "type": "company"}]
    node_id_map: dict[str, str] = {}

    for i, supplier in enumerate(sorted(disclosed_suppliers)):
        nid = _make_id(supplier, i)
        node_id_map[supplier] = nid
        nodes.append({"id": nid, "label": supplier, "type": "disclosed"})

    for i, supplier in enumerate(sorted(hidden_suppliers)):
        nid = _make_id(supplier, i + len(disclosed_suppliers))
        node_id_map[supplier] = nid
        nodes.append({"id": nid, "label": supplier, "type": "hidden"})

    # 5. Build edges from manifest rows
    edges: list[dict] = []
    seen_edges: set[tuple] = set()

    for _, row in manifest_df.iterrows():
        supplier = str(row.get("supplier", "")).strip()
        if not supplier:
            continue

        node_id = node_id_map.get(supplier)
        if not node_id:
            # Add previously unseen supplier as hidden
            node_id = _make_id(supplier, len(nodes))
            node_id_map[supplier] = node_id
            nodes.append({"id": node_id, "label": supplier, "type": "hidden"})

        edge_key = ("Company", node_id)
        if edge_key not in seen_edges:
            edges.append({
                "source": "Company",
                "target": node_id,
                "label": "tier1",
                "transport_mode": str(row.get("transport_mode", "unknown")),
                "emissions_factor": float(row.get("emissions_factor", 0.0)),
                "quantity": float(row.get("quantity", 0.0)),
            })
            seen_edges.add(edge_key)

    # 6. Infer subcontract edges for hidden suppliers
    for _, row in manifest_df.iterrows():
        origin = str(row.get("origin", "")).strip()
        supplier = str(row.get("supplier", "")).strip()
        if origin and origin in node_id_map and supplier and supplier in node_id_map:
            if origin != supplier:
                edge_key = (node_id_map[origin], node_id_map[supplier])
                if edge_key not in seen_edges:
                    edges.append({
                        "source": node_id_map[origin],
                        "target": node_id_map[supplier],
                        "label": "subcontract",
                    })
                    seen_edges.add(edge_key)

    # 7. Calculate total emissions
    total_emissions = _calculate_total_emissions(manifest_df)

    # 8. Assemble output
    graph = {
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "total_suppliers": len(nodes) - 1,  # exclude company root
            "disclosed": len(disclosed_suppliers),
            "hidden": len(hidden_suppliers),
            "total_emissions_tco2e": round(total_emissions, 3),
        },
    }

    logger.info(
        "Supplier graph built: %d nodes, %d edges, %.1f tCO₂e total",
        len(nodes),
        len(edges),
        total_emissions,
    )
    return graph


# ──────────────────────────────────────────────
# Internals
# ──────────────────────────────────────────────

def _extract_disclosed_suppliers(esg_text: str) -> set[str]:
    """
    Pull supplier/vendor names referenced in the ESG report text.
    Uses regex heuristics to find capitalised noun phrases near
    supply-chain keywords.
    """
    # Keywords that signal a supplier reference
    trigger = re.compile(
        r"(supplier|vendor|partner|contractor|subcontractor|tier[-\s]?\d|procured from|sourced from)",
        re.IGNORECASE,
    )
    # Proper noun phrase after the keyword (up to 5 title-case words)
    noun_phrase = re.compile(r"([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+){0,4})")

    suppliers: set[str] = set()
    for match in trigger.finditer(esg_text):
        window = esg_text[match.end(): match.end() + 120]
        for m2 in noun_phrase.finditer(window):
            candidate = m2.group(1).strip()
            # Filter out common words that aren't supplier names
            if len(candidate) > 3 and candidate not in _STOPWORDS:
                suppliers.add(candidate)
    return suppliers


def _extract_manifest_suppliers(df: pd.DataFrame) -> set[str]:
    """Get unique supplier names from manifest DataFrame."""
    if "supplier" not in df.columns:
        return set()
    return {str(s).strip() for s in df["supplier"].dropna() if str(s).strip()}


def _make_id(name: str, index: int) -> str:
    """Generate a short stable ID for a supplier node."""
    prefix = "".join(w[0].upper() for w in name.split()[:3]) or "S"
    suffix = hashlib.md5(name.encode()).hexdigest()[:4].upper()
    return f"{prefix}{index}_{suffix}"


def _calculate_total_emissions(df: pd.DataFrame) -> float:
    """
    Estimate total Scope 3 emissions (tCO₂e) from manifest.
    Formula: quantity (tonnes) × emissions_factor (kg CO₂e/t-km) × assumed_distance_km
    Distance defaults to 500 km when not provided.
    """
    if df.empty:
        return 0.0
    qty = pd.to_numeric(df.get("quantity", pd.Series(dtype=float)), errors="coerce").fillna(0)
    ef = pd.to_numeric(df.get("emissions_factor", pd.Series(dtype=float)), errors="coerce").fillna(0.1)
    distance = pd.to_numeric(df.get("distance_km", pd.Series(dtype=float)), errors="coerce").fillna(500)
    # kg → tonnes: divide by 1000
    return float((qty * ef * distance / 1000).sum())


_STOPWORDS = {
    "The", "This", "Our", "Their", "These", "Those", "With", "From",
    "That", "Within", "Under", "Above", "Below", "Between", "Among",
    "Company", "Report", "Annual", "Carbon", "Emission", "Climate",
    "Global", "Supply", "Chain", "Sustainability", "Environmental",
}


# ──────────────────────────────────────────────
# CLI helper (quick test)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import json
    import sys
    from data.parsers.pdf_extractor import extract_text_from_pdf
    from data.parsers.manifest_parser import parse_manifest

    if len(sys.argv) < 3:
        print("Usage: python scope3_processor.py <esg_pdf> <manifest_csv_or_pdf>")
        sys.exit(1)

    esg = extract_text_from_pdf(sys.argv[1])
    manifest = parse_manifest(sys.argv[2])
    graph = build_supplier_graph(esg, manifest)
    print(json.dumps(graph, indent=2))
