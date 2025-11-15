# Ink - VASP Calculation Toolkit

A comprehensive command-line toolkit for setting up and managing VASP calculations with integration for ShengBTE and AMSET.

## Features

### VASP Calculations
- **Static calculations**: Setup single-point energy calculations
- **Structure relaxation**: Configure ionic and/or volume relaxation
- **Batch calculations**: Manage multiple VASP calculations efficiently

### POTCAR Generation
- Generate POTCAR files using pymatgen
- Support for multiple functionals (PBE, LDA, PBE_52, PBE_54)
- Automatic element detection from POSCAR

### Third-party Integration
- **ShengBTE**: Thermal transport property calculations
- **AMSET**: Electronic transport property calculations

## Installation

```bash
# Install from source
pip install -e .

# Or using uv
uv pip install -e .
```

## Usage

### VASP Commands

```bash
# Setup static calculation
ink vasp static --workdir /path/to/calc

# Setup structure relaxation
ink vasp relax --workdir /path/to/calc --relax-type full

# Setup batch calculations
ink vasp batch --workdir /path/to/batch

# Generate POTCAR from POSCAR
ink vasp potcar POSCAR --functional PBE --output-dir ./
```

### ShengBTE

```bash
# Setup ShengBTE calculation from POSCAR
ink shengbte setup POSCAR --workdir /path/to/calc --scell "3,3,3" --temperature 300

# Setup with temperature range
ink shengbte setup POSCAR --t-min 100 --t-max 800 --t-step 50

# Run complete workflow (coming soon)
ink shengbte run --workdir /path/to/calc
```

### AMSET

```bash
# Setup AMSET calculation
ink amset setup --workdir /path/to/calc

# Run complete workflow
ink amset run --workdir /path/to/calc
```

## Project Structure

```
src/
├── main.py          # CLI entry point
├── vasp/            # VASP calculation modules
│   ├── static.py    # Static calculations
│   ├── relax.py     # Structure relaxation
│   ├── batch.py     # Batch calculations
│   └── potcar/      # POTCAR generation
│       └── generator.py # Pymatgen-based POTCAR generator
├── shengbte/        # ShengBTE integration
│   ├── setup.py     # ShengBTE setup
│   └── workflow.py  # Complete workflow management
├── amset/           # AMSET integration
│   ├── setup.py     # AMSET setup
│   └── workflow.py  # Complete workflow management
└── utils/           # Shared utilities
    ├── io.py        # I/O operations
    └── validators.py # Input validation
```

## Requirements

- Python >= 3.12
- pymatgen >= 2025.10.7
- ase >= 3.26.0
- typer >= 0.20.0
- And more (see pyproject.toml)

## License

TBD

## Contributing

TBD
