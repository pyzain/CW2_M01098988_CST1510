# app/components/ai_core.py
"""
Small AI helper for domain-specific prompt construction.
Used by dashboards to create short context-aware prompts.
"""

from typing import Dict, Any, List

def build_cyber_prompt(question: str, top_incidents: List[Dict[str, Any]] = None) -> str:
    """
    Create a concise prompt for cyber questions.
    `top_incidents` is a list of small dicts (id, type, severity, asset).
    """
    lines = []
    lines.append("You are a concise cybersecurity assistant. Answer briefly and suggest next steps.")
    if top_incidents:
        lines.append("Top incidents summary:")
        for r in top_incidents[:5]:
            lines.append(f"- id:{r.get('id','?')}, type:{r.get('type','')}, severity:{r.get('severity','')}, asset:{r.get('asset','')}")
    lines.append(f"User question: {question}")
    return "\n".join(lines)
