import os
import math
from scenariogeneration import xodr

OUTPUT_PATH = r"C:\adas-thesis\maps\adas_network.xodr"

odr = xodr.OpenDrive("adas_network")

JX, JY, R = 0.0, 0.0, 20.0

# --- helpers ---

def urban_road(rid, length, hdg, sx, sy, speed=50, lanes=2, width=3.5):
    r = xodr.create_road(
        geometry=xodr.Line(length),
        id=rid, left_lanes=lanes, right_lanes=lanes, lane_width=width)
    r.add_type(xodr.RoadType.town, speed=speed, speed_unit="km/h")
    r.planview.set_start_point(sx, sy, hdg)
    return r

def add_crosswalk(road, s_pos):
    road.add_object(xodr.Object(
        s=s_pos, t=0,
        Type=xodr.ObjectType.crosswalk,
        name=f"cw_{road.id}_{int(s_pos)}",
        orientation=xodr.Orientation.none,
        length=3.0, width=14.0, height=0.01))

def make_junction(jid, name, roads_angles, r=15, startnum=100):
    # roads_angles: list of (road, angle) or (road, angle, connection_type)
    # connection_type defaults to "predecessor"
    jc = xodr.CommonJunctionCreator(id=jid, name=name, startnum=startnum)
    for entry in roads_angles:
        road, angle = entry[0], entry[1]
        conn = entry[2] if len(entry) == 3 else "predecessor"
        jc.add_incoming_road_circular_geometry(
            road, radius=r, angle=angle, road_connection=conn)
    ids = [entry[0].id for entry in roads_angles]
    for i in range(len(ids)):
        for j in range(i+1, len(ids)):
            jc.add_connection(ids[i], ids[j])
    return jc.junction, jc.junction_roads

# --- highway and connector ---

CONN_START_X   = -R - 200.0
CONN_START_Y   = 0.0
CONN_START_HDG = math.pi
arc_sweep       = 150 / 200
CONN_END_HDG   = CONN_START_HDG + arc_sweep
CONN_END_X     = CONN_START_X + 200*(math.sin(CONN_END_HDG) - math.sin(CONN_START_HDG))
CONN_END_Y     = CONN_START_Y + 200*(-math.cos(CONN_END_HDG) + math.cos(CONN_START_HDG))

road_connector = xodr.create_road(
    geometry=xodr.Arc(curvature=1/200, length=150),
    id=2, left_lanes=2, right_lanes=2, lane_width=3.5)
road_connector.add_type(xodr.RoadType.rural, speed=80, speed_unit="km/h")
road_connector.planview.set_start_point(CONN_START_X, CONN_START_Y, CONN_START_HDG)

road_highway = xodr.create_road(
    geometry=xodr.Line(800),
    id=1, left_lanes=2, right_lanes=2, lane_width=3.75)
road_highway.add_type(xodr.RoadType.motorway, speed=120, speed_unit="km/h")
road_highway.planview.set_start_point(CONN_END_X, CONN_END_Y, CONN_END_HDG)

road_highway.add_successor(xodr.ElementType.road, 2, xodr.ContactPoint.start)
road_connector.add_predecessor(xodr.ElementType.road, 1, xodr.ContactPoint.end)
road_connector.add_successor(xodr.ElementType.road, 10, xodr.ContactPoint.end)

# --- urban junction arms ---

road_west = xodr.create_road(
    geometry=xodr.Line(200), id=10, left_lanes=2, right_lanes=2, lane_width=3.5)
road_west.add_type(xodr.RoadType.town, speed=50, speed_unit="km/h")

road_east = xodr.create_road(
    geometry=xodr.Line(200), id=11, left_lanes=2, right_lanes=2, lane_width=3.5)
road_east.add_type(xodr.RoadType.town, speed=50, speed_unit="km/h")

road_north = xodr.create_road(
    geometry=xodr.Line(150), id=12, left_lanes=2, right_lanes=2, lane_width=3.5)
road_north.add_type(xodr.RoadType.town, speed=50, speed_unit="km/h")
road_north.add_signal(xodr.Signal(
    s=145, t=-3.5, country="DE", Type="1000001", subtype="10",
    name="tl_main", dynamic=xodr.Dynamic.yes,
    orientation=xodr.Orientation.positive, zOffset=1.5))

road_south = xodr.create_road(
    geometry=xodr.Line(150), id=13, left_lanes=2, right_lanes=2, lane_width=3.5)
road_south.add_type(xodr.RoadType.town, speed=50, speed_unit="km/h")

jc1 = xodr.CommonJunctionCreator(id=1, name="main_junction", startnum=100)
jc1.add_incoming_road_circular_geometry(road_west,  R, math.pi,     "predecessor")
jc1.add_incoming_road_circular_geometry(road_east,  R, 0,           "predecessor")
jc1.add_incoming_road_circular_geometry(road_north, R, math.pi/2,   "predecessor")
jc1.add_incoming_road_circular_geometry(road_south, R, 3*math.pi/2, "predecessor")
jc1.add_connection(road_west.id,  road_east.id)
jc1.add_connection(road_west.id,  road_north.id)
jc1.add_connection(road_west.id,  road_south.id)
jc1.add_connection(road_east.id,  road_north.id)
jc1.add_connection(road_east.id,  road_south.id)
jc1.add_connection(road_north.id, road_south.id)

road_west.add_successor(xodr.ElementType.road, 2, xodr.ContactPoint.end)
road_east.add_successor(xodr.ElementType.road, 20, xodr.ContactPoint.start)
# road_south.successor set automatically by city_N junction creator

# --- s-curve ---

road_curve = xodr.create_road(
    geometry=[xodr.Line(50),
              xodr.Arc(curvature= 1/100, length=157),
              xodr.Arc(curvature=-1/100, length=157),
              xodr.Line(50)],
    id=20, left_lanes=2, right_lanes=2, lane_width=3.5)
road_curve.add_type(xodr.RoadType.rural, speed=80, speed_unit="km/h")
road_curve.planview.set_start_point(R+200.0, 0.0, 0.0)
road_curve.add_predecessor(xodr.ElementType.road, 11, xodr.ContactPoint.start)

# --- city grid ---
# 3x2 block layout south of main junction
# top row y=-170, bottom row y=-250, columns at x=-120, 0, +120
# block size 80m, 1 lane each side, 30 kph

GR = 10
GL = 3.0
SEG = 60      # block segment length = GS(80) - 2*GR(10)
EW_HDG = math.radians(43.0)
NS_HDG = math.radians(133.0)

# coordinates calculated from road_south actual end point (-633.2,-79.2)
ew_n_left  = urban_road(30, SEG, EW_HDG, -705.8, -133.3, speed=30, lanes=1, width=GL)
ew_n_lc    = urban_road(31, SEG, EW_HDG, -691.2, -119.6, speed=30, lanes=1, width=GL)
ew_n_cr    = urban_road(32, SEG, EW_HDG, -632.7,  -65.1, speed=30, lanes=1, width=GL)
ew_n_right = urban_road(33, SEG, EW_HDG, -574.2,  -10.5, speed=30, lanes=1, width=GL)

ew_s_left  = urban_road(34, SEG, EW_HDG, -760.4,  -74.8, speed=30, lanes=1, width=GL)
ew_s_lc    = urban_road(35, SEG, EW_HDG, -745.8,  -61.1, speed=30, lanes=1, width=GL)
ew_s_cr    = urban_road(36, SEG, EW_HDG, -687.3,   -6.6, speed=30, lanes=1, width=GL)
ew_s_right = urban_road(37, SEG, EW_HDG, -628.8,   48.0, speed=30, lanes=1, width=GL)

ns_l_top    = urban_road(40, SEG, NS_HDG, -705.3, -119.1, speed=30, lanes=1, width=GL)
ns_l_bottom = urban_road(41, SEG, NS_HDG, -759.9,  -60.6, speed=30, lanes=1, width=GL)

ns_c_mid    = urban_road(42, SEG, NS_HDG, -646.8,  -64.6, speed=30, lanes=1, width=GL)
ns_c_bottom = urban_road(43, SEG, NS_HDG, -701.4,   -6.1, speed=30, lanes=1, width=GL)

ns_r_top    = urban_road(44, SEG, NS_HDG, -588.3,  -10.0, speed=30, lanes=1, width=GL)
ns_r_bottom = urban_road(45, SEG, NS_HDG, -642.9,   48.5, speed=30, lanes=1, width=GL)

# crosswalks
add_crosswalk(ew_n_lc,  SEG * 0.5)
add_crosswalk(ew_n_cr,  SEG * 0.5)
add_crosswalk(ew_s_lc,  SEG * 0.5)
add_crosswalk(ew_s_cr,  SEG * 0.5)
add_crosswalk(ns_c_mid, SEG * 0.5)

# city junctions
junc_N,  jroads_N  = make_junction(3, "city_N",  [(ew_n_lc, math.pi), (ew_n_cr, 0), (road_south, math.pi/2, "successor"), (ns_c_mid, 3*math.pi/2)], r=GR, startnum=200)
junc_S,  jroads_S  = make_junction(6, "city_S",  [(ew_s_lc, math.pi), (ew_s_cr, 0), (ns_c_mid, math.pi/2, "successor"), (ns_c_bottom, 3*math.pi/2)], r=GR, startnum=300)
junc_NW, jroads_NW = make_junction(2, "city_NW", [(ew_n_left, math.pi), (ew_n_lc, 0, "successor"), (ns_l_top, 3*math.pi/2)], r=GR, startnum=400)
junc_NE, jroads_NE = make_junction(4, "city_NE", [(ew_n_cr, math.pi, "successor"), (ew_n_right, 0), (ns_r_top, 3*math.pi/2)], r=GR, startnum=500)
junc_SW, jroads_SW = make_junction(5, "city_SW", [(ew_s_left, math.pi), (ew_s_lc, 0, "successor"), (ns_l_top, math.pi/2, "successor"), (ns_l_bottom, 3*math.pi/2)], r=GR, startnum=600)
junc_SE, jroads_SE = make_junction(7, "city_SE", [(ew_s_cr, math.pi, "successor"), (ew_s_right, 0), (ns_r_top, math.pi/2, "successor"), (ns_r_bottom, 3*math.pi/2)], r=GR, startnum=700)

# --- assemble ---

for r in [road_highway, road_connector,
          road_west, road_east, road_north, road_south,
          road_curve,
          ew_n_left, ew_n_lc, ew_n_cr, ew_n_right,
          ew_s_left, ew_s_lc, ew_s_cr, ew_s_right,
          ns_l_top, ns_l_bottom,
          ns_c_mid, ns_c_bottom,
          ns_r_top, ns_r_bottom]:
    odr.add_road(r)

for jr in jc1.junction_roads:
    odr.add_road(jr)

for jr in jroads_N + jroads_S + jroads_NW + jroads_NE + jroads_SW + jroads_SE:
    odr.add_road(jr)

odr.add_junction(jc1.junction)
for j in [junc_N, junc_S, junc_NW, junc_NE, junc_SW, junc_SE]:
    odr.add_junction(j)

odr.adjust_roads_and_lanes()

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
odr.write_xml(OUTPUT_PATH)
print(f"written: {OUTPUT_PATH}")
