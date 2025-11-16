#!/usr/bin/env python3

# This example demonstrates how to probe the machine bed in direct write
# mode to create a heightmap that is printed in CSV format. The program
# probes the bed in a grid pattern, moving to each point on the machine
# bed and recording the Z height at each point.

import logging, sys
from argparse import ArgumentParser
from collections import namedtuple
from gscrib import GConfig, GCodeBuilder
from gscrib.excepts import DeviceError


Option = namedtuple("Option", ["type", "name", "default", "help"])

# ----------------------------------------------------------------------
# Command line definition
# ----------------------------------------------------------------------

description = "Probe the bed to create a heightmap"

options = (
    Option(str, "direct-write", "socket", "Direct write method"),
    Option(str, "host", "localhost", "Machine hostname/IP"),
    Option(str, "port", "8000", "Machine port"),
    Option(int, "baudrate", "250000", "Serial connection baudrate"),
    Option(float, "safe-z", 25, "Safe Z height"),
    Option(float, "probe-z", 0, "Probe Z height"),
    Option(float, "probe-speed", 100, "Probing feedrate"),
    Option(int, "width", 400, "Grid width"),
    Option(int, "height", 400, "Grid height"),
    Option(int, "spacing", 50, "Grid spacing"),
    Option(str, "log-level", "critical", "Print debug information"),
)


# ----------------------------------------------------------------------
# Command line parsing
# ----------------------------------------------------------------------


def parse_command_line_options():
    parser = ArgumentParser(description=description)

    for option in options:
        parser.add_argument(
            f"--{option.name}",
            type=option.type,
            default=option.default,
            help=option.help,
        )

    return parser.parse_args()


# ----------------------------------------------------------------------
# Probing program
# ----------------------------------------------------------------------


def execute_probing_program(ctx):
    results = []
    grid_points = []

    min_axes = (0, 0, 0)
    max_axes = (ctx.width, ctx.height, ctx.safe_z)

    # Configure and initialize the builder

    config = GConfig.from_object(ctx)
    g = GCodeBuilder(config)
    w = g.get_writer()

    # Configure settings for the program

    g.set_time_units("seconds")
    g.set_length_units("millimeters")
    g.set_distance_mode("absolute")
    g.set_bounds("axes", min_axes, max_axes)

    # Reset axes and move to safe Z

    g.set_axis(point=(0, 0, 0))
    g.rapid(Z=ctx.safe_z)

    # Create the grid points in a zig-zag pattern

    for i, y in enumerate(range(0, ctx.height + 1, ctx.spacing)):
        row = [(x, y) for x in range(0, ctx.width + 1, ctx.spacing)]
        row = reversed(row) if i % 2 else row
        grid_points.extend(row)

    # Probe the grid points

    for x, y in grid_points:
        g.rapid(point=(x, y))
        g.pause()  # Pause for user to move the probe

        try:
            g.probe("towards", Z=ctx.probe_z, F=ctx.probe_speed)
        except DeviceError as e:
            print("Probe failed. Exiting now.", file=sys.stderr)
            g.teardown()
            sys.exit(1)

        try:
            g.sleep(0)  # Sync with the machine
            g.wait()  # Ensure probe is done
            g.query("position")
        except DeviceError as e:
            logging.warning("Warning: %s", e)

        nz = w.get_parameter("z")
        results.append((x, y, nz))

        g.rapid(z=ctx.safe_z)

    # Program termination

    g.rapid(x=0, y=0)
    g.stop()
    g.teardown()

    # Adjust the heightmap to the lowest point

    min_z = min(z for _, _, z in results)
    results = [(x, y, z - min_z) for x, y, z in results]

    return results


# ----------------------------------------------------------------------
# Main function
# ----------------------------------------------------------------------

if __name__ == "__main__":
    context = parse_command_line_options()
    logging.basicConfig(level=context.log_level.upper())
    results = execute_probing_program(context)

    for x, y, z in results:
        print(f"{x}, {y}, {z}")
