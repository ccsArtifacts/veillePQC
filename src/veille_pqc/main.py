from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil

import typer
from rapidfuzz import fuzz

from veille_pqc.classification import classify_category, classify_sectors
from veille_pqc.collectors import rss as rss_collector
from veille_pqc.collectors import webpage as webpage_collector
from veille_pqc.config_loader import load_config
from veille_pqc.models import Item
from veille_pqc.notifiers.emailer import send_email_with_attachment
from veille_pqc.reporting import to_csv, to_html, to_markdown
from veille_pqc.scoring import score_item
from veille_pqc.storage import open_db, upsert_items

app = typer.Typer(add_completion=False, no_args_is_help=True)


def deduplicate(items: list[Item], threshold: int = 92) -> list[Item]:
    unique: list[Item] = []
    for item in items:
        is_duplicate = False
        for existing in unique:
            same_link = item.url.rstrip("/") == existing.url.rstrip("/")
            close_title = fuzz.ratio(item.title.lower(), existing.title.lower()) >= threshold
            if same_link or close_title:
                is_duplicate = True
                if item.score > existing.score:
                    existing.score = item.score
                    existing.matched_keywords = sorted(set(existing.matched_keywords + item.matched_keywords))
                    existing.sector_tags = sorted(set(existing.sector_tags + item.sector_tags))
                    if existing.category == "other" and item.category != "other":
                        existing.category = item.category
                break
        if not is_duplicate:
            unique.append(item)
    return unique


def _collect_items(config_path: str) -> tuple[list[Item], object]:
    cfg = load_config(config_path)
    collected: list[Item] = []
    for source in cfg.sources:
        if source.type == "rss":
            items = rss_collector.collect(source)
        elif source.type == "webpage":
            items = webpage_collector.collect(source)
        else:
            raise ValueError(f"Type de source non supporté: {source.type}")

        for item in items:
            item = score_item(item, cfg.keywords)
            item = classify_category(item, cfg.categories)
            item = classify_sectors(item, cfg.sectors)
            collected.append(item)
    return deduplicate(collected), cfg


@app.command()
def run(
    config: str = typer.Option("config/sources.yaml", help="Chemin du fichier YAML de configuration"),
    db: str = typer.Option("data/veille_pqc.db", help="Base SQLite locale"),
    md_out: str = typer.Option("reports/veille_pqc.md", help="Rapport Markdown"),
    csv_out: str = typer.Option("reports/veille_pqc.csv", help="Export CSV"),
    sector: str | None = typer.Option(None, help="Filtre de secteur: banque, santé, industrie, cloud"),
) -> None:
    deduped, cfg = _collect_items(config)

    conn = open_db(db)
    inserted = upsert_items(conn, deduped)
    conn.close()

    md_path = to_markdown(deduped, md_out, sector=sector)
    csv_path = to_csv(deduped, csv_out, sector=sector)

    typer.echo(f"Sources inspectées : {len(cfg.sources)}")
    typer.echo(f"Éléments uniques    : {len(deduped)}")
    typer.echo(f"Nouveaux éléments   : {inserted}")
    typer.echo(f"Rapport Markdown    : {md_path}")
    typer.echo(f"Rapport CSV         : {csv_path}")


@app.command()
def export_html(
    config: str = typer.Option("config/sources.yaml"),
    db: str = typer.Option("data/veille_pqc.db"),
    html_out: str = typer.Option("site/index.html"),
    csv_out: str = typer.Option("site/veille_pqc.csv"),
    md_out: str = typer.Option("site/veille_pqc.md"),
    sector: str | None = typer.Option(None, help="Filtre de secteur"),
) -> None:
    deduped, _ = _collect_items(config)
    conn = open_db(db)
    upsert_items(conn, deduped)
    conn.close()

    html_path = to_html(deduped, html_out, sector=sector)
    generated_csv = to_csv(deduped, csv_out, sector=sector)
    generated_md = to_markdown(deduped, md_out, sector=sector)

    typer.echo(f"Rapport HTML        : {html_path}")
    typer.echo(f"Rapport CSV         : {generated_csv}")
    typer.echo(f"Rapport Markdown    : {generated_md}")


@app.command()
def send_mail(
    to_email: str = typer.Option(..., "--to", help="Adresse e-mail destinataire"),
    config: str = typer.Option("config/sources.yaml"),
    db: str = typer.Option("data/veille_pqc.db"),
    md_out: str = typer.Option("reports/veille_pqc.md"),
    csv_out: str = typer.Option("reports/veille_pqc.csv"),
    sector: str | None = typer.Option(None, help="Filtre de secteur"),
) -> None:
    deduped, _ = _collect_items(config)
    conn = open_db(db)
    upsert_items(conn, deduped)
    conn.close()

    md_path = to_markdown(deduped, md_out, sector=sector)
    to_csv(deduped, csv_out, sector=sector)

    subject = f"Veille PQC — {datetime.now().strftime('%Y-%m-%d')}"
    body = "Bonjour,\n\nVeuillez trouver en pièce jointe le rapport de veille PQC du jour.\n"
    send_email_with_attachment(subject=subject, body=body, to_email=to_email, attachment_path=str(md_path))
    typer.echo(f"E-mail envoyé à {to_email}")


@app.command()
def publish_bundle(
    config: str = typer.Option("config/sources.yaml"),
    db: str = typer.Option("data/veille_pqc.db"),
    bundle_dir: str = typer.Option("dist_bundle"),
    sector: str | None = typer.Option(None, help="Filtre de secteur"),
) -> None:
    bundle = Path(bundle_dir)
    bundle.mkdir(parents=True, exist_ok=True)
    deduped, _ = _collect_items(config)
    conn = open_db(db)
    upsert_items(conn, deduped)
    conn.close()

    html_path = to_html(deduped, bundle / "index.html", sector=sector)
    md_path = to_markdown(deduped, bundle / "veille_pqc.md", sector=sector)
    csv_path = to_csv(deduped, bundle / "veille_pqc.csv", sector=sector)
    db_target = bundle / "veille_pqc.db"
    shutil.copyfile(db, db_target)

    typer.echo(f"Bundle HTML         : {html_path}")
    typer.echo(f"Bundle Markdown     : {md_path}")
    typer.echo(f"Bundle CSV          : {csv_path}")
    typer.echo(f"Bundle SQLite       : {db_target}")


if __name__ == "__main__":
    app()
