"""
=============================================================================
ADAS THESIS - SUMO + TraCI + esmini UDP Co-simulation Bridge
Student : HasnainBadar | hasnainbdr@gmail.com
File    : C:\adas-thesis\scripts\sumo_traci_bridge.py

VERIFIED FACTS:
  - esmini ports: NPC_A=49951, NPC_B=49952
  - NPC_A esmini world start: x=-474.68, y=-161.35, hdg=3.89 rad
  - NPC_B esmini world start: x=-418.70, y=-104.08, hdg=3.89 rad
  - SUMO drives vehicles in opposite direction to esmini on edge "1"
    Fix: negate the SUMO displacement delta before applying to esmini pos
  - Vehicles disappear when they reach road end — fix: use road geometry
    to compute position from s-coordinate directly instead of SUMO XY

HOW TO RUN:
  Terminal 1:
    cd C:\esmini
    .\bin\esmini --osc C:\adas-thesis\scenarios\S0_controller_demo\sumo_bridge.xosc --window 60 60 1200 600

  Terminal 2:
    cd C:\adas-thesis
    .venv\Scripts\Activate.ps1
    python scripts\sumo_traci_bridge.py

  Drive Ego with arrow keys. Ctrl+C to stop.
=============================================================================
"""

import socket
import struct
import time
import sys
import os
import math
import subprocess
import traci
import traci.constants as tc

# ── CONFIGURATION ─────────────────────────────────────────────────────────────

SUMO_EXE    = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"
CFG_FILE    = r"C:\adas-thesis\maps\adas_network.sumocfg"
NET_FILE    = r"C:\adas-thesis\maps\adas_network.net.xml"
ROU_FILE    = r"C:\adas-thesis\maps\adas_network.rou.xml"

TRACI_PORT  = 8813
ESMINI_HOST = "127.0.0.1"
PORT_NPC_A  = 49951
PORT_NPC_B  = 49952
TIMESTEP    = 0.05

# Road 1 geometry — verified from esmini log
# NPC_A at s=160, laneId=-1 -> x=-474.68, y=-161.35, hdg=3.89
ROAD1_X0  = -356.3277520046668
ROAD1_Y0  = -53.66222622523582
ROAD1_HDG = 3.891592653589793
ROAD1_LEN = 796.0
LANE_W    = 3.75

# Verified esmini world positions at start
NPC_A_START_X = -474.68
NPC_A_START_Y = -161.35
NPC_A_LANE    = -1      # laneId
NPC_A_START_S = 160.0

NPC_B_START_X = -418.70
NPC_B_START_Y = -104.08
NPC_B_LANE    = -2      # laneId
NPC_B_START_S = 80.0


def s_to_world(s, lane_id):
    """
    Convert road s-coordinate + laneId to world XY.
    This is the ground truth — matches esmini's road geometry exactly.
    laneId -1: 1.875m right of centreline
    laneId -2: 5.625m right of centreline
    """
    dx = math.cos(ROAD1_HDG)
    dy = math.sin(ROAD1_HDG)
    px = math.cos(ROAD1_HDG - math.pi / 2)
    py = math.sin(ROAD1_HDG - math.pi / 2)
    t  = abs(lane_id) * LANE_W - LANE_W / 2   # 1.875 for -1, 5.625 for -2
    x  = ROAD1_X0 + s * dx + t * px
    y  = ROAD1_Y0 + s * dy + t * py
    return x, y


def pack_stateXYH(object_id, frame_nr, x, y, heading_rad, speed_ms):
    """
    Verified packet format from esmini udp_osi_common.py.
    mode 3 = stateXYH
    """
    return struct.pack('iiiidddddB',
        1,           # version
        3,           # inputMode = stateXYH
        object_id,
        frame_nr,
        float(x),
        float(y),
        float(heading_rad),
        float(speed_ms),
        0.0,         # wheelAngle
        1            # deadReckon
    )


def main():
    print("=" * 60)
    print(" ADAS Thesis - SUMO + TraCI + esmini UDP Bridge")
    print("=" * 60)
    print()

    # Verify files
    for f in [NET_FILE, ROU_FILE, CFG_FILE]:
        if not os.path.exists(f):
            print(f"ERROR: Missing {f}")
            sys.exit(1)
        print(f"  OK  {f}")
    print()

    # Launch SUMO
    print("Starting SUMO...")
    sumo_proc = subprocess.Popen(
        [SUMO_EXE, "-c", CFG_FILE,
         "--remote-port", str(TRACI_PORT),
         "--step-length",  str(TIMESTEP),
         "--no-step-log", "--no-warnings",
         "--collision.action", "warn",
         "--time-to-teleport", "-1"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    time.sleep(2.5)
    if sumo_proc.poll() is not None:
        print("ERROR: SUMO exited immediately.")
        sys.exit(1)
    print(f"  SUMO PID {sumo_proc.pid}")

    # Connect TraCI
    print("Connecting TraCI...")
    try:
        traci.init(port=TRACI_PORT)
    except Exception as e:
        print(f"ERROR: {e}")
        sumo_proc.terminate()
        sys.exit(1)
    print("  Connected.")
    print()

    # Wait for vehicles to depart and get their SUMO starting s-coordinate
    print("Waiting for vehicles...")
    subscribed = set()
    WATCH = [tc.VAR_LANEPOSITION, tc.VAR_SPEED, tc.VAR_ANGLE, tc.VAR_LANE_INDEX]

    # Subscribe to lane position (s along edge) instead of XY
    # This avoids coordinate system confusion entirely
    for _ in range(100):
        traci.simulationStep()
        for vid in traci.simulation.getDepartedIDList():
            if vid in ("NPC_A", "NPC_B") and vid not in subscribed:
                traci.vehicle.subscribe(vid, WATCH)
                subscribed.add(vid)
                print(f"  {vid} departed")
        if "NPC_A" in subscribed and "NPC_B" in subscribed:
            break

    print(f"  Active: {list(traci.vehicle.getIDList())}")
    print()

    # Get SUMO starting s-positions
    npc_a_sumo_s0 = None
    npc_b_sumo_s0 = None
    if "NPC_A" in subscribed:
        r = traci.vehicle.getSubscriptionResults("NPC_A")
        if r:
            npc_a_sumo_s0 = r.get(tc.VAR_LANEPOSITION, NPC_A_START_S)
    if "NPC_B" in subscribed:
        r = traci.vehicle.getSubscriptionResults("NPC_B")
        if r:
            npc_b_sumo_s0 = r.get(tc.VAR_LANEPOSITION, NPC_B_START_S)

    print(f"  NPC_A SUMO start s: {npc_a_sumo_s0:.1f}")
    print(f"  NPC_B SUMO start s: {npc_b_sumo_s0:.1f}")
    print()

    # UDP sockets
    sock_a = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    frame_a = 0
    frame_b = 0

    print("Bridge running. Drive Ego in esmini (arrow keys). Ctrl+C to stop.")
    print()
    print(f"{'Step':>6}  {'A_s':>7}  {'A_kph':>6}  {'B_s':>7}  {'B_kph':>6}")
    print("-" * 42)

    step = 0

    try:
        while True:
            t0 = time.perf_counter()

            traci.simulationStep()

            # Check for new departures (respawns from flow)
            for vid in traci.simulation.getDepartedIDList():
                if vid in ("NPC_A", "NPC_B") and vid not in subscribed:
                    traci.vehicle.subscribe(vid, WATCH)
                    subscribed.add(vid)

            # ── NPC_A ─────────────────────────────────────────────────────
            a_s_display, a_kph = 0.0, 0.0
            if "NPC_A" in subscribed:
                r = traci.vehicle.getSubscriptionResults("NPC_A")
                if r and tc.VAR_LANEPOSITION in r:
                    sumo_s = r[tc.VAR_LANEPOSITION]
                    spd    = r[tc.VAR_SPEED]

                    # SUMO drives edge "1" in opposite direction to esmini.
                    # SUMO s increases as vehicle moves away from esmini start.
                    # esmini s increases as vehicle moves toward road end.
                    # Fix: esmini_s = start_s - (sumo_s - sumo_s0)
                    delta_s = sumo_s - npc_a_sumo_s0
                    esmini_s = NPC_A_START_S + delta_s

                    # Wrap around if vehicle goes off end of road
                    esmini_s = esmini_s % ROAD1_LEN

                    wx, wy = s_to_world(esmini_s, NPC_A_LANE)
                    pkt = pack_stateXYH(0, frame_a, wx, wy, ROAD1_HDG, spd)
                    sock_a.sendto(pkt, (ESMINI_HOST, PORT_NPC_A))
                    frame_a   += 1
                    a_s_display = esmini_s
                    a_kph       = spd * 3.6

            # ── NPC_B ─────────────────────────────────────────────────────
            b_s_display, b_kph = 0.0, 0.0
            if "NPC_B" in subscribed:
                r = traci.vehicle.getSubscriptionResults("NPC_B")
                if r and tc.VAR_LANEPOSITION in r:
                    sumo_s = r[tc.VAR_LANEPOSITION]
                    spd    = r[tc.VAR_SPEED]

                    delta_s  = sumo_s - npc_b_sumo_s0
                    esmini_s = NPC_B_START_S + delta_s
                    esmini_s = esmini_s % ROAD1_LEN

                    wx, wy = s_to_world(esmini_s, NPC_B_LANE)
                    pkt = pack_stateXYH(1, frame_b, wx, wy, ROAD1_HDG, spd)
                    sock_b.sendto(pkt, (ESMINI_HOST, PORT_NPC_B))
                    frame_b   += 1
                    b_s_display = esmini_s
                    b_kph       = spd * 3.6

            if step % 40 == 0:
                print(f"{step:6d}  {a_s_display:7.1f}  {a_kph:6.1f}  "
                      f"{b_s_display:7.1f}  {b_kph:6.1f}")

            step += 1

            elapsed = time.perf_counter() - t0
            wait    = TIMESTEP - elapsed
            if wait > 0:
                time.sleep(wait)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        try: traci.close()
        except Exception: pass
        try: sumo_proc.terminate(); sumo_proc.wait(timeout=3)
        except Exception: pass
        print("Done. Press ESC in esmini to close it.")
        sys.exit(0)


if __name__ == "__main__":
    main()
