import typer

from . import __version__

app = typer.Typer(
    help="Deterministic configuration management for home automation devices"
)


@app.command()
def version() -> None:
    """Display the application version."""
    typer.echo(__version__)


if __name__ == "__main__":
    app()
    