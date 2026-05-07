"""Command line interface for Analytics VMS."""

from __future__ import annotations

import csv
import re
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from io import StringIO
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote, unquote

import typer

from analytics_vms import __version__
from analytics_vms.batch_check import check_camera_batch
from analytics_vms.inventory import InventoryValidationError, load_inventory_csv
from analytics_vms.reports import (
    DETAILED_FIELDNAMES,
    SUMMARY_BY_SITE_FIELDNAMES,
    SUMMARY_FIELDNAMES,
    build_detailed_rows,
    build_report_payload,
    build_summary_by_site_rows,
    build_summary_rows,
    write_csv_report,
    write_json_report,
)

app = typer.Typer(
    add_completion=False,
    help="Analytics VMS CLI para validacion batch de camaras.",
    invoke_without_command=True,
    no_args_is_help=False,
)


def _version_callback(value: bool) -> None:
    """Print the package version and exit."""
    if value:
        typer.echo(f"analytics-vms {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Muestra la version instalada.",
    ),
) -> None:
    """Show CLI help/version without running validation logic."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def version() -> None:
    """Print the installed package version."""
    typer.echo(f"analytics-vms {__version__}")


@app.command()
def check_inventory(
    path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Ruta al CSV de inventario a validar.",
    ),
) -> None:
    """Validate an inventory CSV without running camera checks."""
    try:
        rows = load_inventory_csv(path)
    except InventoryValidationError as exc:
        typer.secho("Inventario invalido:", fg=typer.colors.RED, err=True)
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Inventario valido: {len(rows)} filas.")


@app.command()
def check_cameras(
    inventory_csv: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Ruta al CSV de inventario a validar y ejecutar.",
    ),
    out_dir: Path = typer.Option(
        ...,
        "--out-dir",
        file_okay=False,
        dir_okay=True,
        help="Directorio donde se escriben los reportes.",
    ),
    probe_timeout_seconds: float = typer.Option(
        5,
        "--probe-timeout-seconds",
        help="Timeout de ffprobe por camara.",
    ),
    frame_timeout_seconds: float = typer.Option(
        10,
        "--frame-timeout-seconds",
        help="Timeout de ffmpeg para validar frames por camara.",
    ),
    min_frames: int = typer.Option(
        1,
        "--min-frames",
        help="Frames minimos requeridos para declarar frames_ok=1.",
    ),
    visual_diagnostics: bool = typer.Option(
        True,
        "--visual-diagnostics/--no-visual-diagnostics",
        help="Habilita o deshabilita diagnosticos visuales.",
    ),
    visual_timeout_seconds: float = typer.Option(
        10,
        "--visual-timeout-seconds",
        help="Timeout por detector visual.",
    ),
    visual_sample_seconds: float = typer.Option(
        5,
        "--visual-sample-seconds",
        help="Duracion de muestra para diagnosticos visuales.",
    ),
    print_details: bool = typer.Option(
        False,
        "--print-details",
        help="Imprime filas detalladas sanitizadas en terminal.",
    ),
) -> None:
    """Run camera checks from an inventory CSV and write operator reports."""
    try:
        inventory_rows = load_inventory_csv(inventory_csv)
    except InventoryValidationError as exc:
        typer.secho("Inventario invalido:", fg=typer.colors.RED, err=True)
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    source_rows = [_row_to_mapping(row) for row in inventory_rows]

    try:
        batch_result = check_camera_batch(
            source_rows,
            probe_timeout_seconds=probe_timeout_seconds,
            frame_timeout_seconds=frame_timeout_seconds,
            min_frames=min_frames,
            enable_visual_diagnostics=visual_diagnostics,
            visual_timeout_seconds=visual_timeout_seconds,
            visual_sample_seconds=visual_sample_seconds,
        )

        out_dir.mkdir(parents=True, exist_ok=True)
        report_paths = {
            "detailed.csv": out_dir / "detailed.csv",
            "summary.csv": out_dir / "summary.csv",
            "summary_by_site.csv": out_dir / "summary_by_site.csv",
            "report.json": out_dir / "report.json",
        }

        detailed_rows = build_detailed_rows(batch_result, source_rows=source_rows)
        write_csv_report(
            report_paths["detailed.csv"],
            detailed_rows,
            fieldnames=DETAILED_FIELDNAMES,
        )
        write_csv_report(
            report_paths["summary.csv"],
            build_summary_rows(batch_result),
            fieldnames=SUMMARY_FIELDNAMES,
        )
        write_csv_report(
            report_paths["summary_by_site.csv"],
            build_summary_by_site_rows(batch_result, source_rows=source_rows),
            fieldnames=SUMMARY_BY_SITE_FIELDNAMES,
        )
        write_json_report(
            report_paths["report.json"],
            build_report_payload(batch_result, source_rows=source_rows),
        )
    except Exception as exc:
        typer.secho("Error fatal del CLI:", fg=typer.colors.RED, err=True)
        typer.echo(_sanitize_cli_error(str(exc), source_rows=source_rows), err=True)
        raise typer.Exit(code=1) from exc

    _print_operational_summary(batch_result.summary, report_paths)
    if print_details:
        _print_detail_rows(detailed_rows)


def _row_to_mapping(row: Any) -> dict[str, Any]:
    if isinstance(row, Mapping):
        return dict(row)
    if is_dataclass(row) and not isinstance(row, type):
        return asdict(row)
    return {
        key: getattr(row, key)
        for key in dir(row)
        if not key.startswith("_") and not callable(getattr(row, key))
    }


def _print_operational_summary(summary: Any, report_paths: Mapping[str, Path]) -> None:
    typer.echo("Resumen operativo:")
    typer.echo(f"total: {summary.total}")
    typer.echo(f"ok: {summary.ok}")
    typer.echo(f"no_frames: {summary.no_frames}")
    typer.echo(f"probe_failed: {summary.probe_failed}")
    typer.echo(f"error: {summary.error}")
    typer.echo(f"black_detected: {summary.black_detected}")
    typer.echo(f"freeze_detected: {summary.freeze_detected}")
    typer.echo("Archivos generados:")
    for filename, path in report_paths.items():
        typer.echo(f"{filename}: {path}")


def _print_detail_rows(rows: list[dict[str, Any]]) -> None:
    typer.echo("Detalles:")
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=DETAILED_FIELDNAMES,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    typer.echo(output.getvalue().rstrip("\n"))


def _sanitize_cli_error(message: str, *, source_rows: list[dict[str, Any]]) -> str:
    text = re.sub(r"rtsp://[^\s'\"<>]+", "[rtsp_url_redacted]", message)
    for secret in _source_secret_tokens(source_rows):
        text = text.replace(secret, "***")
    return text


def _source_secret_tokens(source_rows: list[dict[str, Any]]) -> set[str]:
    tokens: set[str] = set()
    for row in source_rows:
        for key in ("credential_id", "username", "password"):
            value = row.get(key)
            if value is None:
                continue

            text = str(value)
            tokens.update({text, quote(text, safe=""), unquote(text)})

    return {token for token in tokens if token}


if __name__ == "__main__":
    app()
