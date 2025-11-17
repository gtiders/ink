import os
import stat
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import typer
import yaml


app = typer.Typer()


class AbortTasks(Exception):
    """Raised when the user chooses to abort remaining tasks."""


def _load_config(config_path: str) -> dict:
    config_file = Path(config_path)
    if not config_file.is_file():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    with config_file.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _check_vaspkit(global_cfg: dict) -> str:
    vaspkit_cmd = str(global_cfg.get("vaspkit", "vaspkit"))
    exe = shutil.which(vaspkit_cmd)
    if exe is None:
        raise RuntimeError(
            f"vaspkit executable '{vaspkit_cmd}' not found in PATH. "
            "Please ensure it is installed and available."
        )
    return vaspkit_cmd


def _prepare_poscar(task_name: str, work_dir: Path, poscar_spec: str) -> None:
    task_dir = work_dir / task_name
    task_dir.mkdir(parents=True, exist_ok=True)

    src = work_dir / poscar_spec
    if not src.is_file():
        raise FileNotFoundError(
            f"POSCAR source '{poscar_spec}' for task '{task_name}' does not exist at {src}"
        )

    dst = task_dir / "POSCAR"
    shutil.copyfile(src, dst)


def _prepare_chgcar(task_name: str, work_dir: Path, chgcar_spec: str) -> None:
    task_dir = work_dir / task_name
    task_dir.mkdir(parents=True, exist_ok=True)

    src = work_dir / chgcar_spec
    if not src.is_file():
        raise FileNotFoundError(
            f"CHGCAR source '{chgcar_spec}' for task '{task_name}' does not exist at {src}"
        )

    dst = task_dir / "CHGCAR"
    shutil.copyfile(src, dst)


def _run_command_in_task(task_name: str, work_dir: Path, raw_cmd: str, vaspkit_cmd: str) -> None:
    if not raw_cmd:
        return

    cmd = raw_cmd.strip()
    if cmd.startswith("vaspkit"):
        cmd = cmd.replace("vaspkit", vaspkit_cmd, 1)

    task_dir = work_dir / task_name
    task_dir.mkdir(parents=True, exist_ok=True)

    typer.echo(f"[task {task_name}] running: {cmd}")
    subprocess.run(cmd, shell=True, cwd=str(task_dir), check=True)


def _write_incar(task_name: str, work_dir: Path, incar_cfg: dict) -> None:
    if not incar_cfg:
        return

    task_dir = work_dir / task_name
    task_dir.mkdir(parents=True, exist_ok=True)

    incar_path = task_dir / "INCAR"
    lines: List[str] = []
    for key, value in incar_cfg.items():
        lines.append(f"{key} = {value}\n")

    with incar_path.open("w", encoding="utf-8") as f:
        f.writelines(lines)


def _write_jobscript(task_name: str, work_dir: Path, script_content: str) -> Path:
    if not script_content:
        return work_dir / task_name / "jobscript.sh"

    task_dir = work_dir / task_name
    task_dir.mkdir(parents=True, exist_ok=True)

    script_path = task_dir / "jobscript.sh"
    with script_path.open("w", encoding="utf-8") as f:
        f.write(script_content)

    mode = script_path.stat().st_mode
    script_path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return script_path


def _submit_job(task_name: str, script_path: Path, auto_yes: bool) -> None:
    if not script_path.is_file():
        msg = (
            typer.style("[task ", fg=typer.colors.RED)
            + typer.style(task_name, fg=typer.colors.GREEN)
            + typer.style(
                f"] jobscript not found at {script_path}, skip qsub.",
                fg=typer.colors.RED,
            )
        )
        typer.echo(msg)
        return

    if not auto_yes:
        prompt = (
            typer.style("[task ", fg=typer.colors.RED)
            + typer.style(task_name, fg=typer.colors.GREEN)
            + typer.style(
                f"] Submit job with qsub {script_path.name}?", fg=typer.colors.RED
            )
        )
        do_submit = typer.confirm(prompt)
        if not do_submit:
            typer.echo(f"[task {task_name}] submission skipped by user. Aborting remaining tasks.")
            raise AbortTasks()

    typer.secho("[task ", nl=False, fg=typer.colors.RED)
    typer.secho(task_name, nl=False, fg=typer.colors.GREEN)
    typer.secho(f"] submitting job: qsub {script_path.name}", fg=typer.colors.RED)
    subprocess.run("qsub " + script_path.name, shell=True, cwd=str(script_path.parent), check=True)


def _process_task(
    task_name: str,
    config: dict,
    work_dir: Path,
    vaspkit_cmd: str,
    auto_yes: bool,
) -> None:
    task_cfg = config.get(task_name)
    if not isinstance(task_cfg, dict):
        typer.echo(f"[task {task_name}] config not found or invalid, skip.")
        return

    typer.echo(f"\nProcessing task: {task_name}")

    poscar_spec = task_cfg.get("poscar")
    if poscar_spec:
        _prepare_poscar(task_name, work_dir, str(poscar_spec))

    chgcar_spec = task_cfg.get("chgcar")
    if chgcar_spec:
        _prepare_chgcar(task_name, work_dir, str(chgcar_spec))

    potcar_cmd = task_cfg.get("potcar")
    if potcar_cmd:
        _run_command_in_task(task_name, work_dir, str(potcar_cmd), vaspkit_cmd)

    kpoints_cmd = task_cfg.get("kpoints")
    if kpoints_cmd:
        _run_command_in_task(task_name, work_dir, str(kpoints_cmd), vaspkit_cmd)

    incar_cfg = task_cfg.get("incar")
    if isinstance(incar_cfg, dict):
        _write_incar(task_name, work_dir, incar_cfg)

    jobscript_content = task_cfg.get("jobscript")
    script_path = _write_jobscript(task_name, work_dir, jobscript_content or "")

    _submit_job(task_name, script_path, auto_yes)


@app.command()
def main(
    tasks: Optional[List[str]] = typer.Argument(
        None,
        help="Tasks to run (e.g. relax1 relax2 static). If omitted, run all tasks in YAML order.",
    ),
    config_path: str = typer.Option(
        "vasp_config.yaml",
        "--config",
        "-c",
        help="Path to YAML config file.",
    ),
    yes: bool = typer.Option(
        False,
        "-y",
        "--yes",
        help="Submit jobs without confirmation.",
    ),
    from_label: bool = typer.Option(
        False,
        "-l",
        "--from-label",
        help=(
            "When tasks are provided, start from the first specified task in YAML order "
            "and continue to the end. For example, 'main static -l' starts from 'static' "
            "instead of only running 'static'."
        ),
    ),
) -> None:
    config = _load_config(config_path)

    global_cfg = config.get("global") or {}
    work_dir_str = global_cfg.get("work_dir", "./")
    work_dir = Path(work_dir_str).expanduser().resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Changing working directory to: {work_dir}")
    os.chdir(work_dir)

    vaspkit_cmd = _check_vaspkit(global_cfg)
    typer.echo(f"Using vaspkit executable: {vaspkit_cmd}")

    yaml_order = [k for k in config.keys() if k not in {"global", "ending"}]

    if tasks:
        if from_label:
            first = tasks[0]
            if first not in yaml_order:
                typer.echo(f"First specified task '{first}' not found in config, nothing to do.")
                return
            start_idx = yaml_order.index(first)
            task_order = yaml_order[start_idx:]
        else:
            task_order = tasks
    else:
        task_order = yaml_order

    try:
        for task_name in task_order:
            _process_task(task_name, config, work_dir, vaspkit_cmd, yes)
    except AbortTasks:
        typer.echo("Aborted remaining tasks by user request.")

    typer.echo("\nAll requested tasks processed.")


if __name__ == "__main__":
    app()

