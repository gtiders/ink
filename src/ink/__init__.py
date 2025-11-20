import typer

from .dotfiles import run_dotbot as _run_dotbot


app = typer.Typer(help="Ink CLI")


@app.command()
def dotbot() -> None:
    code = _run_dotbot()
    raise typer.Exit(code)


@app.command()
def hello(name: str = "world") -> None:
    """Print a friendly greeting."""
    typer.echo(f"Hello, {name}!")

