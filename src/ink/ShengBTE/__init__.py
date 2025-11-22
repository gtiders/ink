import typer
from .control import write_control

app=typer.Typer(help="ink.ShengBTE command-line interface")

control=app.command(name="control")(write_control)