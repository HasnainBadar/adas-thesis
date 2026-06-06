"""
check_alks_decel.py
Reads the 50kph dry CSV and calculates ALKS actual braking deceleration.
This tells us exactly how hard ALKS brakes in esmini so we can
place obstacles correctly for all speeds.

Run: python scripts\check_alks_decel.py
"""
import pandas as pd
import numpy as np
import os

RAW_DIR = r"C:\adas-thesis\results\raw"

def load_csv(path):
    df = pd.read_csv(path, skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    return df

def get_entity(df, name):
    return df[df["name"]==name].reset_index(drop=True)

for fname, spd_kph in [
    ("S1_AEB_dry_50kph.csv", 50),
    ("S1_AEB_dry_80kph.csv", 80),
    ("S1_AEB_dry_120kph.csv", 120),
]:
    path = os.path.join(RAW_DIR, fname)
    if not os.path.exists(path):
        print(f"{fname}: not found")
        continue

    df  = load_csv(path)
    ego = get_entity(df, "Ego")
    times  = ego["time"].values.astype(float)
    speeds = ego["speed"].values.astype(float)
    xs     = ego["x"].values.astype(float)
    ys     = ego["y"].values.astype(float)

    v_init = speeds[0]

    # Find AEB trigger
    trigger_idx = next((i for i in range(1,len(speeds))
                        if speeds[i] < v_init - 0.5), None)
    if trigger_idx is None:
        print(f"{fname}: AEB never fired")
        continue

    # Find minimum speed
    post      = speeds[trigger_idx:]
    min_idx   = trigger_idx + int(np.argmin(post))
    min_speed = speeds[min_idx]

    # Deceleration = change in speed / change in time from trigger to min
    dt = times[min_idx] - times[trigger_idx]
    dv = speeds[trigger_idx] - min_speed
    decel = dv / dt if dt > 0 else 0

    # Distance from trigger to min
    dx = xs[min_idx] - xs[trigger_idx]
    dy = ys[min_idx] - ys[trigger_idx]
    dist = np.sqrt(dx**2 + dy**2)

    # Obstacle position
    obs = get_entity(df, "Obstacle")
    obs_x = obs["x"].iloc[0] if not obs.empty else None
    obs_y = obs["y"].iloc[0] if not obs.empty else None

    # Gap between ego at trigger and obstacle
    if obs_x is not None:
        gap_at_trigger = np.sqrt(
            (xs[trigger_idx]-obs_x)**2 +
            (ys[trigger_idx]-obs_y)**2
        ) - 4.5

    # Theoretical stopping dist from trigger speed
    theory_d = speeds[trigger_idx]**2 / (2 * decel) if decel > 0 else 9999

    print(f"\n{'='*55}")
    print(f"File: {fname}  ({spd_kph} kph)")
    print(f"  Initial speed:      {round(v_init*3.6,1)} kph = {round(v_init,3)} m/s")
    print(f"  Speed at trigger:   {round(speeds[trigger_idx]*3.6,1)} kph")
    print(f"  Trigger time:       {times[trigger_idx]}s")
    print(f"  Min speed:          {round(min_speed*3.6,2)} kph at t={times[min_idx]}s")
    print(f"  Brake duration:     {round(dt,3)}s")
    print(f"  Speed change:       {round(dv,3)} m/s")
    print(f"  ALKS avg decel:     {round(decel,3)} m/s²")
    print(f"  Distance braking:   {round(dist,2)}m")
    print(f"  Gap at trigger:     {round(gap_at_trigger,2)}m")
    print(f"  Theory stop dist:   {round(theory_d,2)}m from trigger")
    print(f"  Obstacle position:  x={obs_x}, y={obs_y}")

    # Print speed sequence around trigger
    print(f"  Speed around trigger (idx {trigger_idx-2} to {trigger_idx+5}):")
    for i in range(max(0,trigger_idx-2), min(len(speeds),trigger_idx+8)):
        print(f"    t={times[i]:.2f}s  spd={round(speeds[i]*3.6,2)}kph")

