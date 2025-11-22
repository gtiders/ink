import numpy as np
from pathlib import Path
import typer
import yaml
from pymatgen.io.vasp.outputs import Outcar, Vasprun



AMSET_SETTINGS = {
    # general settings
    "doping": [
        -1.0e18,
        -1.5e18,
        -2.0e18,
        -2.5e18,
        -3.0e18,
        -3.5e18,
        -4.0e18,
        -4.5e18,
        -5.0e18,
        -5.5e18,
        -6.0e18,
        -6.5e18,
        -7.0e18,
        -7.5e18,
        -8.0e18,
        -8.5e18,
        -9.0e18,
        -1.0e19,
        -1.05e19,
        -1.1e19,
        -1.15e19,
        -1.2e19,
        -1.25e19,
        -1.3e19,
        -1.35e19,
        -1.4e19,
        -1.45e19,
        -1.5e19,
        -1.75e19,
        -2.0e19,
        -2.5e19,
        -3.0e19,
        -3.5e19,
        -4.0e19,
        -4.5e19,
        -5.0e19,
        -5.5e19,
        -6.0e19,
        -6.5e19,
        -7.0e19,
        -7.5e19,
        -8.0e19,
        -8.5e19,
        -9.0e19,
        -1.0e20,
        -1.5e20,
        -2.0e20,
        -2.5e20,
        -3.0e20,
        -3.5e20,
        -4.0e20,
        -4.5e20,
        -5.0e20,
        -5.5e20,
        -6.0e20,
        -6.5e20,
        -7.0e20,
        -7.5e20,
        -8.0e20,
        -8.5e20,
        -9.0e20,
        -1.0e21,
        -1.5e21,
        -2.0e21,
        -2.5e21,
        -3.0e21,
        -3.5e21,
        -4.0e21,
        -4.5e21,
        -5.0e21,
        -5.5e21,
        -6.0e21,
        -6.5e21,
        -7.0e21,
        -7.5e21,
        -8.0e21,
        -8.5e21,
        -9.0e21,
        -1.0e22,
        1.0e18,
        1.5e18,
        2.0e18,
        2.5e18,
        3.0e18,
        3.5e18,
        4.0e18,
        4.5e18,
        5.0e18,
        5.5e18,
        6.0e18,
        6.5e18,
        7.0e18,
        7.5e18,
        8.0e18,
        8.5e18,
        9.0e18,
        1.0e19,
        1.05e19,
        1.1e19,
        1.15e19,
        1.2e19,
        1.25e19,
        1.3e19,
        1.35e19,
        1.4e19,
        1.45e19,
        1.5e19,
        1.75e19,
        2.0e19,
        2.5e19,
        3.0e19,
        3.5e19,
        4.0e19,
        4.5e19,
        5.0e19,
        5.5e19,
        6.0e19,
        6.5e19,
        7.0e19,
        7.5e19,
        8.0e19,
        8.5e19,
        9.0e19,
        1.0e20,
        1.5e20,
        2.0e20,
        2.5e20,
        3.0e20,
        3.5e20,
        4.0e20,
        4.5e20,
        5.0e20,
        5.5e20,
        6.0e20,
        6.5e20,
        7.0e20,
        7.5e20,
        8.0e20,
        8.5e20,
        9.0e20,
        1.0e21,
        1.5e21,
        2.0e21,
        2.5e21,
        3.0e21,
        3.5e21,
        4.0e21,
        4.5e21,
        5.0e21,
        5.5e21,
        6.0e21,
        6.5e21,
        7.0e21,
        7.5e21,
        8.0e21,
        8.5e21,
        9.0e21,
        1.0e22,
    ],
    "temperatures": 300,
    "scattering_type": "auto",
    "use_projections": False,

    # electronic_structure settings
    "interpolation_factor": 30,

    # material settings
    "wavefunction_coefficients": "wavefunction.hdf5",
    "deformation_potential": "deform.hdf5",

    # performance settings
    "symprec": 1e-5,
    "nworkers": -1,
    "cache_wavefunction": True,

    # Output settings
    "file_format": "json",
    "write_input": True,
    "write_mesh": True,
}


def write_settings(
    wavefunction_hdf5: Path,
    deform_hdf5: Path,
    dfpt_vasprun: Path,
    elastic_outcar: Path,
    pop_frequency: float,
) -> None:
    """Write AMSET_SETTINGS to a YAML file.

    Parameters
    ----------
    wavefunction_hdf5 : Path
        Path to the AMSET wavefunction HDF5 file.
    deform_hdf5 : Path
        Path to the AMSET deformation potential HDF5 file.
    dfpt_vasprun : Path
        Path to the DFPT `vasprun.xml` file containing dielectric tensors.
    elastic_outcar : Path
        Path to the DFPT `OUTCAR` file containing elastic constants.
    pop_frequency : float
        Polar optical phonon frequency (in THz or the units expected by AMSET).

    All parameters must be provided in this order when calling the function.
    """
    high_frequency_dielectric = np.array(Vasprun(dfpt_vasprun).epsilon_static)
    static_dielectric = np.array(Vasprun(dfpt_vasprun).epsilon_ionic) + np.array(
        Vasprun(dfpt_vasprun).epsilon_static
    )
    elastic_outcar = Outcar(elastic_outcar)
    elastic_outcar.read_elastic_tensor()
    elastic_constant = elastic_outcar.data["elastic_tensor"]

    AMSET_SETTINGS["wavefunction_coefficients"] = wavefunction_hdf5.absolute().as_posix()
    AMSET_SETTINGS["deformation_potential"] = deform_hdf5.absolute().as_posix()
    AMSET_SETTINGS["high_frequency_dielectric"] = high_frequency_dielectric.tolist()
    AMSET_SETTINGS["static_dielectric"] = static_dielectric.tolist()
    AMSET_SETTINGS["elastic_constant"] = elastic_constant
    AMSET_SETTINGS["pop_frequency"] = pop_frequency

    with open("settings.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(AMSET_SETTINGS, f, sort_keys=False)
