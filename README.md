# Gscrib: Supercharge G-code with Python

**Gscrib** is a powerful Python library for generating G-code for CNC
machines, 3D printers, and other automated devices. It provides a
comprehensive set of tools for creating, transforming, and optimizing
toolpaths, empowering creators to write clean, efficient, and highly
customizable G-code programs.

## Features

- **Core G-code Generation**: Generate essential G-code commands for
  linear and rapid moves, coordinate transformations, and more.
- **Advanced Path Interpolation**: Create arcs, splines, helices, spirals,
  and parametric curves for complex toolpaths.
- **Temperature & Tool Control**: Manage spindle speed, laser power, fan
  speed, and temperature settings.
- **State Management**: Track machine state (position, distance mode,
  units, etc.) for safe and consistent operations.
- **Transformation Utilities**: Apply translations, rotations, scaling,
  reflections, and mirroring to toolpaths.
- **Customizable Hooks**: Add custom logic to modify parameters dynamically.
- **Multiple Output Options**: Write G-code to files, serial ports,
  or network sockets.
- **Error Handling**: Built-in validation and error handling ensure safe
  and reliable G-code generation.

## Documentation

Documentation for the latest version of the project can be found at
[Read the Docs](https://gscrib.readthedocs.io/en/latest/).

## Examples

### Basic Usage

```python
from gscrib import GCodeBuilder

with GCodeBuilder(output="output.gcode") as g:
    g.set_axis(x=0, y=0, z=0)     # Set initial position
    g.rapid(z=5)                  # Rapid move up to Z=5
    g.rapid(x=10, y=10)           # Rapid move to (10, 10)
    g.tool_on("clockwise", 1000)  # Start tool at 1000 RPM
    g.coolant_on("flood")         # Enable flood coolant
    g.move(x=20, y=20, F=1500)    # Linear move with feed rate
    g.coolant_off()               # Turn off coolant
    g.tool_off()                  # Turn off tool
```

Generated G-code:

```
G92 X0 Y0 Z0 ; Set axis position
G0 Z5
G0 X10 Y10
S1000 M03 ; Start tool, clockwise
M08 ; Turn on coolant, flood
G1 X20 Y20 F1500
M09 ; Turn off coolant
M05 ; Stop tool
```

### Path Interpolation

```python
# Clockwise arc
g.set_direction("clockwise")
g.trace.arc(target=(10, 0), center=(5, 0))

# Counterclockwise arc
g.set_direction("counter")
g.trace.arc(target=(0, 0), center=(0, -10))

# Spline curve through a series of control points
control_points = [(0, 0), (5, 10), (10, -5), (15, 0)]
g.trace.spline(control_points)

# Helix
g.trace.helix(target=(10, 0, 10), center=(-10, 0), turns=3)

# Spiral
g.trace.spiral(target=(10, 0, 5), turns=2)

# Thread
g.trace.thread(target=(10, 0, 5), pitch=1)
```

### Advanced Path Interpolation

Use mathematical functions to generate parametric curves and complex
shapes dynamically.

```python
import numpy as np

# Custom parametric circle function

def circle(thetas):
    x = 10 * np.cos(2 * np.pi * thetas)
    y = 10 * np.sin(2 * np.pi * thetas)
    z = np.zeros_like(thetas)
    return np.column_stack((x, y, z))

# Estimate path length
length = g.trace.estimate_length(100, circle)

# Interpolate the path
g.set_resolution(0.1)
g.trace.parametric(circle, length)
```

### Custom Hooks

Hooks allow you to dynamically modify movement parameters, such as
adding extrusion for 3D printing.

```python
import math

def extrude_hook(origin, target, params, state):
    dt = target - origin
    length = math.hypot(dt.x, dt.y, dt.z)
    params.update(E=0.1 * length) # Add extrusion parameter
    return params

with g.hook(extrude_hook):
    g.move(x=10, y=0)   # Will add E=1.0
    g.move(x=20, y=10)  # Will add E=1.414
    g.move(x=10, y=10)  # Will add E=1.0
```

### Toolpath Manipulation

Matrix transformations allow you to manipulate toolpaths by applying
translations, rotations, scaling, reflections, or mirroring.

```python
# Save current transformation state
g.push_matrix()

# Translate 10 units along X and Y
g.translate(x=10, y=10)

# Rotate 45 degrees around Z-axis
g.rotate(angle=45, axis="z")

# Trace an arc in the transformed coordinate system
g.trace.arc(target=(10, 0), center=(5, 0))

# Restore original transformation state
g.pop_matrix()
```

## Development setup

Here is how to clone the project for development:

```bash
$ git clone https://github.com/joansalasoler/gscrib.git
$ cd gscrib
```

Create a virtual environment:

```bash
$ python3 -m venv venv
$ source venv/bin/activate
```

Install `gscrib` and its dependencies:

```bash
$ pip install --upgrade pip
$ pip install -e .
$ pip install -r requirements.txt
$ pip install -r requirements.dev.txt
```

Run tests:

```bash
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (```git checkout -b feature/amazing-feature```)
3. Commit your changes (```git commit -m 'Add some amazing feature'```)
4. Push to the branch (```git push origin feature/amazing-feature```)
5. Open a Pull Request

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

See the [LICENSE](LICENSE) file for more details.
