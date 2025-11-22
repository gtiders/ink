import typer

from .dotfiles import run_dotbot as _run_dotbot
from .tools import app as tools_app
from .ShengBTE import app as shengbte_app

from .vasp.jobs import app as vaspjobs_app

app = typer.Typer(help="Ink CLI")


@app.command()
def dotbot() -> None:
    code = _run_dotbot()
    raise typer.Exit(code)


@app.command()
def hello(name: str = "world") -> None:
    """Print a friendly greeting."""
    typer.echo(f"Hello, {name}!")

# Register ShengBTE subcommand group: `ink shengbte ...`
app.add_typer(shengbte_app, name="shengbte")

# Register tools subcommand group: `ink tools ...`
app.add_typer(tools_app, name="tools")

app.add_typer(vaspjobs_app,name="vaspjobs")

