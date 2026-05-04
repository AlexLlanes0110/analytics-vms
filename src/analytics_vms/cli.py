"""Command line interface for Analytics VMS."""

from pathlib import Path
from typing import Optional

import typer

from analytics_vms import __version__
from analytics_vms.inventory import InventoryValidationError, load_inventory_csv

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


if __name__ == "__main__":
    app()
