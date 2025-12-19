# AGENTS.md

This document defines the mandatory rules for all automated agents
modifying this repository. Any changes that do not follow these rules
will be rejected.

## The Three Laws of Agents

Following Isaac Asimov's foundational principles for artificial beings:

1. An agent may not harm a human's work or, through inaction, allow a
   human's work to come to harm.
2. An agent must follow the project's guidelines and human instructions,
   except where such actions would conflict with the First Law.
3. An agent must preserve the codebase's integrity as long as such
   preservation does not conflict with the First or Second Law.

## Agent Responsibilities

All agents contributing to this project are expected to operate as experts
in their domain, whether writing code, documentation, or tests, and to
follow the project's conventions, standards, and architectural patterns.
All source code produced by agents must follow best practices for modularity,
readability, and maintainability.

## Project Overview

Gscrib is a Python library for programmatically generating G-code for
CNC machines, 3D printers, laser cutters, and similar devices. Rather
than writing raw G-code, users describe toolpaths, machine actions, and
constraints using Python, which Gscrib converts into G-code output.
Gscrib prioritizes readability, correctness, and machine safety.

## Project Structure

```
gscrib/
├── gscrib/               # Main package directory
│   ├── __init__.py       # Package initialization
│   └── ...               # Other module files
├── tests/                # Tests directory
├── docs/                 # Project documentation
└── pyproject.toml        # Project configuration and metadata
```

## Architecture and Mental Model

* `GCodeCore` class manages low-level logic and raw string output.
* `GCodeBuilder` class to manages high-level user API and safety checks.
* `GState` class manages the single source of truth for machine state.
* `PathTracer` class provides path interpolation and length estimation.
* `CoordinateTransformer` handles matrix transformations.
* `formatters` control G-code string formatting and presentation.
* `writers` handle output destinations (files, sockets, etc).

## Coding Standards

Code is written for humans to read and understand, not just for machines
to execute. Prioritize clarity, simplicity, and maintainability over
cleverness or performance optimizations unless absolutely necessary or
specifically requested.

* Google-style docstrings are mandatory for all public APIs.
* Include a code example in the docstring for any complex logic.
* Follow PEP8 guidelines, but prioritize readability over compliance.
* Use explicit type annotations for all return types.
* Use explicit type annotations for all method arguments.
* Explicit type annotations for private methods are optional.
* Use `typeguard` for runtime type checking and validation logic.
* Use `pyproject.toml` as the single source of truth for project metadata.
* Ensure all code passes `pylint` checks.
* Do not break existing functionality.

## Testing and Validation

* Add new unit tests in the `tests/` directory for every new feature.
* Update existing tests in the `tests/` directory if behavior changes.
* Ensure all tests pass using the `poetry run pytest` command.
* Ensure code correctness using the `poetry run pylint -E gscrib` command.
* Tests should cover normal functionality as well as edge cases, error
  conditions, and failure scenarios.

## Environment and Commands

* Use `poetry` to manage all project dependencies.
* Use `poetry` to manage the Python virtual environment.
* Run `poetry install` to install dependencies.
* Run `poetry run pytest` to run the test suite.
* Run `poetry run pylint -E gscrib` to check for errors.
