"""Ink - VASP calculation toolkit CLI"""

import typer
from pathlib import Path
from typing import Optional

# ShengBTE subcommands - imported from shengbte.setup
from .shengbte.setup import setup_shengbte

app = typer.Typer(
    name="ink",
    help="VASP calculation toolkit for computational materials science"
)

@app.command()
def version():
    """Show version information"""
    from . import __version__
    typer.echo(f"ink version {__version__}")

app.command(name="setup_shengbte")(
    setup_shengbte
)

