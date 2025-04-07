# Gscrib: Supercharge G-code with Python

**Gscrib** is a powerful Python library for generating G-code for CNC
machines, 3D printers, and other automated devices. It provides a
comprehensive set of tools for creating, transforming, and optimizing
toolpaths, empowering creators to write clean, efficient, and highly
customizable G-code programs.

## Features

- **Core G-code Generation**: Linear and rapid moves, coordinate
  transformations, and more.
- **Advanced Path Interpolation**: Trace arcs, splines, helices,
  parametric curves, and more.
- **Temperature & Tool Control**: Manage spindle speed, laser power,
  fan speed, and more.
- **State Management**: Track machine state for safe and consistent
  operations.
- **Transformation Utilities**: Apply rotations, scaling, reflections,
  and more.
- **Customizable Hooks**: Add custom logic to modify parameters dynamically.
- **Multiple Output Options**: Write G-code to files, serial ports,
  or network sockets.
- **Error Handling**: Built-in validation and error handling.

## Documentation

Documentation for the latest version of the project can be found at
[Read the Docs](https://gscrib.readthedocs.io/en/latest/).

## Examples

### Basic Usage

```python
from gscrib import GCodeBuilder

g = GCodeBuilder(output="output.gcode"):

g.set_axis(x=0, y=0, z=0)     # Set initial position
g.rapid(z=5)                  # Rapid move up to Z=5
g.rapid(x=10, y=10)           # Rapid move to (10, 10)
g.tool_on("clockwise", 1000)  # Start tool at 1000 RPM
g.coolant_on("flood")         # Enable flood coolant
g.move(x=20, y=20, F=1500)    # Linear move with feed rate
g.coolant_off()               # Turn off coolant
g.tool_off()                  # Turn off tool

g.teardown()                  # Flush file changes
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
g.trace.spiral(target=(10, 0), turns=2)

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

# Custom extrusion hook function
def extrude_hook(origin, target, params, state):
    dt = target - origin
    length = math.hypot(dt.x, dt.y, dt.z)
    params.update(E=0.1 * length) # Add extrusion parameter
    return params

g.add_hook(extrude_hook)
g.move(x=10, y=0)   # Will add E=1.0
g.move(x=20, y=10)  # Will add E=1.414
g.move(x=10, y=10)  # Will add E=1.0
g.remove_hook(extrude_hook)
```

### Toolpath Manipulation

Matrix transformations allow you to manipulate toolpaths by applying
translations, rotations, scaling, reflections, or mirroring.

```python
# Save current transformation state
g.transform.save_state()

# Translate 10 units along X and Y
g.transform.translate(x=10, y=10)

# Change the pivot point for the next transformation
g.transform.set_pivot(point=(5, 5, 0))

# Rotate 45 degrees around Z-axis
g.transform.rotate(angle=45, axis="z")

# Trace an arc in the transformed coordinate system
g.trace.arc(target=(10, 0), center=(5, 0))

# Restore original transformation state
g.transform.restore_state()
```

By default, transformations are pushed to and popped from a stack, but
you can assign names to them to reuse your custom coordinate systems.

```python
# Save a transformation state with a name
g.transform.save_state("my_transorm")

# Rotate and scale the coordinate system
g.transform.rotate(angle=90, axis="z")
g.transform.scale(2.0)
g.move(x=10, y=10)

# Restore the transformation state
g.transform.restore_state("my_transorm")

# Trace an arc in the restored coordinate system
g.trace.arc(target=(10, 0), center=(5, 0))
```

### Enforcing Parameter Limits

You can define safe operating ranges for key machine parameters using
`set_bounds()`. This helps prevent invalid or potentially dangerous
values during runtime. Once bounds are set, any command that violates
them will raise a `ValueError`.

```python
# Define safety bounds for different machine parameters
g.set_bounds("bed-temperature", min=0, max=200)
g.set_bounds("chamber-temperature", min=0, max=60)
g.set_bounds("hotend-temperature", min=0, max=200)
g.set_bounds("feed-rate", min=100, max=7000)
g.set_bounds("tool-number", min=1, max=5)
g.set_bounds("tool-power", min=0, max=100)

# You can also constrain motion in 3D space
g.set_bounds("axes", min=(0, 0, -10), max=(20, 20, 10))

# These will raise exceptions due to being out of bounds
g.set_feed_rate(10000)    # Exceeds max feed rate
g.move(x=5, y=5, F=10)    # Below min feed rate
g.move(x=-100)            # Outside defined X-axis range
```

### Context Managers

Gscrib provides several context managers to allow you to modify settings,
apply transforms, or add hooks for specific operations, and automatically
restore the previous state when the context ends.

```python
# Automatic teardown (flush and close)
with GCodeBuilder(output="outfile.gcode") as g:
    g.move(x=10, y=10)

# Temporary absolute positioning
with g.absolute_mode():
    g.move(x=10, y=10)

# Temporary relative positioning
with g.relative_mode():
    g.move(x=10, y=10)

# Temporary hooks
with g.move_hook(temporary_hook):
    g.move(x=10, y=10)

# Temporary transformations
with g.current_transform():
    g.transform.rotate(angle=45, axis="z")
    g.trace.arc(target=(10, 0), center=(5, 0))

# Temporary restore of named transformations
with g.named_transform("my_transorm"):
    g.transform.rotate(angle=45, axis="z")
    g.trace.arc(target=(10, 0), center=(5, 0))
```

## Projects Using Gscrib

**Vpype-Gscrib**: A [vpype](https://vpype.readthedocs.io/en/latest/)
plugin that extends vpype’s capabilities with a powerful command-line
interface for converting SVG files into G-code. It provides a flexible
and efficient toolkit for plotter and CNC workflows. See
[Vpype-Gscrib's Documentation](https://vpype-gscrib.readthedocs.io/en/latest/)

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

## Acknowledgments

Gscrib is an independent project that was initially forked from
[Mecode](https://github.com/jminardi/mecode), a lightweight Python library
for G-code generation originally developed at the
[Lewis Lab](http://lewisgroup.seas.harvard.edu/) at Harvard University.
The development of Gscrib was heavily influenced by Mecode’s design, and
we are grateful for the foundational work done by its original author
and contributors.

Additionally, Gscrib includes code developed by the authors of
[Printrun](https://github.com/kliment/Printrun), a Python-based suite
for controlling 3D printers.

As Gscrib continues to evolve with new features, optimizations, and
expanded capabilities, we recognize and appreciate the importance of this
early work in shaping its foundation.

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

See the [LICENSE](LICENSE) file for more details.
