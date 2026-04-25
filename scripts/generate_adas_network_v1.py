"""
ADAS Thesis - Road Network Generator
=====================================
File   : scripts/generate_adas_network.py
Output : maps/adas_network.xodr

Strategy: explicit set_start_point on every road with calculated world
coordinates. No auto-adjustment chains. Every road is placed exactly
where it should be. Verified against scenariogeneration 0.16.4.

World layout (all coords in metres):
  Junction centre: (0, 0)
  Highway runs West of junction, heading ~223 deg after connector arc
  Cross street runs North-South through junction
  S-curve exits East of junction

Run:
  cd C:/adas-thesis
  .venv/Scripts/Activate.ps1
  python scripts/generate_adas_network.py
"""

import os
import math
from scenariogeneration import xodr

OUTPUT_PATH = r"C:\adas-thesis\maps\adas_network.xodr"

# ── junction centre and radius ─────────────────────────────────────────────
JX, JY, R = 0.0, 0.0, 20.0

# ==============================================================================
# ZONE B — Urban intersection arms (placed first, junction owns their geometry)
# ==============================================================================
print("Building urban intersection arms...")

road_west = xodr.create_road(
    geometry=xodr.Line(200), id=10, left_lanes=2, right_lanes=2, lane_width=3.5)
road_west.add_type(xodr.RoadType.town, speed=50, speed_unit="km/h")

road_east = xodr.create_road(
    geometry=xodr.Line(200), id=11, left_lanes=2, right_lanes=2, lane_width=3.5)
road_east.add_type(xodr.RoadType.town, speed=50, speed_unit="km/h")

road_north = xodr.create_road(
    geometry=xodr.Line(150), id=12, left_lanes=2, right_lanes=2, lane_width=3.5)
road_north.add_type(xodr.RoadType.town, speed=50, speed_unit="km/h")

road_south = xodr.create_road(
    geometry=xodr.Line(150), id=13, left_lanes=2, right_lanes=2, lane_width=3.5)
road_south.add_type(xodr.RoadType.town, speed=50, speed_unit="km/h")

# Crosswalk on south arm for S3 pedestrian scenario
road_south.add_object(xodr.Object(
    s=140, t=0,
    Type=xodr.ObjectType.crosswalk,
    name="crosswalk_S3",
    orientation=xodr.Orientation.none,
    length=3.0, width=14.0, height=0.01
))

# Traffic signal on north arm
road_north.add_signal(xodr.Signal(
    s=145, t=-3.5,
    country="DE", Type="1000001", subtype="10",
    name="traffic_light_junction",
    dynamic=xodr.Dynamic.yes,
    orientation=xodr.Orientation.positive,
    zOffset=1.5
))

# ==============================================================================
# JUNCTION — CommonJunctionCreator places arms on a circle around (0,0)
# After this call each arm has its planview geometry set by the creator.
# road_connection='predecessor' means each arm's START touches the junction.
# Each arm then extends OUTWARD from the junction edge.
# ==============================================================================
print("Building 4-way junction...")

jc = xodr.CommonJunctionCreator(id=1, name="urban_intersection")

jc.add_incoming_road_circular_geometry(
    road_west,  radius=R, angle=math.pi,     road_connection="predecessor")
jc.add_incoming_road_circular_geometry(
    road_east,  radius=R, angle=0,           road_connection="predecessor")
jc.add_incoming_road_circular_geometry(
    road_north, radius=R, angle=math.pi/2,   road_connection="predecessor")
jc.add_incoming_road_circular_geometry(
    road_south, radius=R, angle=3*math.pi/2, road_connection="predecessor")

jc.add_connection(road_west.id,  road_east.id)
jc.add_connection(road_west.id,  road_north.id)
jc.add_connection(road_west.id,  road_south.id)
jc.add_connection(road_east.id,  road_north.id)
jc.add_connection(road_east.id,  road_south.id)
jc.add_connection(road_north.id, road_south.id)

junction       = jc.junction
junction_roads = jc.junction_roads

# ==============================================================================
# ZONE A — Connector arc + Highway straight
#
# road_west starts at (-R, 0) heading West (pi rad) and extends 200 m.
# road_west end = (-220, 0)
#
# Connector arc: radius 200 m, curvature=1/200, length=150 m
#   Starts at road_west end (-220, 0), same heading pi.
#   Curves gently upward (positive curvature = left = northward).
#   End position calculated: (-356, -54), heading 223 deg.
#   We attach it by setting its start point to road_west's end.
#
# Highway: 800 m straight, starts where connector ends.
#   Heading continues from connector end (223 deg).
#
# No successor/predecessor needed — set_start_point places them directly.
# We still set successor/predecessor so esmini knows vehicles can drive
# from highway through connector into the junction network.
# ==============================================================================
print("Building connector arc and highway...")

# Connector arc
# Starts at road_west end: (-220, 0), heading pi (West)
CONN_START_X   = -R - 200.0          # = -220.0
CONN_START_Y   = 0.0
CONN_START_HDG = math.pi

road_connector = xodr.create_road(
    geometry=xodr.Arc(curvature=1/200, length=150),
    id=2, left_lanes=2, right_lanes=2, lane_width=3.5)
road_connector.add_type(xodr.RoadType.rural, speed=80, speed_unit="km/h")
road_connector.planview.set_start_point(CONN_START_X, CONN_START_Y, CONN_START_HDG)

# Connector end position (calculated):
arc_sweep      = 150 / 200           # radians swept = length / radius
CONN_END_HDG   = CONN_START_HDG + arc_sweep
CONN_END_X     = CONN_START_X + 200 * (math.sin(CONN_END_HDG) - math.sin(CONN_START_HDG))
CONN_END_Y     = CONN_START_Y + 200 * (-math.cos(CONN_END_HDG) + math.cos(CONN_START_HDG))

# Highway straight
# Starts where connector ends, continues same heading
road_highway = xodr.create_road(
    geometry=xodr.Line(800),
    id=1, left_lanes=2, right_lanes=2, lane_width=3.75)
road_highway.add_type(xodr.RoadType.motorway, speed=120, speed_unit="km/h")
road_highway.planview.set_start_point(CONN_END_X, CONN_END_Y, CONN_END_HDG)

# Links for drivability (so vehicles can navigate highway -> junction)
road_highway.add_successor(
    xodr.ElementType.road, 2, xodr.ContactPoint.end)
road_connector.add_successor(
    xodr.ElementType.road, 1, xodr.ContactPoint.end)
road_connector.add_predecessor(
    xodr.ElementType.road, 10, xodr.ContactPoint.end)
road_west.add_successor(
    xodr.ElementType.road, 2, xodr.ContactPoint.start)

# ==============================================================================
# ZONE C — S-curve
#
# road_east starts at (+R, 0) heading East (0 rad) and extends 200 m.
# road_east end = (220, 0), heading 0.
# S-curve starts there.
# ==============================================================================
print("Building S-curve...")

CURVE_START_X   = R + 200.0          # = 220.0
CURVE_START_Y   = 0.0
CURVE_START_HDG = 0.0                # East

road_curve = xodr.create_road(
    geometry=[
        xodr.Line(50),
        xodr.Arc(curvature= 1/100, length=157),
        xodr.Arc(curvature=-1/100, length=157),
        xodr.Line(50)
    ],
    id=20, left_lanes=2, right_lanes=2, lane_width=3.5)
road_curve.add_type(xodr.RoadType.rural, speed=80, speed_unit="km/h")
road_curve.planview.set_start_point(CURVE_START_X, CURVE_START_Y, CURVE_START_HDG)

# Links for drivability
road_curve.add_predecessor(
    xodr.ElementType.road, 11, xodr.ContactPoint.end)
road_east.add_successor(
    xodr.ElementType.road, 20, xodr.ContactPoint.start)

# ==============================================================================
# ASSEMBLE AND WRITE
# All roads have explicit start positions so adjust_roads_and_lanes()
# only needs to propagate lane offsets, not solve geometry placement.
# ==============================================================================
print("Assembling OpenDRIVE network...")

odr = xodr.OpenDrive("adas_network")

odr.add_road(road_highway)
odr.add_road(road_connector)
odr.add_road(road_west)
odr.add_road(road_east)
odr.add_road(road_north)
odr.add_road(road_south)
odr.add_road(road_curve)

for jr in junction_roads:
    odr.add_road(jr)

odr.add_junction(junction)

odr.adjust_roads_and_lanes()

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
odr.write_xml(OUTPUT_PATH)

print(f"\n  Written : {OUTPUT_PATH}")
print("\nValidate in esmini:")
print(f'  C:\\esmini\\bin\\odrviewer.exe --odr "{OUTPUT_PATH}" --window 60 60 1200 600')
