#!/usr/bin/env python3

# This example demonstrates how to generate a G-code program to drill a
# grid of holes, combining Python loops with G-code generation. It covers
# the setup, the drilling operation, and the finalization steps.

from itertools import product
from gscrib import GCodeBuilder


# Set work parameters

output_file = "grid_holes.gcode"  # Output file name
feed_rate = 500  # Feed rate (mm/min)
safe_z = 10  # Safe Z position (1 cm above surface)
work_z = -5  # Drill depth (5 mm below surface)


with GCodeBuilder(output=output_file) as g:
    # Set machine bounds (limits for movement)
    g.set_bounds("axes", min=(0, 0, -50), max=(100, 100, 50))

    # Configure settings for the program

    g.set_axis(point=(0, 0, 0))  # Tool is at the origin
    g.set_length_units("millimeters")  # Set units to millimeters
    g.set_time_units("seconds")  # Set time units to seconds
    g.set_distance_mode("absolute")  # Set absolute positioning mode
    g.set_feed_rate(feed_rate)  # Set speed of tool movement

    # Activate the tool and coolant system

    g.rapid(z=safe_z)  # Rapid move to safe Z
    g.tool_on("clockwise", 1000)  # Start the tool (1000 rpm)
    g.coolant_on("flood")  # Turn on flood coolant
    g.sleep(1)  # Dwell for 1 second

    # Drill a 5x5 grid of holes, each 10 mm apart. The `product` function
    # generates (x, y) coordinate pairs for a 5x5 grid.

    for x, y in product(range(0, 50, 10), repeat=2):
        g.rapid(point=(x, y))  # Rapid move to the hole position
        g.move(z=work_z)  # Drill down to 5 mm depth
        g.rapid(z=safe_z)  # Rapid move to safe Z

    # Program termination

    g.tool_off()  # Turn off the tool
    g.coolant_off()  # Turn off the coolant
    g.rapid(x=0, y=0)  # Rapid move back to origin
    g.stop()  # Halt the program
