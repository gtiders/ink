import typer
from .settings import write_settings

app=typer.Typer(help="ink.amset command-line interface")

settings=app.command(name="settings")(write_settings)