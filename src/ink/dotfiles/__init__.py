import os
import subprocess
from pathlib import Path
from typing import Sequence


def run_dotbot(args: Sequence[str] | None = None) -> int:
    """Run dotbot using the current Python interpreter.

    This builds a dotbot command like:

        python -m dotbot -d <base_dir> -c <config_file> [<extra args>]

    where:

    - ``base_dir`` is the directory containing this module (``dotfiles``).
    - ``config_file`` is chosen based on the current OS:
      - Windows: ``dotbot_config/windows.yaml``
      - Other systems: ``dotbot_config/unix.yaml``

    Parameters
    ----------
    args:
        Extra command-line arguments to pass to dotbot, appended after -d/-c.

    Returns
    -------
    int
        The process return code from dotbot.
    """

    if args is None:
        args = []

    base_dir = Path(__file__).resolve().parent
    config_dir = base_dir / "dotbot_config"

    if os.name == "nt":
        config_file = config_dir / "windows.yaml"
    else:
        config_file = config_dir / "unix.yaml"

    # Call the installed `dotbot` CLI directly. The `dotbot` package does not
    # provide a `__main__`, so `python -m dotbot` fails; however, installing
    # from PyPI creates a `dotbot` command in the environment (as you can see
    # from `uv run` listing available commands).
    cmd = [
        "dotbot",
        "-d",
        str(base_dir),
        "-c",
        str(config_file),
        *args,
    ]
    completed = subprocess.run(cmd)
    return completed.returncode
