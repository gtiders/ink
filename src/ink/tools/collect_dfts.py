from pathlib import Path

import typer
from ase.io import read 
from ase.io.extxyz import write_extxyz


def collect_dfts(
    paths: list[Path] = typer.Argument(
        ...,
        help="Files or directories to scan for DFT results.",
    ),
):
    """Collect DFT results from arbitrary files using ASE writer to dftsets.xyz.

    接受若干路径参数（文件），适合作为 Typer 命令行入口：

    ink tools collect_dfts PATH1 PATH2 ...

    收集所有文件中的原子结构，写入 dftsets.xyz
    """

    results = []

    for f in paths:
        if not f.is_file():
            continue
        try:
            atoms = read(f, index=":")
        except Exception:
            # Skip files that ASE cannot read
            continue
        results.extend(atoms)
    write_extxyz("dftsets.xyz", results)

