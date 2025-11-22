import typer
import f90nml
from pathlib import Path
from typing import Optional
from pymatgen.core.structure import Structure

def write_control(
    poscar: Path = typer.Argument(..., help="Path to POSCAR file."),
    sx: int = typer.Argument(..., help="Supercell size in x (scell(1))."),
    sy: int = typer.Argument(..., help="Supercell size in y (scell(2))."),
    sz: int = typer.Argument(..., help="Supercell size in z (scell(3))."),
    is_born: bool = typer.Option(
        False,
        "--is-born",
        help="Enable Born effective charges (requires OUTCAR)",
    ),
    outcar: Optional[Path] = typer.Option(
        None,
        "--outcar",
        help="Path to OUTCAR file (required if --is-born)",
    ),
    output: Path = typer.Option(
        Path("CONTROL"),
        "-o",
        "--output",
        help="Output CONTROL file path (default: CONTROL)",
    ),
):
    """Generate a ShengBTE CONTROL file from a POSCAR and supercell size."""

    if not poscar.is_file():
        raise FileNotFoundError(f"POSCAR not found: {poscar}")

    if is_born:
        if outcar is None:
            raise ValueError("OUTCAR file must be provided when is_born is enabled.")
        if not outcar.is_file():
            raise FileNotFoundError(f"OUTCAR not found: {outcar}")
        from pymatgen.io.vasp.outputs import Outcar
        born = Outcar(outcar).born
        epsilon = Outcar(outcar).dielectric_tensor

    structure = Structure.from_file(poscar)
    scell = (sx, sy, sz)

    nml = f90nml.Namelist()

    # --- &allocations ---
    species = [str(sp) for sp in structure.composition.elements]
    nelements = len(species)
    natoms = len(structure)

    nml["allocations"] = {
        "nelements": nelements,
        "natoms": natoms,
        "ngrid": [15, 15, 15],
    }

    # --- &crystal ---
    # Lattice vectors: 3x3 matrix
    latt = structure.lattice.matrix  # [[a1,a2,a3], [b1,b2,b3], [c1,c2,c3]]

    # Positions as list of [x, y, z] fractional coordinates
    positions = [list(site.frac_coords) for site in structure.sites]

    # Type indices: map element symbol to 1..nelements
    elem_to_type = {el: i + 1 for i, el in enumerate(species)}
    types = [elem_to_type[str(site.specie)] for site in structure.sites]

    nml["crystal"] = {
        "lfactor": 0.1,
        "lattvec": [list(row) for row in latt],
        "elements": species,
        "types": types,
        "positions": positions,
        "born": born,
        "epsilon": epsilon,
        "scell": list(scell),
    }

    # --- &parameters --- (fixed from template)
    nml["parameters"] = {
        "T_min": 300,
        "T_max": 900,
        "T_step": 100,
        "scalebroad": 0.5,
    }

    # --- &flags --- (fixed from template)
    nml["flags"] = {
        "convergence": True,
    }

    with output.open("w") as f:
        nml.write(f)
