# Quick-Start Guide

**Gscrib** is a **Python library** that helps you write clean, flexible,
and reliable **G-code** for CNC machines, 3D printers or laser cutters.
All this without writing a single G-code line!

**This guide will walk you through**:

* Installing Gscrib.
* Writing your first G-code script in Python.
* Automating, customizing, and controlling toolpaths.
* Exploring advanced features for more complex projects.

---

## Introduction

Writing raw G-code by hand is often slow, repetitive, and error-prone.
**Gscrib** solves this by letting you write simple, readable, and easy to
maintain **Python code** to describe your toolpaths, which it converts
into clean, correct **G-code** for you.

**Benefits**:

- Write machine logic in Python, not raw G-code.
- Control complex movements with simple scripts.
- Build safer, more reliable machine programs.

## Installation

To use **Gscrib**, you need to have **Python 3.10 or newer** installed on
your computer. You'll also need **Pip** to install the library. If you're
new to Python or Pip, these links will help you get set up:

- [Python Downloads](https://www.python.org/downloads/)
- [Pip Installation Guide](https://pip.pypa.io/en/stable/installation/)

Once you're set up, open your terminal and install **Gscrib** with:

```bash
pip install gscrib
```

That's it! This will download and install **Gscrib** and any other software
it needs to work. Once installed, you're ready to start using Gscrib in
your Python scripts.

## Writing Your First Gscrib Program

Let's write a super simple program that creates a G-code file (output.gcode)
to move your machine from point A to point B:

```python
from gscrib import GCodeBuilder

g = GCodeBuilder(output="output.gcode")

g.set_axis(x=0, y=0, z=0)     # Set start position
g.rapid(z=5)                  # Move Z axis up quickly
g.rapid(x=10, y=10)           # Move to X=10, Y=10
g.tool_on("clockwise", 1000)  # Turn on the tool at 1000 RPM
g.move(x=20, y=20, F=1500)    # Move to X=20, Y=20 at feed rate 1500
g.tool_off()                  # Turn off the tool
g.teardown()                  # Finalize and save the file
```

This is a very basic example. Once you're comfortable, you can add loops,
curves, safety checks, and even export directly to your CNC. All using
Python's full power.

## Features at a Glance

Gscrib isn't just about simple moves. Here's a quick overview of its key
capabilities:

- **Path Interpolation**: Easily create circles, arcs, spirals, helices,
  splines, and more.
- **State Awareness**: Tracks your machine's position, tool status, and
  safety limits automatically.
- **Hooks & Customization**: Use simple Python functions to add custom
  behavior.
- **Transformations**: Move, scale, rotate, and mirror your toolpaths
  without rewriting coordinates.
- **Safe Output**: Export to G-code files or send instructions directly
  to your machine.

## Full Example: Drilling a Grid of Holes

This example demonstrates how to generate a G-code program to drill a
grid of holes, combining Python loops with G-code generation. It covers
the setup, drilling, and finalization steps.

```python
from itertools import product
from gscrib import GCodeBuilder

# Set work parameters

file_name = "grid_holes.gcode"    # Output file name
feed_rate = 500                   # Feed rate (mm/min)
safe_z = 10                       # Safe Z position (1 cm above surface)
work_z = -5                       # Drill depth (5 mm below surface)

with GCodeBuilder(output=file_name) as g:

    # Set machine bounds (limits for movement)
    g.set_bounds("axes", min=(0, 0, -50), max=(100, 100, 50))

    # Configure settings for the program

    g.set_axis(point=(0, 0, 0))        # Tool is at the origin
    g.set_length_units("millimeters")  # Set units to millimeters
    g.set_time_units("seconds")        # Set time units to seconds
    g.set_distance_mode("absolute")    # Set absolute positioning mode
    g.set_feed_rate(feed_rate)         # Set speed of tool movement

    # Activate the tool and coolant system

    g.rapid(z=safe_z)                  # Rapid move to safe Z
    g.tool_on("clockwise", 1000)       # Start the tool (1000 rpm)
    g.coolant_on("flood")              # Turn on flood coolant
    g.sleep(1)                         # Dwell for 1 second

    # Drill a 5x5 grid of holes, each 10 mm apart. The `product` function
    # generates (x, y) coordinate pairs for a 5x5 grid.

    for x, y in product(range(0, 50, 10), repeat=2):
        g.rapid(point=(x, y))          # Rapid move to the hole position
        g.move(z=work_z)               # Drill down to 5 mm depth
        g.rapid(z=safe_z)              # Rapid move to safe Z

    # Program termination

    g.tool_off()                       # Turn off the tool
    g.coolant_off()                    # Turn off the coolant
    g.rapid(x=0, y=0)                  # Rapid move back to origin
    g.stop()                           # Halt the program
```

This script generates a G-code file that drills a 5x5 grid of holes, each
spaced 10 mm apart. The use of loops makes it easy to scale or modify the
pattern, demonstrating the flexibility of Python for G-code generation.

## Sending G-code with Writers

By default, Gscrib can save your generated G-code to a file using the
`output` option when you create a [GCodeBuilder](#GCodeBuilder). But you
can also send it anywhere: the console, a serial port, or over a network.
Gscrib uses writers to handle this. You can mix and match as many writers
as you like. Gscrib will send each G-code line to all registered writers,
so you can save to a file, print to the console, and send to a machine
all at once if you like.

Basic setup looks like this:

```python
from gscrib import GCodeBuilder

g = GCodeBuilder(
    output='output.gcode',  # Save to a file
    print_lines=True,       # Also print each line to stdout
    direct_write='serial',  # Or send directly to a machine via serial
    host='192.168.0.100',   # Host/IP for network (socket mode)
    port=8000,              # Port number for network or serial
    baudrate=250000         # Baud rate for serial connections
)
```

You can also add writers manually with `add_writer()`. Gscrib includes
ready-made writers in [gscrib.writers](#gscrib.writers) for files, serial
ports, sockets, and the console.

## Beyond Basics

### Path Interpolation

Draw curves, arcs, spirals, helices, and threads with single commands.

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

### Transforming Paths

Transformations make it easy to shift, rotate, scale, or mirror your
entire design without manually adjusting coordinates.

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

# Restore original state before transformations
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

### State Tracking And Validation

Easily track and manage the machine's state during operations, including
tool activity, position, feed rates, and more. The state is updated
automatically as actions are performed.

```python
# Set the initial position and feed rate
g.set_axis(x=0, y=0, z=0)
g.set_distance_mode("relative")
g.set_feed_rate(1200)

# Activate the tool and move to a position
g.tool_on("cw", 1000)
g.move(x=10, y=10)

# Access and print the current state
print(f"Tool Active: { g.state.is_tool_active }")    # True
print(f"Tool Power: { g.state.tool_power }")         # S=1000
print(f"Feed Rate: { g.state.feed_rate }")           # F=1200
print(f"Position: { g.state.position }")             # X=10, Y=10, Z=0

# Move again with an updated feed rate
g.move(x=20, y=20, F=800)

# State automatically reflects the changes
print(f"Feed Rate: { g.state.feed_rate }")           # F=800
print(f"Position: { g.state.position }")             # X=30, Y=30, Z=0

# Attempt to change the spindle direction while the tool is active
g.tool_on("ccw", 2000)    # This will raise a ToolStateError
```

### Enforcing Parameter Limits

Safe operating ranges for key machine parameters can be set using
`set_bounds()`. This helps prevent invalid or potentially dangerous
values during runtime. Once bounds are set, any command that violates
them will raise an exception.

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

### Dynamic Behavior with Hooks

Sometimes, you'll want to automatically adjust machine parameters while
generating paths. That's where hooks shine, allowing you to modify
parameters dynamically.

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

For basic extrusion, Gscrib also provides a built-in hook for you:

```python
from gscrib.hooks import extrusion_hook

hook_function = extrusion_hook(
    layer_height = 0.2,
    nozzle_diameter = 0.4,
    filament_diameter = 1.75
)

with g.move_hook(hook_function)
    g.move(x=10, y=0)
```

### Context Managers

Context managers help you write cleaner, safer code by providing a
convenient way to temporarily modify settings, apply transformations, or
add hooks during operations, and automatically restore the previous state
once the block finishes.

```python
# Switch to absolute positioning for a specific operation
with g.absolute_mode():
    g.rapid(x=0, y=0)

# Switch to relative positioning for a specific operation
with g.relative_mode():
    g.move(x=10)
    g.move(y=10)

# Apply a transformation within a specific context
with g.current_transform():
    g.transform.rotate(angle=45, axis="z")
    g.trace.arc(target=(10, 0), center=(5, 0))

# Restore and apply a named transformation
with g.named_transform("my_transform"):
    g.transform.rotate(angle=45, axis="z")
    g.trace.arc(target=(10, 0), center=(5, 0))

# Add a custom hook for the duration of the operation
with g.move_hook(temporary_hook):
    g.move(x=10, y=10)
```

## Where to Go Next

Ready to go deeper? Explore the [full API reference](#gscrib) for more
examples, tips, and best practices. Start with [GCodeCore](#GCodeCore)
and [GCodeBuilder](#GCodeBuilder), they're the foundation of **Gscrib**.
