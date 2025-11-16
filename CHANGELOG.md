# Change log

## 1.1.1 (2025-11-15)

* Switches from poetry to uv
* Updates Numpy and Scipy min versions and in the process bumps the python min ver to 3.11
* Adjusts tests so that can be run quickly in parallal using pytest-xdist
* Ruff checking and formatting for the whole project (instead of black, isort and pylint)

## 1.1.0 (2025-04-28)

* Allows dwell for zero seconds (G4 P0).
* New G-code command: G28 (auto-home).
* New G-code commands: G38.X (probe commands)
* New G-code commands: M105 and M114 (machine state queries).
* Improves device synchronization and exception handling.
* Adds automatic line numbering and checksums on supported devices.
* Adds methods to create GConfig from dictionary-like objects.
* Adds resend support for lost or corrupted messages.
* Adds support for device readings (positions, temperatures, etc.).
* Adds support for retrieving writers by index.
* Fix user bounds checking with unknown coordinates.
* Fix serial port parsing.

## 1.0.1 (2025-04-18)

* Printrun writer waits for device aknowledgements.
* Strip new lines when printing to a logger.
* Fix default value for direct_write.

## 1.0.0 (2025-04-15)

* First stable release of Gscrib.

## 0.1.0 (UNRELEASED)

* Initial release
