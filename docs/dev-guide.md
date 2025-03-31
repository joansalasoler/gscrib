# Development Guide

Welcome to the development guide for **Gscrib**. This guide will
walk you through the process of setting up your development environment
and extend the project with new features.

---

## Introduction

TODO

## Getting Started

### Prerequisites

Before you start, make sure you have the following installed on your
machine:

- **Python** (3.10 or newer)
- **Pip** (Python package manager)
- **Git** (Version control tool)

If you need help installing any of these, check out their official
installation guides:

- [Python](https://www.python.org/downloads/)
- [Pip](https://pip.pypa.io/en/stable/installation/)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

### Setting Up the Development Environment

Follow these steps to set up your development environment:

**Clone the repository:**

```bash
git clone https://github.com/joansalasoler/gscrib.git
cd gscrib
```

**Create and activate a virtual environment:**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

**Install dependencies:**

```bash
pip install --upgrade pip  # Upgrade pip
pip install -e .  # Install in development mode
pip install -r requirements.txt  # Install additional dependencies
pip install -r requirements.dev.txt  # Install development dependencies
```

## Project Structure

Here's a brief overview of the `Gscrib` project structure:

```bash
gscrib/
├── gscrib/               # Main package directory
│   ├── __init__.py       # Package initialization
│   └── ...               # Other module files
├── tests/                # Tests directory
└── docs/                 # Documentation builder
```

## Documentation and Testing

To build the documentation locally run the following commands. This will
generate the documentation in the `./docs/html` directory. Open `index.html`
in a web browser to view it.

```bash
cd docs
pip install -r requirements.txt
python -m sphinx . ./html
```

To run the test suite, use `pytest`. This will automatically discover
and run all the tests in the project. You can also run specific tests
by referring to the [pytest documentation](https://docs.pytest.org/en/stable/).

```bash
pytest
```

## Extending the Builder

### Adding G-code Commands

G-code commands define specific machine instructions within the system.
These commands are implemented using enums and mapped to their
corresponding G-code instructions. The `GCodeBuilder` class provides
high-level methods to generate and manage these commands.

The following steps outline how to add a new G-code command.

**Define the Command:**

1. Create a new enum for command inside `gscrib/enums/`.
2. Make sure the enum extends `BaseEnum`.

```python
from gscrib.enums import BaseEnum

class LengthUnits(BaseEnum):
    INCHES = 'in'
    MILLIMETERS = 'mm'
```

**Map the Command:**

1. Open `gscrib/codes/gcode_mappings.py`.
2. Add the enum values and their G-code instructions.

```python
gcode_table = GCodeTable((
    GCodeEntry(LengthUnits.INCHES,
        'G20', 'Set length units, inches'),

    GCodeEntry(LengthUnits.MILLIMETERS,
        'G21', 'Set length units, millimeters'),
))
```

**Implement the Command:**

1. Open `gscrib/gcode_builder.py`.
2. Modify `GCodeBuilder` to support the new command by adding a new method.
3. Use `self._get_statement()` to build the G-code statement.
4. Write the G-code statement using `self.write(statement)`.

```python
@typechecked
def set_units(self, length_units: LengthUnits | str) -> None:
    length_units = LengthUnits(length_units)
    statement = self._get_statement(length_units)
    self.write(statement)
```

By following these steps, you ensure that the new G-code command
integrates seamlessly with the existing system while maintaining
consistency and correctness.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. **Fork the repository** on GitHub.
2. **Create your feature branch**:

```bash
git checkout -b feature/your-new-feature
```

3. **Make your changes** and commit them:

```bash
git commit -m "Add a detailed description of your feature"
```

4. **Push your changes** to the branch:

```bash
git push origin feature/your-new-feature
```

5. **Open a Pull Request** on GitHub.

Please ensure your code follows a style consistent with the project's
own and includes tests for any new functionality.

## Getting Help

If you need help or have questions, feel free to:

* Check out the [documentation](https://gscrib.readthedocs.io/en/latest/).
* [Open an issue](https://github.com/joansalasoler/gscrib/issues) on GitHub.

Happy coding, and don't forget to have fun! We hope you enjoy working
with **gscrib** as much as we do. Feel free to contribute, experiment,
and bring your creative ideas to life!
