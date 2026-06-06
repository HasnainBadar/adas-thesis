"""
fix_AEB_scenarios.py
====================
Regenerates AEB scenarios with correct obstacle placement
based on ACTUAL measured ALKS braking performance:
  - ALKS brakes at ~6.0 m/s² at highway speeds
  - TTC trigger fires when gap ≈ v × 3s
  - Obstacle placed at: ego_start + trigger_gap + stop_dist + 30m buffer

Verified obstacle positions:
  50kph  → s_obstacle = 140m  (ego at s=50)
  80kph  → s_obstacle = 190m  (ego at s=50)
  120kph → s_obstacle = 275m  (ego at s=50)

At 120kph ALKS needs 92.6m to stop but has ~125m gap at trigger → SAFE
At 80kph  ALKS needs 41.2m to stop but has ~90m  gap at trigger → SAFE
At 50kph  gentle braking, plenty of room                        → SAFE

Run: python scripts\\fix_AEB_scenarios.py
"""

import os, math

ALKS_DECEL   = 6.0    # m/s² — measured from actual simulation
TTC_TRIGGER  = 3.0    # seconds — ALKS TTC threshold
BUFFER       = 30.0   # m — extra safety margin
S_EGO        = 50.0   # ego start s-position on Road 1
G            = 9.81

SURFACES = {
    "dry":  {"mu":1.0, "xodr":"adas_network_friction_dry.xodr"},
    "damp": {"mu":0.6, "xodr":"adas_network_friction_damp.xodr"},
    "wet":  {"mu":0.4, "xodr":"adas_network_friction_wet.xodr"},
    "icy":  {"mu":0.2, "xodr":"adas_network_friction_icy.xodr"},
}

SPEEDS = {
    50:  {"v_ms": 13.889, "s_obst": 140.0},
    80:  {"v_ms": 22.222, "s_obst": 190.0},
    120: {"v_ms": 33.333, "s_obst": 275.0},
}

OUT_DIR = r"C:\adas-thesis\scenarios\S_results\AEB"
os.makedirs(OUT_DIR, exist_ok=True)

def verify_positions():
    """Print verification table before generating files."""
    print("="*65)
    print("OBSTACLE PLACEMENT VERIFICATION")
    print(f"ALKS measured decel: {ALKS_DECEL} m/s²")
    print(f"TTC trigger:         {TTC_TRIGGER}s")
    print(f"Ego start:           s={S_EGO}m")
    print("="*65)
    print(f"{'Speed':>6}  {'v(m/s)':>7}  {'TTC gap':>8}  "
          f"{'Stop dist':>10}  {'Obst s':>7}  {'Margin':>8}  Result")
    print("-"*65)
    for spd, cfg in SPEEDS.items():
        v        = cfg["v_ms"]
        s_obst   = cfg["s_obst"]
        ttc_gap  = v * TTC_TRIGGER
        stop_d   = v**2 / (2 * ALKS_DECEL)
        gap_at_trigger = s_obst - S_EGO - ttc_gap
        margin   = gap_at_trigger - stop_d
        result   = "SAFE ✓" if margin > 5 else "TIGHT" if margin > 0 else "COLLISION ✗"
        print(f"{spd:>5}kph  {v:>7.3f}  {ttc_gap:>8.1f}m  "
              f"{stop_d:>10.1f}m  {s_obst:>7.1f}m  {margin:>7.1f}m  {result}")
    print("="*65)

def gen_xosc(surface, speed_kph):
    cfg      = SPEEDS[speed_kph]
    v_ms     = cfg["v_ms"]
    s_obst   = cfg["s_obst"]
    mu       = SURFACES[surface]["mu"]
    xodr     = SURFACES[surface]["xodr"]
    xodr_path = f"C:/adas-thesis/maps/{xodr}"

    # Theoretical stopping distance for this surface
    theory_d  = round(v_ms**2 / (2 * mu * G), 2)
    # ALKS measured stopping distance (from actual simulation, dry)
    alks_d    = round(v_ms**2 / (2 * ALKS_DECEL), 2)
    # Gap available at ALKS trigger
    ttc_gap   = round(v_ms * TTC_TRIGGER, 1)
    avail_gap = round(s_obst - S_EGO - ttc_gap, 1)
    margin    = round(avail_gap - alks_d, 1)
    safe      = margin > 5
    stop_time = max(30, int((v_ms / ALKS_DECEL) * 2.5 + 15))

    fname = f"S_AEB_{surface}_{speed_kph}kph.xosc"
    desc  = (f"AEB {surface} {speed_kph}kph | "
             f"mu={mu} obst_s={s_obst} | "
             f"predicted={'SAFE' if safe else 'COLLISION'}")

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!--
  AEB RESULT SCENARIO — {surface.upper()} {speed_kph}KPH
  ═══════════════════════════════════════════════════════════
  Surface           : {surface} (mu={mu})
  Road              : {xodr}, Road 1 lane -1
  ───────────────────────────────────────────────────────────
  Ego               : s={S_EGO}m, {v_ms} m/s ({speed_kph}kph)
  Obstacle          : s={s_obst}m (stationary car_red)
  Gap ego→obstacle  : {s_obst - S_EGO}m
  ───────────────────────────────────────────────────────────
  ALKS decel (meas) : {ALKS_DECEL} m/s² (from 50kph simulation)
  TTC trigger gap   : {ttc_gap}m (v × {TTC_TRIGGER}s)
  Gap at trigger    : {avail_gap}m
  ALKS stop dist    : {alks_d}m
  Safety margin     : {margin}m → {'SAFE ✓' if safe else 'COLLISION ✗'}
  ───────────────────────────────────────────────────────────
  Physics model (theory):
    dry  mu=1.0 → stop dist = {round(v_ms**2/(2*1.0*G),2)}m
    damp mu=0.6 → stop dist = {round(v_ms**2/(2*0.6*G),2)}m
    wet  mu=0.4 → stop dist = {round(v_ms**2/(2*0.4*G),2)}m
    icy  mu=0.2 → stop dist = {round(v_ms**2/(2*0.2*G),2)}m
  ───────────────────────────────────────────────────────────
  Record {stop_time}s, StopTrigger on EgoSpeed < 0.3 m/s
  ═══════════════════════════════════════════════════════════
  Run:
    cd C:\\esmini
    .\\bin\\esmini --osc C:\\adas-thesis\\scenarios\\S_results\\AEB\\{fname} ^
                 --fixed_timestep 0.05 --headless ^
                 --record C:\\adas-thesis\\results\\raw\\{fname.replace('.xosc','.dat')}
    .\\bin\\dat2csv C:\\adas-thesis\\results\\raw\\{fname.replace('.xosc','.dat')} ^
                   C:\\adas-thesis\\results\\raw\\{fname.replace('.xosc','.csv')}
-->
<OpenSCENARIO>
  <FileHeader revMajor="1" revMinor="2"
              date="2026-01-01T00:00:00"
              description="{desc}"
              author="HasnainBadar"/>
  <ParameterDeclarations/>
  <CatalogLocations>
    <VehicleCatalog>
      <Directory path="C:/esmini/resources/xosc/Catalogs/Vehicles"/>
    </VehicleCatalog>
    <ControllerCatalog>
      <Directory path="C:/esmini/resources/xosc/Catalogs/Controllers"/>
    </ControllerCatalog>
  </CatalogLocations>
  <RoadNetwork>
    <LogicFile filepath="{xodr_path}"/>
  </RoadNetwork>
  <Entities>
    <ScenarioObject name="Ego">
      <CatalogReference catalogName="VehicleCatalog" entryName="car_white"/>
      <ObjectController>
        <Controller name="ALKS_R157SM_Controller">
          <Properties>
            <Property name="model"    value="Regulation"/>
            <Property name="logLevel" value="2"/>
            <Property name="cruise"   value="true"/>
          </Properties>
        </Controller>
      </ObjectController>
    </ScenarioObject>
    <ScenarioObject name="Obstacle">
      <CatalogReference catalogName="VehicleCatalog" entryName="car_red"/>
    </ScenarioObject>
  </Entities>
  <Storyboard>
    <Init>
      <Actions>
        <Private entityRef="Ego">
          <PrivateAction>
            <TeleportAction>
              <Position>
                <LanePosition roadId="1" laneId="-1" offset="0" s="{S_EGO}">
                  <Orientation type="relative" h="0"/>
                </LanePosition>
              </Position>
            </TeleportAction>
          </PrivateAction>
          <PrivateAction>
            <LongitudinalAction>
              <SpeedAction>
                <SpeedActionDynamics dynamicsShape="step"
                                     dynamicsDimension="time" value="0"/>
                <SpeedActionTarget>
                  <AbsoluteTargetSpeed value="{v_ms}"/>
                </SpeedActionTarget>
              </SpeedAction>
            </LongitudinalAction>
          </PrivateAction>
          <PrivateAction>
            <ControllerAction>
              <ActivateControllerAction longitudinal="true" lateral="false"/>
            </ControllerAction>
          </PrivateAction>
        </Private>
        <Private entityRef="Obstacle">
          <PrivateAction>
            <TeleportAction>
              <Position>
                <LanePosition roadId="1" laneId="-1" offset="0" s="{s_obst}">
                  <Orientation type="relative" h="0"/>
                </LanePosition>
              </Position>
            </TeleportAction>
          </PrivateAction>
          <PrivateAction>
            <LongitudinalAction>
              <SpeedAction>
                <SpeedActionDynamics dynamicsShape="step"
                                     dynamicsDimension="time" value="0"/>
                <SpeedActionTarget>
                  <AbsoluteTargetSpeed value="0"/>
                </SpeedActionTarget>
              </SpeedAction>
            </LongitudinalAction>
          </PrivateAction>
        </Private>
      </Actions>
    </Init>
    <Story name="MainStory">
      <Act name="EgoAct">
        <ManeuverGroup maximumExecutionCount="1" name="EgoMG">
          <Actors selectTriggeringEntities="false">
            <EntityRef entityRef="Ego"/>
          </Actors>
        </ManeuverGroup>
        <StartTrigger>
          <ConditionGroup>
            <Condition name="Start" delay="0" conditionEdge="none">
              <ByValueCondition>
                <SimulationTimeCondition value="0" rule="greaterThan"/>
              </ByValueCondition>
            </Condition>
          </ConditionGroup>
        </StartTrigger>
        <StopTrigger>
          <ConditionGroup>
            <Condition name="EgoStopped" delay="1.0" conditionEdge="rising">
              <ByEntityCondition>
                <TriggeringEntities triggeringEntitiesRule="any">
                  <EntityRef entityRef="Ego"/>
                </TriggeringEntities>
                <EntityCondition>
                  <SpeedCondition value="0.3" rule="lessThan"/>
                </EntityCondition>
              </ByEntityCondition>
            </Condition>
          </ConditionGroup>
        </StopTrigger>
      </Act>
      <Act name="ObstacleAct">
        <ManeuverGroup maximumExecutionCount="1" name="ObstacleMG">
          <Actors selectTriggeringEntities="false">
            <EntityRef entityRef="Obstacle"/>
          </Actors>
        </ManeuverGroup>
        <StartTrigger>
          <ConditionGroup>
            <Condition name="Start" delay="0" conditionEdge="none">
              <ByValueCondition>
                <SimulationTimeCondition value="0" rule="greaterThan"/>
              </ByValueCondition>
            </Condition>
          </ConditionGroup>
        </StartTrigger>
      </Act>
    </Story>
    <StopTrigger>
      <ConditionGroup>
        <Condition name="TimeLimit" delay="0" conditionEdge="none">
          <ByValueCondition>
            <SimulationTimeCondition value="{stop_time}" rule="greaterThan"/>
          </ByValueCondition>
        </Condition>
      </ConditionGroup>
    </StopTrigger>
  </Storyboard>
</OpenSCENARIO>"""

    path = os.path.join(OUT_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return fname

def gen_ps_runner(files):
    lines = [
        "# run_AEB_fixed.ps1",
        "# Re-runs AEB scenarios with corrected obstacle positions",
        "# Run from any directory",
        "",
        '$e = "C:\\esmini\\bin\\esmini"',
        '$d = "C:\\esmini\\bin\\dat2csv"',
        '$r = "C:\\adas-thesis\\results\\raw"',
        '$s = "C:\\adas-thesis\\scenarios\\S_results\\AEB"',
        "",
    ]
    for f in files:
        dat = f.replace(".xosc", ".dat")
        csv = f.replace(".xosc", ".csv")
        lines += [
            f'Write-Host "Running {f}..." -ForegroundColor Cyan',
            f'& $e --osc "$s\\{f}" --fixed_timestep 0.05 --headless --record "$r\\{dat}"',
            f'& $d "$r\\{dat}" "$r\\{csv}"',
            f'Write-Host "Done: {f}" -ForegroundColor Green',
            "",
        ]
    lines.append('Write-Host "All AEB scenarios complete." -ForegroundColor Yellow')

    ps_path = os.path.join(OUT_DIR, "run_AEB_fixed.ps1")
    with open(ps_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Runner: {ps_path}")

def main():
    verify_positions()
    print(f"\nGenerating {len(SURFACES)*len(SPEEDS)} AEB scenario files...")
    files = []
    for surface in ["dry","damp","wet","icy"]:
        for speed_kph in [50, 80, 120]:
            fname = gen_xosc(surface, speed_kph)
            files.append(fname)
            print(f"  {fname}")

    gen_ps_runner(files)

    print(f"\nDone. {len(files)} files in {OUT_DIR}")
    print("\nNext steps:")
    print("1. python scripts\\fix_AEB_scenarios.py")
    print("2. PowerShell -ExecutionPolicy Bypass -File")
    print("   C:\\adas-thesis\\scenarios\\S_results\\AEB\\run_AEB_fixed.ps1")
    print("3. python scripts\\analyze_results_v2.py")

if __name__ == "__main__":
    main()
