import os
import math
import typer
import subprocess
import shutil
from pathlib import Path
from typing import Optional
from ruamel.yaml import YAML
from pymatgen.core.structure import Structure
from pymatgen.io.vasp.inputs import Kpoints,Incar
import inspect
from functools import wraps


yaml = YAML(typ="rt")


class Job:
    def __init__(self):
        # Load configuration from vasp_config.yaml
        # 1) module directory
        # 2) current working directory (overrides previous keys)
        base_config_path = Path(__file__).parent / "vasp_config.yaml"
        cwd_config_path = Path.cwd() / "vasp_config.yaml"

        config: dict = {}

        if base_config_path.is_file():
            with base_config_path.open("r", encoding="utf-8") as f:
                data = yaml.load(f) or {}
                if isinstance(data, dict):
                    config.update(data)

        if cwd_config_path.is_file():
            with cwd_config_path.open("r", encoding="utf-8") as f:
                data = yaml.load(f) or {}
                if isinstance(data, dict):
                    config.update(data)

        # merged config
        self.config = config

        # Resolve working directory: use config['global']['work_dir'] if present,
        # otherwise default to the current working directory.
        work_dir_cfg = self.config.get("global").get("work_dir")
        if work_dir_cfg is None:
            self.work_dir = Path.cwd()
        else:
            self.work_dir = Path(work_dir_cfg)

        self.work_dir.mkdir(exist_ok=True)
        os.chdir(self.work_dir)

        self._write_merged_config_to_cwd()

    def _write_merged_config_to_cwd(self) -> None:
        """Overwrite vasp_config.yaml in the current directory with merged cfg."""
        cfg_path = Path.cwd() / "vasp_config.yaml"
        with cfg_path.open("w", encoding="utf-8") as f:
            yaml.dump(self.config, f)

    def _calculate_grid_dimensions(self, bnorm, kpr: float):
        """Calculate K-mesh using VASPKIT-like KPR formula.

        For each direction i, the number of k-points is

            N_i = max(1, ceil(|b_i| / kpr))

        where |b_i| are the norms of the reciprocal lattice vectors and
        ``kpr`` is the user-defined KPT-resolved value.
        """

        b1, b2, b3 = bnorm
        nkpx = max(1, math.floor(b1 / kpr/2/math.pi))
        nkpy = max(1, math.floor(b2 / kpr/2/math.pi))
        nkpz = max(1, math.floor(b3 / kpr/2/math.pi))

        return nkpx, nkpy, nkpz

    def submit(self, cwd: Path):
        """Submit the job.
        
        If a qsub.pid file exists in the directory, read the PID and cancel the old job
        before submitting a new one. The new job ID is then saved to qsub.pid.
        """
        pid_file = cwd / "qsub.pid"

        # 1. Check and cancel existing job
        if pid_file.is_file():
            old_pid = pid_file.read_text().strip()
            if old_pid:
                print(f"Found existing job ID {old_pid} in {pid_file}. Cancelling...")
                try:
                    subprocess.run(["qdel", old_pid], check=False)
                except Exception as e:
                    print(f"Failed to cancel job {old_pid}: {e}")
        
        # 2. Submit new job and capture stdout
        result = subprocess.run(
            ["qsub", "jobscript.sh"], 
            check=True, 
            cwd=cwd, 
            stdout=subprocess.PIPE, 
            text=True
        )
        
        # 3. Extract job ID (assuming qsub prints the job ID to stdout)
        # Output format varies by scheduler (Torque, PBS, Slurm wrapper), 
        # but usually it's "12345.server" or just "12345".
        # We save the whole stripped output for now.
        new_pid = result.stdout.strip()
        if new_pid:
            pid_file.write_text(new_pid)
            print(f"Submitted job {new_pid}. PID saved to {pid_file}.")
    
    def _write_poscar(self, poscar, cwd: Path):
        """
        Write POSCAR file from a file path or a structure.
        """

        target = cwd / "POSCAR"

        # Case 1: existing POSCAR-like file path
        if isinstance(poscar, (Path,str)):
            poscar=Path(poscar)
            poscar=Structure.from_file(poscar)
            poscar.to_file(target)
            return

        raise TypeError(
            "poscar must be a path-like object that can be parsed by pymatgen"
        )

    def _write_incar(self, incar, cwd: Path):
        """Write INCAR file from a file path or a dict.

        - If ``incar`` is a Path or string, copy its contents to ``cwd/INCAR``.
        - If ``incar`` is a dict, write key-value pairs into ``cwd/INCAR``.
        """

        target = cwd / "INCAR"

        # Case 1: existing INCAR-like file path
        if isinstance(incar, (Path,str)):
            incar=Incar.from_file(incar)
            incar.write_file(target)
            return

        # Case 2: INCAR content as dict
        if isinstance(incar, dict):
            incar=Incar.from_dict(incar)
            incar.write_file(target)
            return

        raise TypeError("incar must be a path-like object or a dict of INCAR settings")


    def _write_potcar(self, potcar, cwd: Path):
        """
        Write POTCAR file from a file path or a potcar object.
        """

        target = cwd / "POTCAR"

        # Case 1: existing POTCAR-like file path
        if isinstance(potcar, (Path, str)):
            potcar=Path(potcar)
            potcar=potcar.read_text()
            target.write_text(potcar)
            return

        raise TypeError(
            "potcar must be a path-like object or a string"
        )

    def _write_kpoints(self, kpoints, cwd: Path,poscar=None):
        """
        Write KPOINTS file from a file path or a kpoints object.
        """

        target = cwd / "KPOINTS"

        # Case 1: KPOINTS line mode
        if kpoints == "line":
            from pymatgen.symmetry.kpath import KPathSeek
            if poscar is None:
                raise ValueError("poscar is required to generate line-mode KPOINTS")

            structure = Structure.from_file(poscar)
            kpath = KPathSeek(structure,symprec=1e-5)

            # line_density 控制每段路径的点数密度
            kpts, labels = kpath.get_kpoints(line_density=30, coords_are_cartesian=True)

            kp = Kpoints(comment="High-symmetry line path from Seek-path")
            kp.kpts = kpts
            kp.kpts_labels = labels
            kp.style = Kpoints.supported_modes.Line_mode

            kp.write_file(target)
            return


        # Case 2: Gamma-centered automatic mesh based on reciprocal-space size.
        # ``kpoints`` is treated as the KPR value (float/int) used in
        # N_i = max(1, ceil(|b_i| / kpr)), similar to VASPKIT's definition.
        if isinstance(kpoints, (float, int)):
            if poscar is None:
                raise ValueError("poscar is required to generate gamma-mode KPOINTS")
            structure = Structure.from_file(poscar)

            # Use norms of the reciprocal lattice vectors |b_i|
            bnorm = structure.lattice.reciprocal_lattice.abc
            grid = self._calculate_grid_dimensions(bnorm, float(kpoints))
            kp = Kpoints.gamma_automatic(grid)
            kp.write_file(target)
            return

        # Case 3: existing KPOINTS-like file path
        if isinstance(kpoints, (Path, str)):
            kpoints=Path(kpoints)
            kpoints=Kpoints.from_file(kpoints)
            kpoints.write_file(target)
            return



        
    
    def _write_jobscript(self, jobscript, cwd: Path):
        """
        Write jobscript file from a file path or a string.
        """

        target = cwd / "jobscript.sh"

        # Case 1: existing jobscript-like file path
        if isinstance(jobscript, Path):
            jobscript=Path(jobscript)
            jobscript=jobscript.read_text()
            target.write_text(jobscript)
            return

        # Case 2: jobscript content as string
        if isinstance(jobscript, str):
            target.write_text(jobscript)
            return

        raise TypeError(
            "jobscript must be a path-like object or a string"
        )   

    def _resolve_path(self, arg: Optional[Path], section: str, key: str):
        """Resolve a value from CLI or config.

        Priority: explicit argument > config[section][key].

        For keys like 'poscar' and 'jobscript' the config values are
        path-like strings. For 'incar' it can be a dict, and for
        'kpoints' it can be a float or the string 'line'. We therefore
        return the raw config value without wrapping it in Path.
        """

        if arg is not None:
            return arg

        section_cfg = self.config.get(section) or {}
        cfg_val = section_cfg.get(key)
        if cfg_val is None:
            raise ValueError(
                f"Missing required value: '{key}'. "
                "Provide it as an argument or in vasp_config.yaml."
            )
        return cfg_val

    def _handle_cp(self, job_type: str, cwd: Path):
        """Handle file/directory copying defined in config['cp'].
        
        Format in yaml:
          cp:
            source_path: target_path
            
        source_path is resolved relative to self.work_dir (if not absolute).
        target_path is resolved relative to cwd (if not absolute).
        """
        section_cfg = self.config.get(job_type) or {}
        cp_cfg = section_cfg.get("cp")
        
        if not cp_cfg or not isinstance(cp_cfg, dict):
            return

        for src, dst in cp_cfg.items():
            # Resolve source path
            src_path = Path(src)
            if not src_path.is_absolute():
                src_path = self.work_dir / src_path
                
            # Resolve destination path
            dst_path = cwd / dst
            
            if not src_path.exists():
                print(f"Warning: Source path '{src_path}' does not exist. Skipping copy.")
                continue
                
            if src_path.is_dir():
                # Copy directory
                if dst_path.exists():
                     # Remove existing destination directory to avoid FileExistsError
                     # or merge strategies (here we overwrite/replace)
                     shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
                print(f"Copied directory {src_path} -> {dst_path}")
            else:
                # Copy file
                # Ensure parent directory exists
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                print(f"Copied file {src_path} -> {dst_path}")

    def relax(
        self,
        poscar: Optional[Path] = typer.Option(
            None,
            "--poscar",
            help="Path to POSCAR file (falls back to vasp_config.yaml if omitted)",
        ),
        incar: Optional[Path] = typer.Option(
            None,
            "--incar",
            help="Path to INCAR file (falls back to vasp_config.yaml if omitted)",
        ),
        potcar: Optional[Path] = typer.Option(
            None,
            "--potcar",
            help="Path to POTCAR file (falls back to vasp_config.yaml if omitted)",
        ),
        kpoints: Optional[str] = typer.Option(
            None,
            "--kpoints",
            help="KPOINTS specification: path, 'line', or density value as string",
        ),
        jobscript: Optional[Path] = typer.Option(
            None,
            "--jobscript",
            help="Path to jobscript file (falls back to vasp_config.yaml if omitted)",
        ),
        yes: bool = typer.Option(
            False,
            "--yes",
            "-y",
            help="Submit without interactive confirmation",
        ),
    ) -> None:
        """Relaxation job helper using Job.relax with config fallbacks."""

        cwd=self.work_dir / "relax"
        cwd.mkdir(exist_ok=True)

        self._handle_cp("relax", cwd)

        # Resolve all paths
        poscar_path = self._resolve_path(poscar, "relax", "poscar")
        self._write_poscar(poscar_path, cwd)
        incar_path = self._resolve_path(incar, "relax", "incar")
        self._write_incar(incar_path, cwd)
        potcar_path = self._resolve_path(potcar, "relax", "potcar")
        self._write_potcar(potcar_path, cwd)
        kpoints_path = self._resolve_path(kpoints, "relax", "kpoints")
        self._write_kpoints(kpoints_path, cwd,poscar=poscar_path)
        jobscript_path = self._resolve_path(jobscript, "relax", "jobscript")
        self._write_jobscript(jobscript_path, cwd)
        
        # Handle file copies
        self._handle_cp("relax", cwd)

        if yes:
            self.submit(cwd)
        else:
            typer.confirm("Submit job?", abort=True)
            self.submit(cwd)


    def static(
        self,
        poscar: Optional[Path] = typer.Option(
            None,
            "--poscar",
            help="Path to POSCAR file (falls back to vasp_config.yaml if omitted)",
        ),
        incar: Optional[Path] = typer.Option(
            None,
            "--incar",
            help="Path to INCAR file (falls back to vasp_config.yaml if omitted)",
        ),
        potcar: Optional[Path] = typer.Option(
            None,
            "--potcar",
            help="Path to POTCAR file (falls back to vasp_config.yaml if omitted)",
        ),
        kpoints: Optional[str] = typer.Option(
            None,
            "--kpoints",
            help="KPOINTS specification: path, 'line', or density value as string",
        ),
        jobscript: Optional[Path] = typer.Option(
            None,
            "--jobscript",
            help="Path to jobscript file (falls back to vasp_config.yaml if omitted)",
        ),
        yes: bool = typer.Option(
            False,
            "--yes",
            "-y",
            help="Submit without interactive confirmation",
        ),
    ) -> None:
        """Static calculation job helper using Job.static with config fallbacks."""

        cwd=self.work_dir / "static"
        cwd.mkdir(exist_ok=True)

        self._handle_cp("static", cwd)

        # Resolve all paths
        poscar_path = self._resolve_path(poscar, "static", "poscar")
        self._write_poscar(poscar_path, cwd)
        incar_path = self._resolve_path(incar, "static", "incar")
        self._write_incar(incar_path, cwd)
        potcar_path = self._resolve_path(potcar, "static", "potcar")
        self._write_potcar(potcar_path, cwd)
        kpoints_path = self._resolve_path(kpoints, "static", "kpoints")
        self._write_kpoints(kpoints_path, cwd,poscar=poscar_path)
        jobscript_path = self._resolve_path(jobscript, "static", "jobscript")
        self._write_jobscript(jobscript_path, cwd)
        
        # Handle file copies
        self._handle_cp("static", cwd)

        if yes:
            self.submit(cwd)
        else:
            typer.confirm("Submit job?", abort=True)
            self.submit(cwd)
    def dos(
        self,
        poscar: Optional[Path] = typer.Option(
            None,
            "--poscar",
            help="Path to POSCAR file (falls back to vasp_config.yaml if omitted)",
        ),
        incar: Optional[Path] = typer.Option(
            None,
            "--incar",
            help="Path to INCAR file (falls back to vasp_config.yaml if omitted)",
        ),
        potcar: Optional[Path] = typer.Option(
            None,
            "--potcar",
            help="Path to POTCAR file (falls back to vasp_config.yaml if omitted)",
        ),
        kpoints: Optional[str] = typer.Option(
            None,
            "--kpoints",
            help="KPOINTS specification: path, 'line', or density value as string",
        ),
        jobscript: Optional[Path] = typer.Option(
            None,
            "--jobscript",
            help="Path to jobscript file (falls back to vasp_config.yaml if omitted)",
        ),
        yes: bool = typer.Option(
            False,
            "--yes",
            "-y",
            help="Submit without interactive confirmation",
        ),
    ) -> None:
        """DOS calculation job helper using Job.dos with config fallbacks."""

        cwd=self.work_dir / "dos"
        cwd.mkdir(exist_ok=True)

        # Resolve all paths
        poscar_path = self._resolve_path(poscar, "dos", "poscar")
        self._write_poscar(poscar_path, cwd)
        incar_path = self._resolve_path(incar, "dos", "incar")
        self._write_incar(incar_path, cwd)
        potcar_path = self._resolve_path(potcar, "dos", "potcar")
        self._write_potcar(potcar_path, cwd)
        kpoints_path = self._resolve_path(kpoints, "dos", "kpoints")
        self._write_kpoints(kpoints_path, cwd,poscar=poscar_path)
        jobscript_path = self._resolve_path(jobscript, "dos", "jobscript")
        self._write_jobscript(jobscript_path, cwd)
        
        # Handle file copies
        self._handle_cp("dos", cwd)

        if yes:
            self.submit(cwd)
        else:
            typer.confirm("Submit job?", abort=True)
            self.submit(cwd)
            
    def band(self,
        poscar: Optional[Path] = typer.Option(
            None,
            "--poscar",
            help="Path to POSCAR file (falls back to vasp_config.yaml if omitted)",
        ),
        incar: Optional[Path] = typer.Option(
            None,
            "--incar",
            help="Path to INCAR file (falls back to vasp_config.yaml if omitted)",
        ),
        potcar: Optional[Path] = typer.Option(
            None,
            "--potcar",
            help="Path to POTCAR file (falls back to vasp_config.yaml if omitted)",
        ),
        kpoints: Optional[str] = typer.Option(
            None,
            "--kpoints",
            help="KPOINTS specification: path, 'line', or density value as string",
        ),
        jobscript: Optional[Path] = typer.Option(
            None,
            "--jobscript",
            help="Path to jobscript file (falls back to vasp_config.yaml if omitted)",
        ),
        yes: bool = typer.Option(
            False,
            "--yes",
            "-y",
            help="Submit without interactive confirmation",
        ),
    ) -> None:
        """Band structure calculation job helper using Job.band with config fallbacks."""

        cwd=self.work_dir / "band"
        cwd.mkdir(exist_ok=True)

        # Resolve all paths
        poscar_path = self._resolve_path(poscar, "band", "poscar")
        self._write_poscar(poscar_path, cwd)
        incar_path = self._resolve_path(incar, "band", "incar")
        self._write_incar(incar_path, cwd)
        potcar_path = self._resolve_path(potcar, "band", "potcar")
        self._write_potcar(potcar_path, cwd)
        kpoints_path = self._resolve_path(kpoints, "band", "kpoints")
        self._write_kpoints(kpoints_path, cwd,poscar=poscar_path)
        jobscript_path = self._resolve_path(jobscript, "band", "jobscript")
        self._write_jobscript(jobscript_path, cwd)
        
        # Handle file copies
        self._handle_cp("band", cwd)

        if yes:
            self.submit(cwd)
        else:
            typer.confirm("Submit job?", abort=True)
            self.submit(cwd)


# --- 实例化并提供外部接口

def create_lazy_command(cls, method_name):
    """
    Create a command wrapper that instantiates the class lazily.
    This prevents the class from initializing (and reading config) at module import time.
    """
    method = getattr(cls, method_name)
    
    @wraps(method)
    def wrapper(*args, **kwargs):
        # Instantiate the class only when the command is called
        instance = cls()
        # Call the bound method on the instance
        return getattr(instance, method_name)(*args, **kwargs)
    
    # Update the wrapper signature to remove 'self' so Typer parses arguments correctly
    sig = inspect.signature(method)
    params = [p for p in sig.parameters.values() if p.name != "self"]
    wrapper.__signature__ = sig.replace(parameters=params)
    
    return wrapper

app = typer.Typer(help="vasp jobs command-line interface")

app.command(name="relax")(create_lazy_command(Job, "relax"))
app.command(name="static")(create_lazy_command(Job, "static"))
app.command(name="dos")(create_lazy_command(Job, "dos"))

