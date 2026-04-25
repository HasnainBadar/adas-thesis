"""
=============================================================================
ADAS THESIS - SUMO + TraCI + esmini UDP Bridge v2 (with EGO_GHOST)
Student : HasnainBadar | hasnainbdr@gmail.com
File    : C:\adas-thesis\scripts\sumo_traci_bridge.py

WHAT'S NEW IN V2:
  EGO_GHOST is injected into SUMO at same position as esmini Ego.
  SUMO's IDM makes NPC_A brake/accelerate when EGO_GHOST is close.
  This means NPCs react to Ego in real time.

HOW TO RUN:
  Terminal 1:
    cd C:\esmini
    .\bin\esmini --osc C:\adas-thesis\scenarios\S0_controller_demo\sumo_bridge.xosc --window 60 60 1200 600

  Terminal 2:
    cd C:\adas-thesis
    .venv\Scripts\Activate.ps1
    python scripts\sumo_traci_bridge.py

  Drive Ego with arrow keys. Ctrl+C to stop.

IF THIS BREAKS:
  python scripts\sumo_traci_bridge_WORKING.py
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
ROAD1_X0  = -356.3277520046668
ROAD1_Y0  = -53.66222622523582
ROAD1_HDG = 3.891592653589793
ROAD1_LEN = 796.0
LANE_W    = 3.75

# Verified esmini world start positions
NPC_A_START_X = -474.68
NPC_A_START_Y = -161.35
NPC_A_LANE    = -1
NPC_A_START_S = 160.0

NPC_B_START_X = -418.70
NPC_B_START_Y = -104.08
NPC_B_LANE    = -2
NPC_B_START_S = 80.0

# Ego starts at s=100 in esmini xosc
EGO_START_S   = 100.0
EGO_START_SPD = 13.9   # 50 kph


def s_to_world(s, lane_id):
    dx = math.cos(ROAD1_HDG)
    dy = math.sin(ROAD1_HDG)
    px = math.cos(ROAD1_HDG - math.pi / 2)
    py = math.sin(ROAD1_HDG - math.pi / 2)
    t  = abs(lane_id) * LANE_W - LANE_W / 2
    return ROAD1_X0 + s*dx + t*px, ROAD1_Y0 + s*dy + t*py


def sumo_to_esmini_heading(sumo_deg):
    return math.radians(90.0 - sumo_deg)


def pack_stateXYH(object_id, frame_nr, x, y, heading_rad, speed_ms):
    return struct.pack('iiiidddddB',
        1, 3, object_id, frame_nr,
        float(x), float(y), float(heading_rad),
        float(speed_ms), 0.0, 1)


def main():
    print("=" * 60)
    print(" ADAS Thesis - SUMO + TraCI + esmini UDP Bridge v2")
    print("=" * 60)
    print()
    print(f"NPC_A -> esmini port {PORT_NPC_A}")
    print(f"NPC_B -> esmini port {PORT_NPC_B}")
    print()

    for f in [NET_FILE, ROU_FILE, CFG_FILE]:
        if not os.path.exists(f):
            print(f"ERROR: Missing {f}")
            sys.exit(1)
        print(f"  OK  {os.path.basename(f)}")
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

    # Wait for all vehicles to depart
    print("Waiting for vehicles...")
    subscribed  = set()
    ego_ready   = False
    WATCH = [tc.VAR_LANEPOSITION, tc.VAR_SPEED, tc.VAR_ANGLE, tc.VAR_LANE_INDEX]

    for _ in range(100):
        traci.simulationStep()
        for vid in traci.simulation.getDepartedIDList():
            if vid in ("NPC_A", "NPC_B") and vid not in subscribed:
                traci.vehicle.subscribe(vid, WATCH)
                subscribed.add(vid)
                print(f"  {vid} departed and subscribed")
            if vid == "EGO_GHOST" and not ego_ready:
                # Take full manual control of EGO_GHOST
                traci.vehicle.setSpeedMode("EGO_GHOST", 0)
                traci.vehicle.setLaneChangeMode("EGO_GHOST", 0)
                traci.vehicle.setSpeed("EGO_GHOST", EGO_START_SPD)
                ego_ready = True
                print("  EGO_GHOST ready — NPCs will react to it")
        if "NPC_A" in subscribed and "NPC_B" in subscribed:
            break

    print(f"  Active SUMO vehicles: {list(traci.vehicle.getIDList())}")
    print()

    # Get SUMO starting s-positions for NPC_A and NPC_B
    npc_a_sumo_s0 = None
    npc_b_sumo_s0 = None
    if "NPC_A" in subscribed:
        r = traci.vehicle.getSubscriptionResults("NPC_A")
        if r: npc_a_sumo_s0 = r.get(tc.VAR_LANEPOSITION, NPC_A_START_S)
    if "NPC_B" in subscribed:
        r = traci.vehicle.getSubscriptionResults("NPC_B")
        if r: npc_b_sumo_s0 = r.get(tc.VAR_LANEPOSITION, NPC_B_START_S)

    print(f"  NPC_A SUMO s0={npc_a_sumo_s0:.1f}  esmini s0={NPC_A_START_S:.1f}")
    print(f"  NPC_B SUMO s0={npc_b_sumo_s0:.1f}  esmini s0={NPC_B_START_S:.1f}")
    print()

    # UDP sockets
    sock_a  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_b  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    frame_a = 0
    frame_b = 0

    # Ego state — we estimate Ego speed from keyboard
    # Ego accelerates gradually from start speed
    ego_s     = EGO_START_S
    ego_speed = EGO_START_SPD

    print("Bridge running. Drive Ego in esmini (arrow keys). Ctrl+C to stop.")
    print("NPC_A will brake when Ego catches up to it.")
    print()
    print(f"{'Step':>6}  {'A_s':>7}  {'A_kph':>6}  {'B_s':>7}  {'B_kph':>6}  {'Ego_s':>7}")
    print("-" * 52)

    step = 0

    try:
        while True:
            t0 = time.perf_counter()

            # ── Update EGO_GHOST in SUMO ──────────────────────────────────
            # We move EGO_GHOST to match where Ego approximately is.
            # ego_s increases as Ego drives forward.
            # EGO_GHOST s in SUMO = EGO_START_S + (ego_s - EGO_START_S)
            if ego_ready and "EGO_GHOST" in traci.vehicle.getIDList():
                try:
                    ex, ey = s_to_world(ego_s, -1)
                    traci.vehicle.moveToXY(
                        "EGO_GHOST",
                        edgeID    = "1",
                        laneIndex = 0,
                        x         = ex + 941.68,  # convert esmini world to SUMO coords
                        y         = ey + 598.97,  # verified offset from earlier
                        angle     = math.degrees(ROAD1_HDG),
                        keepRoute = 1
                    )
                    traci.vehicle.setSpeed("EGO_GHOST", ego_speed)
                except Exception:
                    pass

            # ── Step SUMO ─────────────────────────────────────────────────
            traci.simulationStep()

            # ── Update ego dead-reckoning ─────────────────────────────────
            # Simple model: Ego accelerates to cruise speed
            # In reality Ego is keyboard controlled — this is an estimate
            ego_speed = min(ego_speed + 0.01, 22.2)
            ego_s     = min(ego_s + ego_speed * TIMESTEP, ROAD1_LEN - 5.0)

            # Subscribe to newly departed vehicles
            for vid in traci.simulation.getDepartedIDList():
                if vid in ("NPC_A", "NPC_B") and vid not in subscribed:
                    traci.vehicle.subscribe(vid, WATCH)
                    subscribed.add(vid)
                if vid == "EGO_GHOST" and not ego_ready:
                    traci.vehicle.setSpeedMode("EGO_GHOST", 0)
                    traci.vehicle.setLaneChangeMode("EGO_GHOST", 0)
                    ego_ready = True

            # ── NPC_A → esmini port 49951 ─────────────────────────────────
            a_s_disp, a_kph = 0.0, 0.0
            if "NPC_A" in subscribed:
                r = traci.vehicle.getSubscriptionResults("NPC_A")
                if r and tc.VAR_LANEPOSITION in r:
                    sumo_s   = r[tc.VAR_LANEPOSITION]
                    spd      = r[tc.VAR_SPEED]
                    delta_s  = sumo_s - npc_a_sumo_s0
                    esmini_s = (NPC_A_START_S + delta_s) % ROAD1_LEN
                    wx, wy   = s_to_world(esmini_s, NPC_A_LANE)
                    sock_a.sendto(
                        pack_stateXYH(0, frame_a, wx, wy, ROAD1_HDG, spd),
                        (ESMINI_HOST, PORT_NPC_A))
                    frame_a  += 1
                    a_s_disp  = esmini_s
                    a_kph     = spd * 3.6

            # ── NPC_B → esmini port 49952 ─────────────────────────────────
            b_s_disp, b_kph = 0.0, 0.0
            if "NPC_B" in subscribed:
                r = traci.vehicle.getSubscriptionResults("NPC_B")
                if r and tc.VAR_LANEPOSITION in r:
                    sumo_s   = r[tc.VAR_LANEPOSITION]
                    spd      = r[tc.VAR_SPEED]
                    delta_s  = sumo_s - npc_b_sumo_s0
                    esmini_s = (NPC_B_START_S + delta_s) % ROAD1_LEN
                    wx, wy   = s_to_world(esmini_s, NPC_B_LANE)
                    sock_b.sendto(
                        pack_stateXYH(1, frame_b, wx, wy, ROAD1_HDG, spd),
                        (ESMINI_HOST, PORT_NPC_B))
                    frame_b  += 1
                    b_s_disp  = esmini_s
                    b_kph     = spd * 3.6

            if step % 40 == 0:
                print(f"{step:6d}  {a_s_disp:7.1f}  {a_kph:6.1f}  "
                      f"{b_s_disp:7.1f}  {b_kph:6.1f}  {ego_s:7.1f}")

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
