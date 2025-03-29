Gscrib
======

Generate and manipulate G-code, making it easy for CNC and 3D printing
enthusiasts to automate and customize their machining processes.

Is This the Right Tool for You?
-------------------------------

TODO

Aim of the Project
------------------

The goal of **Gscrib** is to provide a seamless and flexible way
to generate G-code programs from vector-based designs.

**Key Objectives:**

- **Accuracy & Reliability** — Generate correct and consistent G-code
  output, ensuring compatibility with different machines and workflows.
- **Flexibility** — Support a wide range of use cases, from CNC milling
  to pen plotting, by allowing users to configure and adapt the G-code
  generation process to meet their specific needs.
- **Extensibility** — Provide a highly modular and developer-friendly
  architecture that makes it easy to add new features, support additional
  hardware, and adapt to different workflows with minimal effort.
- **Ease of Use** — Provide an intuitive and well-documented API that
  seamlessly integrates with existing workflows, making it easy for
  developers to adopt and use.
- **Open-Source Collaboration** — Encourage contributions from the
  community to enhance the plugin's capabilities and adapt it to new
  use cases.

.. toctree::
   :maxdepth: 1
   :caption: Contents

   Home <self>
   Development Guide <dev-guide>
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
   gscrib.writers
