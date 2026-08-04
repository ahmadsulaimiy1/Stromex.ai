#!/usr/bin/env python3
"""Render every diagram to SVG (for the record) and high-DPI PNG (for embedding)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cairosvg  # noqa: E402

import diagrams_arch as A      # noqa: E402
import diagrams_design as D    # noqa: E402
import diagrams_product as P   # noqa: E402

OUT = "/home/user/Stromex.ai/publication/build/diagrams"
SCALE = 3.0          # 900 px logical → 2700 px raster; placed ~6.3 in ⇒ ≈ 430 DPI

# (builder, anchor heading it follows, chapter)
FIGURES = [
    (D.decision_rules,        0,  "0.9"),
    (D.palette_sheet,         2,  "2.5"),
    (D.spacing_radius,        2,  "2.12"),
    (D.navigation_ia,         3,  "3.1"),
    (D.thumb_zones,           3,  "3.12"),
    (D.ai_decision,           4,  "4.1"),
    (D.ai_pipeline,           4,  "4.9"),
    (P.message_anatomy,       5,  "5.1"),
    (A.notification_flow,     5,  "5.12"),
    (A.system_architecture,   6,  "6.1"),
    (A.backend_services,      6,  "6.3"),
    (A.encryption_map,        6,  "6.7"),
    (A.sync_architecture,     6,  "6.8"),
    (A.auth_flow,             6,  "6.6"),
    (D.design_token_hierarchy, 7, "7.1"),
    (P.performance_budget,    8,  "8.5"),
    (P.roadmap_timeline,      9,  "Phase 1 — MVP"),
    (P.scope_funnel,          10, "10.1"),
    (P.journey_first_run,     13, "13.4"),
    (P.journey_translation,   13, "13.4"),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = []
    for i, (fn, chapter, after) in enumerate(FIGURES, start=1):
        name, svg, caption = fn()
        svg_path = os.path.join(OUT, name + ".svg")
        png_path = os.path.join(OUT, name + ".png")
        svg.save(svg_path)
        cairosvg.svg2png(url=svg_path, write_to=png_path, scale=SCALE,
                         background_color="#FFFFFF")
        manifest.append({
            "n": i, "name": name, "caption": caption, "chapter": chapter,
            "after": after, "png": png_path, "svg": svg_path,
            "w": svg.w, "h": svg.h,
            "bytes": os.path.getsize(png_path),
        })
        print(f"  fig {i:>2}  {name:<28} {svg.w}×{svg.h}  →  {os.path.getsize(png_path)//1024} KB")
    with open(os.path.join(OUT, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)
    print(f"\n{len(manifest)} figures rendered at {SCALE}× ({int(900*SCALE)} px wide)")


if __name__ == "__main__":
    main()
