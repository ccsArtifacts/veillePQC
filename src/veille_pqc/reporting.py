from __future__ import annotations

import csv
import html
from datetime import datetime
from pathlib import Path

from veille_pqc.models import Item
from veille_pqc.scoring import classify_priority


def sort_items(items: list[Item]) -> list[Item]:
    return sorted(items, key=lambda x: (x.score, x.published or datetime.min), reverse=True)


def _filter_items(items: list[Item], sector: str | None = None) -> list[Item]:
    if not sector:
        return items
    return [item for item in items if sector.lower() in [s.lower() for s in item.sector_tags]]


def to_markdown(items: list[Item], output_path: str | Path, sector: str | None = None) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    selected = sort_items(_filter_items(items, sector))
    rows = [
        "# Rapport de veille PQC",
        "",
        f"Généré le : {datetime.utcnow().isoformat()}Z",
    ]
    if sector:
        rows += [f"Secteur filtré : {sector}", ""]
    else:
        rows.append("")
    rows += [
        "| Priorité | Score | Catégorie | Secteurs | Source | Titre | Date | URL |",
        "|---|---:|---|---|---|---|---|---|",
    ]
    for item in selected:
        date_str = item.published.date().isoformat() if item.published else ""
        title = item.title.replace("|", "\\|")
        sectors = ", ".join(item.sector_tags)
        rows.append(
            f"| {classify_priority(item)} | {item.score} | {item.category} | {sectors} | {item.source_name} | {title} | {date_str} | {item.url} |"
        )
    path.write_text("\n".join(rows), encoding="utf-8")
    return path


def to_csv(items: list[Item], output_path: str | Path, sector: str | None = None) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    selected = sort_items(_filter_items(items, sector))
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "priority", "score", "category", "sector_tags", "source_name", "title", "published", "url", "matched_keywords", "tags"
        ])
        for item in selected:
            writer.writerow([
                classify_priority(item),
                item.score,
                item.category,
                "; ".join(item.sector_tags),
                item.source_name,
                item.title,
                item.published.isoformat() if item.published else "",
                item.url,
                "; ".join(item.matched_keywords),
                "; ".join(item.tags),
            ])
    return path


def to_html(items: list[Item], output_path: str | Path, sector: str | None = None) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    selected = sort_items(_filter_items(items, sector))

    total = len(selected)
    high = sum(1 for item in selected if classify_priority(item) == "HIGH")
    medium = sum(1 for item in selected if classify_priority(item) == "MEDIUM")
    low = sum(1 for item in selected if classify_priority(item) == "LOW")
    generated = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")

    rows = []
    for item in selected:
        date_str = item.published.date().isoformat() if item.published else ""
        sectors = ", ".join(item.sector_tags) if item.sector_tags else "-"
        keywords = ", ".join(item.matched_keywords) if item.matched_keywords else "-"
        rows.append(
            "<tr>"
            f"<td>{html.escape(classify_priority(item))}</td>"
            f"<td>{item.score}</td>"
            f"<td>{html.escape(item.category)}</td>"
            f"<td>{html.escape(sectors)}</td>"
            f"<td>{html.escape(item.source_name)}</td>"
            f"<td><a href=\"{html.escape(item.url)}\" target=\"_blank\" rel=\"noopener noreferrer\">{html.escape(item.title)}</a></td>"
            f"<td>{html.escape(date_str)}</td>"
            f"<td>{html.escape(keywords)}</td>"
            "</tr>"
        )

    sector_title = f" — secteur {html.escape(sector)}" if sector else ""
    html_doc = f"""<!doctype html>
<html lang=\"fr\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Veille PQC{sector_title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; color: #111827; background: #f9fafb; }}
    h1 {{ margin-bottom: 0.25rem; }}
    .muted {{ color: #6b7280; margin-bottom: 1rem; }}
    .cards {{ display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0 1.5rem; }}
    .card {{ background: white; border-radius: 12px; padding: 1rem 1.25rem; box-shadow: 0 1px 6px rgba(0,0,0,0.08); min-width: 180px; }}
    .card .label {{ color: #6b7280; font-size: 0.9rem; }}
    .card .value {{ font-size: 1.8rem; font-weight: bold; margin-top: 0.25rem; }}
    table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 1px 6px rgba(0,0,0,0.08); border-radius: 12px; overflow: hidden; }}
    th, td {{ padding: 0.8rem; text-align: left; border-bottom: 1px solid #e5e7eb; vertical-align: top; }}
    th {{ background: #111827; color: white; position: sticky; top: 0; }}
    tr:hover {{ background: #f3f4f6; }}
    a {{ color: #2563eb; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <h1>Veille PQC{sector_title}</h1>
  <div class=\"muted\">Généré le {generated}</div>
  <div class=\"cards\">
    <div class=\"card\"><div class=\"label\">Total</div><div class=\"value\">{total}</div></div>
    <div class=\"card\"><div class=\"label\">HIGH</div><div class=\"value\">{high}</div></div>
    <div class=\"card\"><div class=\"label\">MEDIUM</div><div class=\"value\">{medium}</div></div>
    <div class=\"card\"><div class=\"label\">LOW</div><div class=\"value\">{low}</div></div>
  </div>
  <table>
    <thead>
      <tr>
        <th>Priorité</th>
        <th>Score</th>
        <th>Catégorie</th>
        <th>Secteurs</th>
        <th>Source</th>
        <th>Titre</th>
        <th>Date</th>
        <th>Mots-clés</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body>
</html>
"""
    path.write_text(html_doc, encoding="utf-8")
    return path
