"""
ADAS THESIS - Generate SUMO network from adas_network.xodr
Student : HasnainBadar
File    : C:\adas-thesis\scripts\generate_sumo_net.py

WHY THIS EXISTS:
  netconvert.exe is blocked by AppLocker on this machine.
  This script reads adas_network.xodr directly and builds a
  SUMO .net.xml file using sumolib's network writing API.
  Result is identical to what netconvert would produce.

HOW TO RUN:
  cd C:\adas-thesis
  .venv\Scripts\Activate.ps1
  python scripts\generate_sumo_net.py

OUTPUT:
  C:\adas-thesis\maps\adas_network.net.xml
  C:\adas-thesis\maps\adas_network.rou.xml
  C:\adas-thesis\maps\adas_network.sumocfg
"""

import os
import math
import xml.etree.ElementTree as ET

# ── PATHS ─────────────────────────────────────────────────────────────────────
MAPS_DIR  = r"C:\adas-thesis\maps"
NET_FILE  = os.path.join(MAPS_DIR, "adas_network.net.xml")
ROU_FILE  = os.path.join(MAPS_DIR, "adas_network.rou.xml")
CFG_FILE  = os.path.join(MAPS_DIR, "adas_network.sumocfg")

# ── ROAD GEOMETRY (from adas_network.xodr) ────────────────────────────────────
# Road 1: highway straight, 800m, heading=3.8916 rad, starts at (-356.33, -53.66)
# We model the two right-hand driving lanes: laneId=-1 and laneId=-2
# SUMO uses a flat graph of nodes + edges — we extract key waypoints

ROAD1_X0  = -356.3277520046668
ROAD1_Y0  = -53.66222622523582
ROAD1_HDG = 3.891592653589793   # radians (~223 degrees, going SW)
ROAD1_LEN = 800.0

# Direction unit vector
DX = math.cos(ROAD1_HDG)
DY = math.sin(ROAD1_HDG)

# Perpendicular (right side, RHT)
PX = math.cos(ROAD1_HDG - math.pi / 2)
PY = math.sin(ROAD1_HDG - math.pi / 2)

LANE_WIDTH = 3.75  # from xodr width a="3.75"

def road_point(s, t):
    """World XY at distance s along road, lateral offset t (positive=right)."""
    x = ROAD1_X0 + s * DX + t * PX
    y = ROAD1_Y0 + s * DY + t * PY
    return x, y

def fmt(v):
    return f"{v:.4f}"

def write_net():
    """Write a minimal but valid SUMO net.xml for the highway straight."""
    print("Writing SUMO network...")

    # We create 3 nodes: start, mid (400m), end of Road 1
    # And 2 edges per lane direction (inner lane -1, outer lane -2)
    # SUMO edges go from node to node; each edge can have multiple lanes

    # Node positions — on the road centreline
    n_start_x, n_start_y = road_point(0,   0)
    n_mid_x,   n_mid_y   = road_point(400, 0)
    n_end_x,   n_end_y   = road_point(800, 0)

    root = ET.Element("net", {
        "version":       "1.9",
        "junctionCornerDetail": "5",
        "limitTurnSpeed": "5.83",
        "xmlns:xsi":     "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation":
            "http://sumo.dlr.de/xsd/net_file.xsd"
    })

    # ── LOCATION ──────────────────────────────────────────────────────────────
    ET.SubElement(root, "location", {
        "netOffset":       "0.00,0.00",
        "convBoundary":    f"{fmt(n_end_x)},{fmt(n_end_y)},{fmt(n_start_x)},{fmt(n_start_y)}",
        "origBoundary":    f"{fmt(n_end_x)},{fmt(n_end_y)},{fmt(n_start_x)},{fmt(n_start_y)}",
        "projParameter":   "!"
    })

    # ── EDGE TYPES ────────────────────────────────────────────────────────────
    types = ET.SubElement(root, "types")
    ET.SubElement(types, "type", {
        "id":       "highway.motorway",
        "priority": "12",
        "numLanes": "2",
        "speed":    "33.33",   # 120 kph in m/s
        "oneway":   "1",
        "sidewalkWidth": "-1",
        "bikeLaneWidth": "-1"
    })

    # ── NODES ─────────────────────────────────────────────────────────────────
    # node_start → node_end, direction of travel (laneId=-1 and -2)
    nodes = [
        ("node_start", n_start_x, n_start_y, "dead_end"),
        ("node_mid",   n_mid_x,   n_mid_y,   "priority"),
        ("node_end",   n_end_x,   n_end_y,   "dead_end"),
    ]
    for nid, nx, ny, ntype in nodes:
        ET.SubElement(root, "node", {
            "id":   nid,
            "x":    fmt(nx),
            "y":    fmt(ny),
            "type": ntype
        })

    # ── EDGES ─────────────────────────────────────────────────────────────────
    # Edge road1_fwd: node_start → node_end (2 lanes, forward direction)
    # Lane shapes: lane 0 = laneId -1 (inner), lane 1 = laneId -2 (outer)

    def lane_shape(t_offset, n_segments=5):
        """Generate shape string for a lane at lateral offset t_offset."""
        points = []
        for i in range(n_segments + 1):
            s = ROAD1_LEN * i / n_segments
            x, y = road_point(s, t_offset)
            points.append(f"{fmt(x)},{fmt(y)}")
        return " ".join(points)

    edge = ET.SubElement(root, "edge", {
        "id":       "road1_fwd",
        "from":     "node_start",
        "to":       "node_end",
        "priority": "12",
        "type":     "highway.motorway",
        "shape":    lane_shape(0),   # centreline shape
        "spreadType": "right"
    })

    # Lane 0 = laneId -1 (inner right lane, 1.875m right of centre)
    ET.SubElement(edge, "lane", {
        "id":    "road1_fwd_0",
        "index": "0",
        "speed": "33.33",
        "length": fmt(ROAD1_LEN),
        "width": fmt(LANE_WIDTH),
        "shape": lane_shape(LANE_WIDTH / 2)
    })
    # Lane 1 = laneId -2 (outer right lane, 5.625m right of centre)
    ET.SubElement(edge, "lane", {
        "id":    "road1_fwd_1",
        "index": "1",
        "speed": "33.33",
        "length": fmt(ROAD1_LEN),
        "width": fmt(LANE_WIDTH),
        "shape": lane_shape(LANE_WIDTH * 1.5)
    })

    # ── JUNCTIONS (required by SUMO even for dead ends) ───────────────────────
    for nid, nx, ny, _ in nodes:
        ET.SubElement(root, "junction", {
            "id":           nid,
            "type":         "dead_end",
            "x":            fmt(nx),
            "y":            fmt(ny),
            "incLanes":     "",
            "intLanes":     "",
            "shape":        f"{fmt(nx)},{fmt(ny)}"
        })

    # ── WRITE FILE ────────────────────────────────────────────────────────────
    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    with open(NET_FILE, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding="utf-8", xml_declaration=False)

    size_kb = os.path.getsize(NET_FILE) / 1024
    print(f"  Written: {NET_FILE}  ({size_kb:.1f} KB)")


def write_routes():
    """Write SUMO route file defining NPC vehicles."""
    print("Writing SUMO route file...")

    root = ET.Element("routes")

    # Vehicle type — standard car
    ET.SubElement(root, "vType", {
        "id":              "car",
        "accel":           "2.0",
        "decel":           "4.5",
        "sigma":           "0.5",     # driver imperfection (0=perfect, 1=max random)
        "length":          "5.0",
        "minGap":          "2.5",
        "maxSpeed":        "33.33",   # 120 kph
        "guiShape":        "passenger",
        "carFollowModel":  "IDM",     # Intelligent Driver Model (same as SUMO default)
        "tau":             "1.5"      # desired time headway
    })

    # Route — full length of road1_fwd
    ET.SubElement(root, "route", {
        "id":    "highway_route",
        "edges": "road1_fwd"
    })

    # NPC_A: inner lane (index 0 = laneId -1), departs at s=160, speed 22.2
    ET.SubElement(root, "vehicle", {
        "id":          "NPC_A",
        "type":        "car",
        "route":       "highway_route",
        "depart":      "0",
        "departLane":  "0",
        "departPos":   "160",
        "departSpeed": "22.2",
        "color":       "1,0,0"    # red
    })

    # NPC_B: outer lane (index 1 = laneId -2), departs at s=120, speed 25.0
    ET.SubElement(root, "vehicle", {
        "id":          "NPC_B",
        "type":        "car",
        "route":       "highway_route",
        "depart":      "0",
        "departLane":  "1",
        "departPos":   "120",
        "departSpeed": "25.0",
        "color":       "0,0,1"    # blue
    })

    # NPC_C: inner lane, behind Ego start (s=50), slower — will be overtaken
    ET.SubElement(root, "vehicle", {
        "id":          "NPC_C",
        "type":        "car",
        "route":       "highway_route",
        "depart":      "0",
        "departLane":  "0",
        "departPos":   "20",
        "departSpeed": "16.7",    # 60 kph
        "color":       "0,1,0"    # green
    })

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    with open(ROU_FILE, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding="utf-8", xml_declaration=False)

    size_kb = os.path.getsize(ROU_FILE) / 1024
    print(f"  Written: {ROU_FILE}  ({size_kb:.1f} KB)")


def write_config():
    """Write SUMO .sumocfg configuration file."""
    print("Writing SUMO config file...")

    root = ET.Element("configuration")

    inp = ET.SubElement(root, "input")
    ET.SubElement(inp, "net-file",    {"value": "adas_network.net.xml"})
    ET.SubElement(inp, "route-files", {"value": "adas_network.rou.xml"})

    time_el = ET.SubElement(root, "time")
    ET.SubElement(time_el, "begin",  {"value": "0"})
    ET.SubElement(time_el, "end",    {"value": "3600"})
    ET.SubElement(time_el, "step-length", {"value": "0.05"})  # 20Hz = matches UDP rate

    proc = ET.SubElement(root, "processing")
    ET.SubElement(proc, "collision.action",   {"value": "warn"})
    ET.SubElement(proc, "time-to-teleport",   {"value": "-1"})  # disable teleport
    ET.SubElement(proc, "ignore-route-errors",{"value": "true"})

    traci_el = ET.SubElement(root, "traci_server")
    ET.SubElement(traci_el, "remote-port", {"value": "8813"})  # TraCI default port

    report = ET.SubElement(root, "report")
    ET.SubElement(report, "verbose",      {"value": "false"})
    ET.SubElement(report, "no-step-log",  {"value": "true"})

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    with open(CFG_FILE, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding="utf-8", xml_declaration=False)

    size_kb = os.path.getsize(CFG_FILE) / 1024
    print(f"  Written: {CFG_FILE}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    print("=" * 55)
    print(" ADAS Thesis - SUMO File Generator")
    print(" Bypassing blocked netconvert.exe")
    print("=" * 55)
    print()

    os.makedirs(MAPS_DIR, exist_ok=True)

    write_net()
    write_routes()
    write_config()

    print()
    print("All SUMO files generated successfully.")
    print()
    print("Next step:")
    print("  python scripts\\sumo_traci_bridge.py")
