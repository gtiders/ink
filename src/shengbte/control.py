"""Custom Control class for ShengBTE CONTROL file generation.

This is a lightweight replacement for pymatgen.io.shengbte.Control
focused on the fields we currently use in ink.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from pymatgen.core import Structure
from pymatgen.io.vasp import Kpoints

try:  # optional dependency, mirrors pymatgen.io.shengbte behaviour
    import f90nml  # type: ignore[import]
except ImportError:  # pragma: no cover - env without f90nml
    f90nml = None


@dataclass
class Control:
    """Minimal ShengBTE CONTROL representation.

    This class stores the parameters we care about and can write
    a ShengBTE-compatible CONTROL file without relying on f90nml.
    """

    # Required / commonly used fields
    nelements: int
    natoms: int
    ngrid: Sequence[int]
    lattvec: Sequence[Sequence[float]]
    types: Sequence[int]
    elements: Sequence[str]
    positions: Sequence[Sequence[float]]
    scell: Sequence[int]

    # Optional crystal parameters
    lfactor: float = 0.1
    masses: Optional[Sequence[float]] = None
    gfactors: Optional[Sequence[float]] = None
    epsilon: Optional[Sequence[Sequence[float]]] = None
    born: Optional[Any] = None

    # Parameters section
    t: Optional[float] = None
    t_min: Optional[float] = None
    t_max: Optional[float] = None
    t_step: Optional[float] = None
    omega_max: Optional[float] = None
    scalebroad: Optional[float] = None

    # Flags section
    nonanalytic: Optional[bool] = None
    convergence: Optional[bool] = None
    isotopes: Optional[bool] = None
    autoisotopes: Optional[bool] = None
    nanowires: Optional[bool] = None
    onlyharmonic: Optional[bool] = None
    espresso: Optional[bool] = None

    # Extra generic storage if needed
    extra: Dict[str, Any] = field(default_factory=dict)

    # These key lists mirror pymatgen.io.shengbte.Control so that when
    # f90nml is available we can write a CONTROL file in the same layout.
    allocations_keys = ("nelements", "natoms", "ngrid", "norientations")
    crystal_keys = (
        "lfactor",
        "lattvec",
        "types",
        "elements",
        "positions",
        "masses",
        "gfactors",
        "epsilon",
        "born",
        "scell",
        "orientations",
    )
    params_keys = (
        "t",
        "t_min",
        "t_max",
        "t_step",
        "omega_max",
        "scalebroad",
        "rmin",
        "rmax",
        "dr",
        "maxiter",
        "nticks",
        "eps",
    )
    flags_keys = (
        "nonanalytic",
        "convergence",
        "isotopes",
        "autoisotopes",
        "nanowires",
        "onlyharmonic",
        "espresso",
    )

    # --- constructors -----------------------------------------------------------------

    @classmethod
    def from_structure(
        cls,
        structure: Structure,
        reciprocal_density: Optional[int] = 50000,
        scell: Sequence[int] | None = None,
        temperature: float | Mapping[str, float] | None = 300,
        **kwargs: Any,
    ) -> "Control":
        """Build a Control object from a Structure.

        This mirrors the idea of pymatgen's Control.from_structure, but keeps
        the data in plain Python types (lists, bools, floats) so that writing
        a CONTROL file is robust.
        """

        if scell is None:
            scell = [3, 3, 3]

        elements = [str(el) for el in structure.elements]

        unique_nums = sorted(set(structure.atomic_numbers))
        type_map = {z: i + 1 for i, z in enumerate(unique_nums)}
        types = [type_map[z] for z in structure.atomic_numbers]

        # k-point grid
        if reciprocal_density:
            kpoints = Kpoints.automatic_density(structure, reciprocal_density)
            # make sure we convert tuples to plain lists
            ngrid = list(kpoints.kpts[0])
        else:
            ngrid = [1, 1, 1]

        control_kwargs: Dict[str, Any] = dict(
            nelements=structure.n_elems,
            natoms=len(structure),
            ngrid=ngrid,
            lattvec=[list(row) for row in structure.lattice.matrix],
            types=types,
            elements=elements,
            positions=[list(coords) for coords in structure.frac_coords],
            scell=list(scell),
        )

        # Temperature handling: single value or dict with min/max/step
        if isinstance(temperature, (int, float)):
            control_kwargs["t"] = float(temperature)
        elif isinstance(temperature, Mapping):
            if "min" in temperature:
                control_kwargs["t_min"] = float(temperature["min"])
            if "max" in temperature:
                control_kwargs["t_max"] = float(temperature["max"])
            if "step" in temperature:
                control_kwargs["t_step"] = float(temperature["step"])

        # Merge extra keyword arguments directly into fields / extra
        for key, value in kwargs.items():
            if hasattr(cls, key):
                control_kwargs[key] = value
            else:
                # Store unknown keys in extra
                control_kwargs.setdefault("extra", {})[key] = value

        return cls(**control_kwargs)  # type: ignore[arg-type]

    # --- serialization ----------------------------------------------------------------

    def to_file(self, filename: str | Path = "CONTROL") -> None:
        """Write a ShengBTE CONTROL file.

        If ``f90nml`` is available, we use it in the same way as
        ``pymatgen.io.shengbte.Control``. Otherwise we raise a clear error
        explaining that f90nml is required for writing CONTROL files.
        """

        if f90nml is None:
            raise RuntimeError(
                "ShengBTE Control writing requires f90nml to be installed. "
                "Please install it via 'pip install f90nml'."
            )

        path = Path(filename)

        # Build dictionaries for each namelist, mimicking pymatgen's layout.
        all_dict: Dict[str, Any] = dict(self.__dict__)

        def _get_subdict(keys: Iterable[str]) -> Dict[str, Any]:
            return {
                k: all_dict[k]
                for k in keys
                if k in all_dict and all_dict[k] is not None
            }

        alloc_dict = _get_subdict(self.allocations_keys)
        # ensure norientations key exists for allocations
        alloc_dict.setdefault("norientations", 0)
        alloc_nml = f90nml.Namelist({"allocations": alloc_dict})
        control_str = str(alloc_nml) + "\n"

        crystal_dict = _get_subdict(self.crystal_keys)
        crystal_nml = f90nml.Namelist({"crystal": crystal_dict})
        control_str += str(crystal_nml) + "\n"

        params_dict = _get_subdict(self.params_keys)
        if params_dict:
            params_nml = f90nml.Namelist({"parameters": params_dict})
            control_str += str(params_nml) + "\n"

        flags_dict = _get_subdict(self.flags_keys)
        if flags_dict:
            flags_nml = f90nml.Namelist({"flags": flags_dict})
            control_str += str(flags_nml) + "\n"

        with path.open(mode="w", encoding="utf-8") as fh:
            fh.write(control_str)

    # --- helpers ----------------------------------------------------------------------

    @staticmethod
    def _fmt_int(name: str, value: int) -> str:
        return f"    {name} = {int(value)}"

    @staticmethod
    def _fmt_int_list(name: str, values: Iterable[int]) -> str:
        vals = ", ".join(str(int(v)) for v in values)
        return f"    {name} = {vals}"

    @staticmethod
    def _fmt_float(name: str, value: float) -> str:
        return f"    {name} = {float(value)}"

    @staticmethod
    def _fmt_float_vec(name: str, values: Iterable[float]) -> str:
        vals = ", ".join(f"{float(v):.15g}" for v in values)
        return f"    {name} = {vals}"

    @staticmethod
    def _fmt_str_list(name: str, values: Iterable[str]) -> str:
        vals = ", ".join(repr(str(v)) for v in values)
        return f"    {name} = {vals}"

    @staticmethod
    def _fmt_bool(name: str, value: bool) -> str:
        flag = ".true." if value else ".false."
        return f"    {name} = {flag}"
