"""The two diagrams that earn their place.

Restrained on purpose. A diagram that restates a list adds pages and subtracts
attention; these two show a *mechanism* the prose can only describe
sequentially — a control flow, and a one-to-many relationship.

Authored as SVG so the PDF gets vectors, and rasterised for Word (which has no
dependable SVG support) by `render_docx`. Both formats therefore show the same
figure rather than one showing a placeholder.
"""

from __future__ import annotations

BRAND_DEFS = """
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#2E7FD1"/><stop offset="100%" stop-color="#7A3FD6"/>
    </linearGradient>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7178"/>
    </marker>
  </defs>
"""

APPROVAL_GATE = f"""
<svg viewBox="0 0 760 250" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="The AI approval gate: propose, persist, review, approve, apply">
{BRAND_DEFS}
  <style>
    .t  {{ font-family: Inter, sans-serif; font-size: 13px; fill: #16191c; }}
    .s  {{ font-family: Inter, sans-serif; font-size: 10.5px; fill: #6b7178; }}
    .lb {{ font-family: Inter, sans-serif; font-size: 9px; fill: #6b7178;
           letter-spacing: 1.4px; text-transform: uppercase; }}
    .bx {{ fill: #f5f5f1; stroke: #d9d9d3; stroke-width: 1; }}
    .hu {{ fill: #ffffff; stroke: #16324f; stroke-width: 1.6; }}
    .ln {{ stroke: #6b7178; stroke-width: 1.2; marker-end: url(#arrow); }}
  </style>

  <text x="0" y="14" class="lb">Machine</text>
  <rect x="0"   y="26" width="150" height="60" rx="4" class="bx"/>
  <text x="16"  y="52" class="t">AI proposes</text>
  <text x="16"  y="70" class="s">draft, never a write</text>

  <rect x="196" y="26" width="150" height="60" rx="4" class="bx"/>
  <text x="212" y="52" class="t">Proposal persisted</text>
  <text x="212" y="70" class="s">with full provenance</text>

  <text x="392" y="14" class="lb">Human</text>
  <rect x="392" y="26" width="150" height="60" rx="4" class="hu"/>
  <text x="408" y="52" class="t">Human reviews</text>
  <text x="408" y="70" class="s">and approves, or not</text>

  <rect x="588" y="26" width="150" height="60" rx="4" class="hu"/>
  <text x="604" y="52" class="t">Applied</text>
  <text x="604" y="70" class="s">attributed and audited</text>

  <line x1="152" y1="56" x2="192" y2="56" class="ln"/>
  <line x1="348" y1="56" x2="388" y2="56" class="ln"/>
  <line x1="544" y1="56" x2="584" y2="56" class="ln"/>

  <path d="M 467 88 L 467 130" class="ln"/>
  <rect x="392" y="136" width="150" height="52" rx="4" class="bx"/>
  <text x="408" y="160" class="t">Rejected</text>
  <text x="408" y="177" class="s">recorded, discarded</text>

  <rect x="0" y="206" width="738" height="40" rx="4" fill="#ffffff" stroke="#7A3FD6"
        stroke-width="1.4"/>
  <rect x="0" y="206" width="3" height="40" fill="url(#g)"/>
  <text x="18" y="223" class="t">There is no code path that writes an academic record from a model response.</text>
  <text x="18" y="239" class="s">The applying step requires an approval row with a distinct approver. A test attempts the bypass and must fail.</text>
</svg>
"""

SIX_HUMANS = """
<svg viewBox="0 0 760 300" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Six personas, six information architectures, one domain model">
  <style>
    .t  { font-family: Inter, sans-serif; font-size: 12.5px; fill: #16191c; font-weight: 600; }
    .s  { font-family: Inter, sans-serif; font-size: 10px; fill: #6b7178; }
    .c  { font-family: Inter, sans-serif; font-size: 12px; fill: #ffffff; font-weight: 600; }
    .lb { font-family: Inter, sans-serif; font-size: 9px; fill: #6b7178; letter-spacing: 1.4px; }
    .bx { fill: #ffffff; stroke: #d9d9d3; stroke-width: 1; }
    .ln { stroke: #d9d9d3; stroke-width: 1; }
  </style>

  <rect x="280" y="126" width="200" height="48" rx="4" fill="#16324f"/>
  <text x="300" y="147" class="c">One domain model</text>
  <text x="300" y="164" class="s" fill="#a8b2bb">records, not screens</text>

  <rect x="0"   y="10" width="230" height="52" rx="4" class="bx"/>
  <text x="16"  y="32" class="t">Administrator</text>
  <text x="16"  y="49" class="s">Efficiency · bulk · audit trail</text>

  <rect x="0"   y="76" width="230" height="52" rx="4" class="bx"/>
  <text x="16"  y="98" class="t">Teacher</text>
  <text x="16"  y="115" class="s">Today · fewest clicks · on a phone</text>

  <rect x="0"   y="142" width="230" height="52" rx="4" class="bx"/>
  <text x="16"  y="164" class="t">Student</text>
  <text x="16"  y="181" class="s">Due next · clear · encouraging</text>

  <rect x="530" y="10" width="230" height="52" rx="4" class="bx"/>
  <text x="546" y="32" class="t">Parent</text>
  <text x="546" y="49" class="s">Reassurance · plain language</text>

  <rect x="530" y="76" width="230" height="52" rx="4" class="bx"/>
  <text x="546" y="98" class="t">Principal</text>
  <text x="546" y="115" class="s">Overview · trend · drill-down</text>

  <rect x="530" y="142" width="230" height="52" rx="4" class="bx"/>
  <text x="546" y="164" class="t">Platform operator</text>
  <text x="546" y="181" class="s">Health · never content, without break-glass</text>

  <line x1="232" y1="36"  x2="278" y2="140" class="ln"/>
  <line x1="232" y1="102" x2="278" y2="146" class="ln"/>
  <line x1="232" y1="168" x2="278" y2="154" class="ln"/>
  <line x1="528" y1="36"  x2="482" y2="140" class="ln"/>
  <line x1="528" y1="102" x2="482" y2="146" class="ln"/>
  <line x1="528" y1="168" x2="482" y2="154" class="ln"/>

  <text x="0" y="230" class="lb">SIX PEOPLE · SIX INFORMATION ARCHITECTURES · ONE SET OF RECORDS</text>
  <line x1="0" y1="240" x2="760" y2="240" stroke="#d9d9d3" stroke-width="1"/>
  <text x="0" y="262" class="s">Not one dashboard with the heading swapped. Each experience is organised around what that person came to do,</text>
  <text x="0" y="278" class="s">and shows only what their permissions and scope allow — the same predicates that guard every query.</text>
</svg>
"""

DIAGRAMS: dict[str, str] = {
    "approval-gate": APPROVAL_GATE,
    "six-humans": SIX_HUMANS,
}

__all__ = ["DIAGRAMS"]
