.. admonition:: Support Gscrib
   :class: tip

   Love **Gscrib**? Maintaining it takes time and effort. If you find it
   useful and want to help Gscrib and its docs grow and improve, consider
   sponsoring on `GitHub <https://github.com/sponsors/joansalasoler>`_ ❤️

Gscrib: Supercharge G-code with Python
======================================

**Gscrib** is a Python library built to enhance your CNC, 3D printing,
and automated fabrication workflows. It offers a powerful suite of tools
for generating, transforming, and optimizing toolpaths, enabling creators
to write clean, efficient, and highly customizable G-code with ease.

Is This the Right Tool for You?
-------------------------------

Traditional G-code is the backbone of CNC and 3D printing, but as designs
become more intricate, it can quickly become cumbersome, error-prone, and
hard to maintain. **Gscrib** takes your G-code to the next level, offering
a more organized, structured, and flexible approach to G-code.

With **Gscrib**, you can incorporate high-level logic, automation, and
customization without needing advanced software development skills.
Whether you're generating complex toolpaths, dynamically adjusting
parameters, or managing multiple machine aspects, **Gscrib** makes it
simple and intuitive.

Powerful Yet Simple
-------------------

**Gscrib** is designed for users who want the power of Python without the
complexity. Here's how it makes G-code creation easier and more efficient:

- **Readability & Maintainability**: Say goodbye to cryptic, error-prone
  G-code. **Gscrib** lets you write clean, readable scripts that are easy
  to modify and debug.
- **Reusable Code**: Automate tasks and create modular, reusable scripts
  that save you time and effort across projects.
- **Error-Free G-code**: Avoid mistakes with automatic error-checking
  that ensures your G-code is always safe and correct.
- **Seamless Integration**: Easily integrate with other systems (CNC
  controllers, 3D printers, and more) for a fully customized solution.
- **Automate tasks**: Easily generate complex toolpaths like arcs,
  splines, and spirals, without manually calculating each point.
- **Device Sensors**: Read real-time machine data such as position,
  temperature, and other sensor values directly from connected devices.
- **Add custom logic**: Modify your G-code on the fly with hooks for
  real-time adjustments, such as adding extrusion or managing speeds.
- **Effortless Transformations**: Apply translations, rotations, and
  scaling to your toolpaths with just a few lines of code.
- **Multiple Output Options**: Write your G-code not just to files, but
  directly to connected devices via serial ports or network sockets.

Even if you're not a Python expert, **Gscrib** integrates seamlessly
into your workflow, giving you unmatched control over your machines.

Why Choose Gscrib?
------------------

If you're happy with standard G-code and don't need to generate complex
toolpaths or customize the process, then plain G-code might suffice for
your needs. However, if you're regularly working with complicated parts
or looking for ways to automate your process, **Gscrib** will make your
workflow faster, more precise, and more flexible.

- **Save Time & Reduce Errors**: Automate repetitive tasks and reuse
  scripts, speeding up your workflow while reducing mistakes.
- **Manage Complex Operations Easily**: From tool control to machine
  states, **Gscrib** simplifies managing intricate operations.
- **Stay in Control**: Get flexible, powerful G-code that you can
  customize to fit your exact needs while keeping your process clean
  and efficient.

With **Gscrib**, you're not just writing G-code —you're writing smarter,
more efficient programs that adapt to your needs.

Aim of the Project
------------------

The goal of **Gscrib** is to offer an intuitive and flexible solution
for generating G-code programs.

**Key Objectives:**

- **Accuracy & Reliability** — Ensure consistent and correct G-code
  output, compatible with a variety of machines and workflows, minimizing
  errors and maximizing precision.
- **Flexibility** — Support a wide range of use cases, from CNC milling
  to pen plotting, by allowing users to configure and adapt the G-code
  generation process to meet their specific needs.
- **Extensibility** — Provide a highly modular and developer-friendly
  architecture that makes it easy to add new features, support additional
  hardware, and adapt to different workflows with minimal effort.
- **Ease of Use** — Provide an intuitive and well-documented API, making
  it accessible even for those with limited programming experience.
- **Open-Source Collaboration** — Encourage contributions from the
  community to enhance the library and adapt it to new use cases.

.. toctree::
   :maxdepth: 1
   :caption: Contents

   Home <self>
   Quick-Start Guide <user-guide>
   Development Guide <dev-guide>
   Quick Reference <quick-reference>
   G-Code Mappings Table <gcode-table>
   Module Index <modindex>
   General Index <genindex>
   License <license>

API Reference
-------------

.. autosummary::
   :toctree: api
   :caption: API Reference
   :template: module.rst
   :recursive:

   gscrib
   gscrib.codes
   gscrib.enums
   gscrib.excepts
   gscrib.formatters
   gscrib.geometry
   gscrib.heightmaps
   gscrib.hooks
   gscrib.types
   gscrib.writers

.. image:: https://home.joansala.com/static/home/assets/logo.png
   :target: https://home.joansala.com/
   :alt: Gscrib is developed by Joan Sala
   :width: 175px
   :height: 24px
   :align: left