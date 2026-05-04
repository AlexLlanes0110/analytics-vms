"""CLI smoke tests."""

from pathlib import Path

from typer.testing import CliRunner

from analytics_vms.cli import app

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Analytics VMS" in result.output


def test_cli_without_args_shows_help() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "analytics-vms 0.1.0" in result.output


def test_cli_check_inventory_with_dummy_csv() -> None:
    result = runner.invoke(
        app,
        ["check-inventory", str(REPO_ROOT / "examples" / "vms_input_dummy_repo.csv")],
    )

    assert result.exit_code == 0
    assert "Inventario valido: 181 filas." in result.output


def test_cli_check_inventory_fails_with_invalid_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "invalid_inventory.csv"
    csv_path.write_text(
        "project_code,municipality,site_type\n"
        "DEMO01,Sample Municipality,PMI\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["check-inventory", str(csv_path)])

    assert result.exit_code == 1
    assert "Inventario invalido" in result.output
    assert "Faltan columnas obligatorias" in result.output
