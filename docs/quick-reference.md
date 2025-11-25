# Gscrib Quick Reference

This reference shows how familiar G-code operations map to Gscrib's Python
API. Gscrib is a **stateful G-code builder** that tracks your machine's
state and generates appropriate G-code commands. Instead of writing raw
G-code, you call Python methods that handle the details.

## Key Differences from Raw G-code

- **State tracking:** Gscrib remembers position, feed rates, tool status, etc.
- **Coordinate transforms:** Like CAM software, rotate, scale, translate before output.
- **No G2/G3 arcs:** All curves become smooth G1 segments (controlled by `set_resolution()`).
- **Safety:** Built-in validation and bounds checking.

## Essential Tips

- **Set units early** before any movements.
- **Set resolution** with `set_resolution()` for smooth curves.
- **Use high-level methods** (`move`, `tool_on`) instead of `write` to maintain state.
- **Use context managers** like `with absolute_mode()` for temporary changes.
- **Add custom parameters** to any command (`move(x=10, custom_param="value")`).
- **Add inline comments** to any command (`move(x=10, comment="Inline comment")`).
- **Coordinates can be specified** as `x=10, y=5`, `Point(10, 5)` or `[10, 5]`.

---

## G-code to Gscrib Translation

| G-code param | Meaning | Gscrib equivalent |
|--------------|---------|-------------------|
| X Y Z | Position | `move(x=…, y=…, z=…)` |
| I J K | Arc center offsets | `center=(i, j, k)` in `trace.arc()` |
| R | Arc radius | `radius=` in `trace.arc_radius()` |
| F | Feed rate | `F=` in `move()` |
| S | Laser power | `power_on(…, power)` |
| S | Spindle speed | `tool_on(…, speed)` |
| P | Dwell time | `sleep(duration)` |
| T | Tool select | `tool_change(…, tool_number)` |

---

## 📏 Units & Coordinate Systems

| G-code | Gscrib | Notes |
|--------|--------|-------|
| G92 | {meth}`set_axis(point) <gscrib.GCodeBuilder.set_axis>` | Set position without moving. |
| G17 / G18 / G19 | {meth}`set_plane(plane) <gscrib.GCodeBuilder.set_plane>` | Ignored, use transforms instead |
| G20 / G21 | {meth}`set_length_units(units) <gscrib.GCodeBuilder.set_length_units>` | Inches or millimeters |
| — | {meth}`set_direction(direction) <gscrib.GCodeBuilder.set_direction>` | For arc interpolation logic. |
| — | {meth}`set_resolution(resolution) <gscrib.GCodeBuilder.set_resolution>` | Segmentation resolution. |
| — | {meth}`set_temperature_units(units) <gscrib.GCodeBuilder.set_temperature_units>` | Controller specific. |
| — | {meth}`set_time_units(units) <gscrib.GCodeBuilder.set_time_units>` | Controller specific. |

**Tips**

* Set units early in your program before any movements.
* Lower resolution values create smoother curves but larger files.
* The controller you use determines which temperature and time units apply.

**Examples**

```python
set_length_units("mm")      # G21
set_axis(x=0, y=0, z=5)     # G92 X0 Y0 Z5
```

## 🔀 Operation Modes

| G-code | Gscrib | Notes |
|--------|--------|-------|
| G90 | {meth}`set_distance_mode("absolute") <gscrib.GCodeBuilder.set_distance_mode>` | Absolute positioning. |
| G91 | {meth}`set_distance_mode("relative") <gscrib.GCodeBuilder.set_distance_mode>` | Relative positioning. |
| G93 | {meth}`set_feed_mode("inverse_time") <gscrib.GCodeBuilder.set_feed_mode>` | Feed as 1/time |
| G94 | {meth}`set_feed_mode("units_per_minute") <gscrib.GCodeBuilder.set_feed_mode>` | Standard feed mode |
| G95 | {meth}`set_feed_mode("units_per_revolution") <gscrib.GCodeBuilder.set_feed_mode>` | Feed per spindle rev |
| M82 | {meth}`set_extrusion_mode("absolute") <gscrib.GCodeBuilder.set_extrusion_mode>` | Absolute filament extrusion |
| M83 | {meth}`set_extrusion_mode("relative") <gscrib.GCodeBuilder.set_extrusion_mode>` | Relative filament extrusion |

**Tips**

* Absolute mode is safer for precise positioning.
* Relative mode is useful for incremental movements.
* Use context managers for temporary mode changes.

**Examples**

```python
set_distance_mode("absolute")      # G90
set_feed_mode("units_per_minute")  # G94
```

## 📈 Feeds & Speeds

| G-code | Gscrib | Notes |
|--------|--------|-------|
| F… | {meth}`set_feed_rate(speed) <gscrib.GCodeBuilder.set_feed_rate>` | Feed rate. |
| S… | {meth}`set_tool_power(power) <gscrib.GCodeBuilder.set_tool_power>` | Tool power/speed. |

**Tips**

* Feed rate and tool power persist until changed.
* Use {meth}`set_bounds() <gscrib.GCodeBuilder.set_bounds>` to enforce safe speed limits.

**Examples**

```python
set_feed_rate(1500)         # F1500
set_tool_power(8000)        # S8000 (without M03)
```

## 🔧 Tool Control

| G-code | Gscrib | Notes |
|--------|--------|-------|
| S… M03 | {meth}`power_on("constant", power) <gscrib.GCodeBuilder.power_on>` | Constant-power mode. |
| S… M03 | {meth}`tool_on("clockwise", speed) <gscrib.GCodeBuilder.tool_on>` | CW spindle. |
| S… M04 | {meth}`tool_on("counter", speed) <gscrib.GCodeBuilder.tool_on>` | CCW spindle. |
| T… M06 | {meth}`tool_change("automatic", tool_number) <gscrib.GCodeBuilder.tool_change>` | Auto tool-change. |
| T… M06 | {meth}`tool_change("manual", tool_number) <gscrib.GCodeBuilder.tool_change>` | Manual tool-change. |
| M05 | {meth}`tool_off() <gscrib.GCodeBuilder.tool_off>` / {meth}`power_off() <gscrib.GCodeBuilder.power_off>` | Stop spindle / Power off tool. |

**Tips**

* Always turn off tool before tool changes.
* Use {meth}`power_on() <gscrib.GCodeBuilder.power_on>` for lasers, {meth}`tool_on() <gscrib.GCodeBuilder.tool_on>` for spindles.
* Check `state.is_tool_active` before operations.

**Examples**

```python
tool_on("cw", 12000)        # M03 S12000
power_on("constant", 80)    # M03 S80 (laser)
tool_change("manual", 2)    # T2 M06
tool_off()                  # M05
```

## 💧 Coolant Control

| M-code | Gscrib |
|--------|--------|
| M07 | {meth}`coolant_on("mist") <gscrib.GCodeBuilder.coolant_on>` |
| M08 | {meth}`coolant_on("flood") <gscrib.GCodeBuilder.coolant_on>` |
| M09 | {meth}`coolant_off() <gscrib.GCodeBuilder.coolant_off>` |

**Tips**

* Turn on coolant after tool start for proper flow.
* Use flood coolant for heavy cutting, mist for light work.
* Always turn off coolant before tool changes.

**Examples**

```python
coolant_on("flood")         # M08
coolant_off()               # M09
```

## 🔥 Temperature Control

| M-code | Gscrib | Notes |
|--------|--------|-------|
| M106 | {meth}`set_fan_speed(speed, fan_number) <gscrib.GCodeBuilder.set_fan_speed>` | Range 0 to 255. |
| M140 | {meth}`set_bed_temperature(temperature) <gscrib.GCodeBuilder.set_bed_temperature>` | Non-blocking. |
| M104 | {meth}`set_hotend_temperature(temperature) <gscrib.GCodeBuilder.set_hotend_temperature>` | Non-blocking. |
| M141 | {meth}`set_chamber_temperature(temperature) <gscrib.GCodeBuilder.set_chamber_temperature>` | Non-blocking. |

**Tips**

* Temperature units controlled by {meth}`set_temperature_units() <gscrib.GCodeBuilder.set_temperature_units>`.
* Use `halt("wait-for-*")` methods to block until temperature reached.
* Use {meth}`set_bounds() <gscrib.GCodeBuilder.set_bounds>` to prevent dangerous temperatures.

**Examples**

```python
set_bed_temperature(60)          # M140 S60
set_hotend_temperature(200)      # M104 S200
set_fan_speed(255)               # M106 P0 S255
```

## 🎯 Motion Control

| G-code | Gscrib | Notes |
|--------|--------|-------|
| G0 | {meth}`rapid(point) <gscrib.GCodeCore.rapid>` | Rapid move. |
| G0 | {meth}`rapid_absolute(point) <gscrib.GCodeCore.rapid_absolute>` | Absolute rapid (ignore transforms). |
| G1 | {meth}`move(point) <gscrib.GCodeCore.move>` | Linear move. |
| G1 | {meth}`move_absolute(point) <gscrib.GCodeCore.move_absolute>` | Absolute linear (ignore transforms). |
| G28 | {meth}`auto_home(point) <gscrib.GCodeBuilder.auto_home>` | Homes axes. |

**Tips**

* Use {meth}`rapid() <gscrib.GCodeCore.rapid>` for positioning, {meth}`move() <gscrib.GCodeCore.move>` for cutting.
* Bypass coordinate transforms with {meth}`rapid_absolute() <gscrib.GCodeCore.rapid_absolute>`/{meth}`move_absolute() <gscrib.GCodeCore.move_absolute>`.
* Current position becomes unknown after {meth}`auto_home() <gscrib.GCodeBuilder.auto_home>` if not specified.
* The behaviour of {meth}`auto_home() <gscrib.GCodeBuilder.auto_home>` may depend on the controller.

**Examples**

```python
rapid(z=5)                     # G0 Z5
rapid(x=10, y=5)               # G0 X10 Y5
move(x=20, y=10, F=1500)       # G1 X20 Y10 F1500
auto_home(x=0, y=0, z=0)       # G28 X0 Y0 Z0
```

## 🌀 Path Interpolation

| G-code | Gscrib | Notes |
|--------|--------|-------|
| G2/G3 (simulated) | {meth}`trace.arc(target, center) <gscrib.geometry.PathTracer.arc>` | Uses I/J/K-like geometry. |
| G2/G3 (simulated) | {meth}`trace.arc_radius(target, radius) <gscrib.geometry.PathTracer.arc_radius>` | Radius-mode arcs. |
| — | {meth}`trace.circle(center) <gscrib.geometry.PathTracer.circle>` | Full circle. |
| — | {meth}`trace.spline(points) <gscrib.geometry.PathTracer.spline>` | Cubic spline. |
| — | {meth}`trace.helix(…) <gscrib.geometry.PathTracer.helix>` | Helical path. |
| — | {meth}`trace.thread(…) <gscrib.geometry.PathTracer.thread>` | Thread-like helix. |
| — | {meth}`trace.spiral(…) <gscrib.geometry.PathTracer.spiral>` | Spiral pattern. |
| — | {meth}`trace.polyline(points) <gscrib.geometry.PathTracer.polyline>` | Linked G1 moves. |
| — | {meth}`trace.parametric(fn, length) <gscrib.geometry.PathTracer.parametric>` | Arbitrary parametric curve. |

**Tips**

* All arc/curve methods emit G1 segments; never G2/G3.
* Interpolated paths ignore the active plane, use coordinate transforms instead.
* Use {meth}`set_resolution() <gscrib.GCodeBuilder.set_resolution>` for smoother arcs/splines (smaller = smoother).
* Use {meth}`set_direction() <gscrib.GCodeBuilder.set_direction>` to control arc direction globally.

**Examples**

```python
set_resolution(0.1)                     # Fine resolution
set_direction("cw")                     # Clockwise arcs
trace.arc((10, 10), center=(5, 0))      # G2-like: X10 Y10 I5 J0
trace.arc_radius((20, 10), radius=30)   # G2-like with R30
trace.circle(center=(0, 0), radius=5)   # Full circle
trace.spline([(0,0), (5,10), (10,0)])   # Smooth curve
```

## 🧭 Coordinate Transforms

| Gscrib | Notes |
|--------|-------|
| {meth}`transform.set_pivot(point) <gscrib.geometry.CoordinateTransformer.set_pivot>` | Set rotation/scale center |
| {meth}`transform.mirror(plane) <gscrib.geometry.CoordinateTransformer.mirror>` | Mirror across plane |
| {meth}`transform.reflect(normal) <gscrib.geometry.CoordinateTransformer.reflect>` | Reflect across normal |
| {meth}`transform.rotate(angle, axis) <gscrib.geometry.CoordinateTransformer.rotate>` | Rotate in degrees |
| {meth}`transform.scale(sx [,sy [,sz]]) <gscrib.geometry.CoordinateTransformer.scale>` | Scale factors |
| {meth}`transform.translate(x, y, z) <gscrib.geometry.CoordinateTransformer.translate>` | Move origin |
| {meth}`transform.save_state(name) <gscrib.geometry.CoordinateTransformer.save_state>` | Save transform stack |
| {meth}`transform.restore_state(name) <gscrib.geometry.CoordinateTransformer.restore_state>` | Restore saved state |
| {meth}`transform.delete_state(name) <gscrib.geometry.CoordinateTransformer.delete_state>` | Delete saved state |

**Tips**

* Set pivot before rotating or scaling.
* Use {meth}`current_transform() <gscrib.GCodeCore.current_transform>` context manager for temporary changes.
* Transforms stack like CAM operations, not G-code offsets.
* Transforms affect all subsequent moves until changed.

**Examples**

```python
transform.save_state("original")    # Save current state
transform.translate(x=10, y=5)      # Move coordinate system
transform.set_pivot(point=(5, 5))   # Set rotation center
transform.rotate(45, axis="z")      # Rotate 45°
move(x=10, y=0)                     # Move in rotated system
transform.restore_state("original") # Back to start state
```

## ⏱️ Timing & Synchronization

| G/M-code | Gscrib | Notes |
|----------|--------|-------|
| G04 P… | {meth}`sleep(duration) <gscrib.GCodeBuilder.sleep>` | Dwell. |
| M00 / M01 | {meth}`pause(optional) <gscrib.GCodeBuilder.pause>` | Required/optional pause. |
| M02 / M30 | {meth}`stop(reset) <gscrib.GCodeBuilder.stop>` | End with/without reset. |
| M400 | {meth}`wait() <gscrib.GCodeBuilder.wait>` | Wait for motion to finish. |

**Tips**

* Time units controlled by {meth}`set_time_units() <gscrib.GCodeBuilder.set_time_units>`.
* Temperature units controlled by {meth}`set_temperature_units() <gscrib.GCodeBuilder.set_temperature_units>`.

**Examples**

```python
wait()               # M400
sleep(2)             # G04 P2
```

## ⛔ Halt Operations

| M-code | Gscrib | Notes |
|--------|--------|-------|
| M00 | {meth}`halt("pause") <gscrib.GCodeBuilder.halt>` | Alias {meth}`pause() <gscrib.GCodeBuilder.pause>` |
| M01 | {meth}`halt("optional-pause") <gscrib.GCodeBuilder.halt>` | Alias {meth}`pause(optional=True) <gscrib.GCodeBuilder.pause>` |
| M02 | {meth}`halt("end-without-reset") <gscrib.GCodeBuilder.halt>` | Alias {meth}`stop() <gscrib.GCodeBuilder.stop>` |
| M30 | {meth}`halt("end-with-reset") <gscrib.GCodeBuilder.halt>` | Alias {meth}`stop(reset=True) <gscrib.GCodeBuilder.stop>` |
| M60 | {meth}`halt("pallet-exchange") <gscrib.GCodeBuilder.halt>` | Pallet exchange. |
| M109 | {meth}`halt("wait-for-hotend") <gscrib.GCodeBuilder.halt>` | Wait to reach temperature. |
| M190 | {meth}`halt("wait-for-bed") <gscrib.GCodeBuilder.halt>` | Wait to reach temperature. |
| M191 | {meth}`halt("wait-for-chamber") <gscrib.GCodeBuilder.halt>` | Wait to reach temperature. |

**Tips**

* Use the aliased methods unless you have a specific reason not to.
* Use {meth}`emergency_halt() <gscrib.GCodeBuilder.emergency_halt>` for a complete safety shutdown sequence.

## 📡 Probing

| G-code | Gscrib |
|--------|--------|
| G38.2 | {meth}`probe("towards", point) <gscrib.GCodeBuilder.probe>` |
| G38.3 | {meth}`probe("towards-no-error", point) <gscrib.GCodeBuilder.probe>` |
| G38.4 | {meth}`probe("away", point) <gscrib.GCodeBuilder.probe>` |
| G38.5 | {meth}`probe("away-no-error", point) <gscrib.GCodeBuilder.probe>` |

**Tips**

* Use slow feed rates for accurate probing.
* Probe sets current position to unknown (actual stop depends on sensor).

**Examples**

```python
probe("towards", z=-10)    # G38.2 Z-10
```

## 🔍 Queries & Status

| M-code | Gscrib |
|----------|--------|
| M105 | {meth}`query("temperature") <gscrib.GCodeBuilder.query>` |
| M114 | {meth}`query("position") <gscrib.GCodeBuilder.query>` |
| ? | {meth}`write("?") <gscrib.GCodeBuilder.write>` |

**Tips**

* Only works in **direct write mode** with connected device.
* Read sensor values with {meth}`writer.get_parameter() <gscrib.writers.PrintrunWriter.get_parameter>`

**Examples**

```python
query("position")                   # M114
query("temperature")                # M105
z = writer.get_parameter("Z")
t = writer.get_parameter("B")
```

## 📝 Comments & Annotations

| G-code | Gscrib | Notes |
|---|--------|-------|
| ; comment | {meth}`comment("…") <gscrib.GCodeCore.comment>` | Uses formatter syntax |
| ; @set key=value | {meth}`annotate(key, value) <gscrib.GCodeCore.annotate>` | Structured annotation |

**Tips**

* Use {meth}`format.set_comment_symbols() <gscrib.formatters.DefaultFormatter.set_comment_symbols>` to change comment style.
* Annotations create machine-readable metadata.

**Examples**

```python
comment("Starting cut operation")    # ; Starting cut operation
comment(f"Feed rate: {feed_rate}")   # ; Feed rate: 1500
annotate("tool", "1/4 inch endmill") # ; @set tool=1/4 inch endmill
```

## ⚠️ Raw G-code

| G-code | Gscrib | Notes |
|--------|--------|-------|
| Raw G-code | {meth}`write(statement) <gscrib.GCodeBuilder.write>` | Bypasses state tracking |

**Tips**

* Raw `write("G1 X…")` does not update internal position.
* Prefer high-level methods to maintain state consistency.
* Only use for unsupported commands or special cases.
