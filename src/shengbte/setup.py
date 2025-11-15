"""ShengBTE calculation setup.

This module provides a CLI entry point that reads a POSCAR/vasp file,
builds a custom ``Control`` object for ShengBTE using our own
``shengbte.control.Control`` implementation, and writes a CONTROL file.
"""

import typer
from pathlib import Path
from typing import Optional, Dict

from .control import Control


def setup_shengbte(
    poscar: Path = typer.Argument(..., help="Path to POSCAR file", exists=True),
    workdir: Optional[Path] = typer.Option(None, help="Working directory"),
    scell: str = typer.Option("3,3,3", help="Supercell size (e.g., '3,3,3')"),
    temperature: float = typer.Option(300.0, help="Temperature in K"),
    t_min: Optional[float] = typer.Option(None, help="Minimum temperature for range"),
    t_max: Optional[float] = typer.Option(None, help="Maximum temperature for range"),
    t_step: Optional[float] = typer.Option(None, help="Temperature step for range"),
    reciprocal_density: int = typer.Option(50000, help="Reciprocal space density"),
    omega_max: Optional[float] = typer.Option(None, help="Maximum phonon frequency (THz)"),
    scalebroad: Optional[float] = typer.Option(None, help="Broadening scale factor"),
    # Add more optional parameters as needed
):
    """Setup ShengBTE calculation from POSCAR file.

    This uses our own ``Control`` implementation (see ``shengbte.control``)
    instead of ``pymatgen.io.shengbte.Control`` so that we keep everything in
    plain Python types (lists, floats, bools) and avoid Fortran tuple issues.
    """
    from pymatgen.io.vasp import Poscar, Kpoints
    
    try:
        # Parse supercell
        scell_list = [int(x.strip()) for x in scell.split(",")]
        if len(scell_list) != 3:
            typer.echo("Error: scell must be 3 integers separated by commas (e.g., '3,3,3')", err=True)
            raise typer.Exit(1)
        
        # Setup temperature
        if t_min is not None and t_max is not None and t_step is not None:
            temp_dict = {"min": t_min, "max": t_max, "step": t_step}
        else:
            temp_dict = temperature
        
        # Setup working directory
        work_path = Path(workdir) if workdir else Path.cwd()
        work_path.mkdir(parents=True, exist_ok=True)
        
        typer.echo(f"Setting up ShengBTE calculation in: {work_path}")
        
        # Read structure from POSCAR
        poscar_obj = Poscar.from_file(str(poscar))
        structure = poscar_obj.structure
        
        # Collect additional parameters passed to Control
        extra_params = {}
        if omega_max is not None:
            extra_params["omega_max"] = omega_max
        if scalebroad is not None:
            extra_params["scalebroad"] = scalebroad

        control = Control.from_structure(
            structure=structure,
            reciprocal_density=reciprocal_density,
            temperature=temp_dict,
            scell=scell_list,
            **extra_params,
        )
        
        # Write CONTROL file
        control_path = work_path / "CONTROL"
        control.to_file(str(control_path))
        
        typer.echo("ShengBTE setup complete!")
        typer.echo(f"  - CONTROL file: {control_path}")
        typer.echo(f"  - Supercell: {scell_list}")
        typer.echo(f"  - Temperature: {temp_dict}")
        typer.echo("\u2713 ShengBTE setup completed successfully!")
        
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    typer.run(setup_shengbte)