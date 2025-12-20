# Development Guide

Welcome to the development guide for **Gscrib**. This guide will walk you
through the process of setting up your development environment and extend
the project with new features. It is intended for developers who want to
dive into the codebase and understand its architecture.

---

## Introduction

**Gscrib** is a modular and extensible G-code generation library written
in Python. It provides a high-level API for generating, managing, and
outputting G-code commands for CNC machines, 3D printers, and other
automated hardware. Designed with clarity and flexibility in mind,
**Gscrib** makes it easy to build complex, validated G-code sequences
while offering full control over output formatting, path interpolation,
and machine state.

## Getting Started

### Prerequisites

Before you start, make sure you have the following installed on your
machine:

- **Python** (3.10 or newer)
- **Poetry** (Python dependency manager and packaging tool)
- **Git** (Version control tool)

If you need help installing any of these, check out their official
installation guides:

- [Python](https://www.python.org/downloads/)
- [Poetry](https://python-poetry.org/docs/#installation)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

### Setting Up the Development Environment

Follow these steps to set up your development environment:

**Clone the repository:**

```bash
git clone https://github.com/joansalasoler/gscrib.git
cd gscrib
```

**Create the virtual environment and install dependencies:**

```bash
poetry install --with dev,docs
eval $(poetry env activate)
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

To run the test suite, use `pytest`. This will automatically discover
and run all the tests in the project. You can also run specific tests
by referring to the [pytest documentation](https://docs.pytest.org/en/stable/).

```bash
poetry run pytest
```

To build the documentation locally run the following commands. This will
generate the documentation in the `./docs/html` directory. Open `index.html`
in a web browser to view it.

```bash
poetry run sphinx-build docs docs/_build/html
```

## Extending the Library

### Overview of Components

**Gscrib**'s architecture is designed for clarity, modularity, and ease of
extension. At its core, it revolves around two primary classes,
[GCodeCore](#GCodeCore) and [GCodeBuilder](#GCodeBuilder):

- [**GCodeCore**](#GCodeCore): The foundational engine for G-code generation.
  It handles basic movement commands, position tracking, coordinate
  transformations, and writing output to various destinations.
- [**GCodeBuilder**](#GCodeBuilder): The main API for structured and safe
  G-code generation. Built on top of [GCodeCore](#GCodeCore), it adds state tracking,
  safety checks, path interpolation, tool and temperature control, and
  custom move hooks. Recommended for most use cases.

In addition to these two core classes, **Gscrib** is composed of modular
components that extend its functionality:

- **Writers**: Handle how G-code is output —whether saved to a file, sent
  over a serial or network connection, or printed to the console.
- **Formatters**: Control the appearance of G-code lines, such as decimal
  precision, comment style, number formatting, or line endings.
- **State Manager**: Tracks the current machine state, including position,
  active tool, units, feed rates, and more. It enforces validation and
  consistency to help avoid unsafe operations.
- **Interpolator**: Break down complex high-level paths, like arcs or
  splines, into sequences of G-code moves that machines can follow.
- **Transformer**: Apply geometric operations such as translation, rotation,
  or scaling to coordinates before G-code is output.

Each component is modular and extensible, making it easy to customize or
replace functionality without altering the core system.

### Adding G-code Commands

G-code commands define specific machine instructions within the system.
These commands are implemented using enums and mapped to their corresponding
G-code instructions. The [GCodeBuilder](#GCodeBuilder) class provides
high-level methods to generate and manage these commands.

The following steps outline how to add a new G-code command.

**Define the Command:**

1. Create a new enum for the command inside `gscrib/enums/`.
2. Make sure the enum extends [`BaseEnum`](#BaseEnum).

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
2. Modify [`GCodeBuilder`](#GCodeBuilder) to support the new command by
   adding a new method.
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

### State Management

**Gscrib** uses a stateful approach to track the current context of G-code
generation. This includes key parameters such as the current units,
positioning, feed rate, and active tools. The [GState](#GState) class is
responsible for tracking and validating these values.

When adding new commands or features to the library, it's important to
consider whether they affect the state. If they do, the relevant properties
within [GState](#GState) should be updated. This ensures that the state
remains accurate, preventing potential errors during G-code generation.

Example:

```python
def set_units(self, length_units: LengthUnits) -> None:
    self.state._set_length_units(length_units)  # Update state
    statement = self._get_statement(length_units)
    self.write(statement)
```

### Custom Writers

Writers let the user control exactly where and how G-code is sent, whether
it's to a file, network, or any other destination. Multiple writers can
be register within the [GCodeCore](#GCodeCore) instance.

To implement a custom writer:

1. Create a new class that inherits from [`BaseWriter`](#BaseWriter).
2. Implement the required `write()` method.
3. Register the writer in the builder instance.

Example:

```python
class ConsoleWriter(BaseWriter):
    def write(self, statement: bytes) -> None:
        print(statement)

g.add_writer(ConsoleWriter())  # Register the writer
```

### Custom Formatters

Formatters control the presentation of G-code statements, including the
formatting of numbers, comments, and commands. **Gscrib** provides a
[DefaultFormatter](#DefaultFormatter) that should meet most common use
cases. However, custom formatters can be easily created to cater to
specific requirements.

To create a custom formatter:

1. Create a class that inherits from [`BaseFormatter`](#BaseFormatter).
2. Implement the required methods, such as `command()` or `number()`.
3. Register the formatter in the builder instance.

Example:

```python
class CustomFormatter(BaseFormatter):
    def number(self, number: Number) -> str:
        return f"{number:.3f}"  # Limit to 3 decimal places

    # ... other methods

g.set_formatter(CustomFormatter())  # Register the formatter
```

### Path Interpolation

The [PathTracer](#PathTracer) class helps generate motion paths by
approximating curves with straight lines. The smoothness of the curve can
be controlled by invoking [set_resolution()](#GCodeBuilder.set_resolution())
on the G-code builder instance. This determines how many segments will
be used. Lower resolution gives smoother curves but increases the number
of generated G-code lines.

Two main methods are provided to make it easier to extend
[PathTracer](#PathTracer):

- The [parametric()](#PathTracer.parametric) method is the core of how
  the [PathTracer](#PathTracer) interpolates curves. It uses a **parametric**
  approach to define curves, meaning the curve is described by a simple
  mathematical function that takes a parameter `theta` ranging from 0 at
  the start to 1 at the end of the curve. The function then calculates the
  position (X, Y, Z) at any point along the curve and traces the sampled
  segments with `G1` commands.

- The [estimate_length()](#PathTracer.estimate_length) method quickly estimates
  the length of a curve by sampling points along the curve and adding up
  the distances between them. It's fast and good enough for rough estimates,
  but if precision is required, it's better to calculate the exact length.

Many of the path methods in the [PathTracer](#PathTracer) rely on the
[parametric()](#PathTracer.parametric) method to approximate complex curves.
On the other hand, [estimate_length()](#PathTracer.estimate_length) should
only be used when computing the exact length of the curve is difficult or
computationally expensive.

Example:

```python
import numpy as np

def circle(self, radius: float, **kwargs) -> None:
    def circle_function(thetas: np.ndarray) -> np.ndarray:
        x = radius * np.cos(2 * np.pi * thetas)
        y = radius * np.sin(2 * np.pi * thetas)
        z = np.zeros(thetas.shape)
        return np.column_stack((x, y, z))

    total_length = 2 * np.pi * radius  # Circumference of the circle
    self.parametric(circle_function, total_length, **kwargs)
```

### Coordinate Transformations

The [CoordinateTransformer](#CoordinateTransformer) class provides a
flexible and powerful way to apply 3D transformations to coordinates
using **4x4 matrices**. By following a simple pattern of defining a
transformation matrix and chaining it with
[chain_transform()](#CoordinateTransformer.chain_transform()), new
transformations can easily be added to the class.

The class also supports saving and restoring transformation states using
the [save_state()](#CoordinateTransformer.save_state()) and
[restore_state()](#CoordinateTransformer.restore_state()) methods. This
is useful for temporarily modifying the transformation and then reverting
to the previous state. By default, the states are stored on a stack.

When generating G-code commands, [GCodeCore](#GCodeCore) applies the
transformations to the user-provided coordinates. For example, the
[move()](#GCodeCore.move()) method, which accepts coordinates as a
[Point](#Point) or individual X, Y, Z values, applies the current
transformation to these coordinates before generating the corresponding
G-code commands.

To add a new transformation method:

1. Define the transformation matrix.
2. Use the [`chain_transform()`](#CoordinateTransformer.chain_transform())
   method to apply the new matrix.

Example:

```python
def shear_xy(self, xy: float) -> None:
    shear_matrix = np.eye(4)  # Identity matrix
    shear_matrix[0, 1] = xy  # Shear in the XY plane
    self.chain_transform(shear_matrix)
```

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
