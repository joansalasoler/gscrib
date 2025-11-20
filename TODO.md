# TODO List

This is a wish-list of potential features and improvements for the
project. Please note that there is no guarantee these features will ever
be implemented. However, contributions towards implementing any of these
features are very welcome! Feel free to submit pull requests, open issues,
or suggest additional ideas to help improve the project.

## Add Support for More G-code Commands

Enhance G-code compatibility by supporting more commands, for example:

* G43, G44: Tool Length Compensation

## Simulate Canned Cycles with Plain G-code

Implement common CNC canned cycles (G81, G82, G83, etc.) as plain G0/G1
commands. This approach will increase flexibility by allowing hooks,
transformations, and custom operations to be applied to the G-code,
ensuring broad compatibility with many machines while offering greater
control over how the G-code is processed.

## Add More Real-World Usage Examples

Include practical examples that demonstrate how to use the library
in real workflows:

* **Postprocessing a plain G-code file**: Show how to write a script that
  loads a G-code file, processes toolpaths, and saves the result.
* **FreeCAD CAM Postprocessor**: Provide an example postprocessor that
  works with FreeCAD’s internal CAM output. See [FreeCAD’s wiki](https://wiki.freecad.org/CAM_Postprocessor_Customization)
  for reference.
* **Advanced Hooks for Complex Effects**: Demonstrate creative uses of
  hooks, such as simulating temperature-driven material changes. A great reference is the
  [wood.py](https://github.com/MoonCactus/gcode_postprocessors/blob/master/wood/wood.py)
  script, which varies temperature to simulate wood grain.

## Ensure Selected Plane Affects Interpolated Paths

Make sure that the selected plane (XY, XZ, or YZ) influences the
generation of interpolated paths during G-code generation. Even when
matrix transformations are in play, allowing the selected plane to
affect the PathTracer method improves user experience and simplifies
code generation.

## Advanced Toolpaths

Implement trochoidal and other advanced toolpaths as a tracing method
in PathTracer, or as a form of interpolation that can be combined with
the existing PathTracer methods.

## Infill Algorithms

Provide a variety of infill algorithms such as zigzag, meander, honeycomb,
or Hilbert curves. For this to be really useful, implement methods for
defining the shapes to be filled.

## Iterators for Grids, Polygons, and More

Implement convenient iterators for common geometric structures, such as
grids, polygons, and other shapes. This functional approach will simplify
the creation of complex paths, enabling users to easily define operations
across regular patterns without manually calculating each point.

## Simple Ordering Algorithms

Implement functions to reorder a set of points using various traversal
patterns like row major, column major, nearest neighbor, shortest path,
or random.

## Add Common Hooks for Standard Operations

Extend the existing hook system by adding the most common operations,
such as automatic filament extrusion, limiting feed rates, temperature
adjustments, and other frequently needed actions.

## Expand Axis Support Beyond X, Y, and Z

Extend support to additional axes (e.g., A, B, C, U, V, W) beyond the
currently supported X, Y, and Z. While additional axes can be set as
keyword parameters, they are not fully integrated into the system.

## Scaffolding System

Scaffolding means creating a basic structure for a program. Implement a
extendable scaffolding system that provides common templates for G-code
programs, including initialization, error handling, and shutdown sequences.

## Speeds, Feeds and Temperature Calculators

Investigate the feasibility of integrating a comprehensive speeds,
feeds and temperature calculator into the system. Additionally, provide
hooks to dynamically adjust these values during G-code generation.

## Estimate Machining Time

Implement a function to estimate machining time based on speeds, feeds
and traveled distances.
