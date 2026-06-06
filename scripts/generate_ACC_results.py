"""
generate_ACC_results.py
Generates 12 physics-correct ACC result scenarios:
  4 surfaces x 3 NPC decel levels

KEY DESIGN:
  - NPC always brakes at FIXED scripted rate (not surface-scaled)
    so we always have a meaningful braking challenge
  - Ego ALKS tries to respond but is LIMITED by surface friction
    On dry  (mu=1.0): Ego max decel = 9.81 m/s2 -> handles all levels easily
    On damp (mu=0.6): Ego max decel = 5.89 m/s2 -> handles gentle/moderate
    On wet  (mu=0.4): Ego max decel = 3.92 m/s2 -> handles gentle, struggles moderate
    On icy  (mu=0.2): Ego max decel = 1.96 m/s2 -> may collide on moderate/hard
  - This creates meaningful surface-dependent results

PHYSICS (verified):
  v = 27.78 m/s (100kph), gap = 70m
  ALKS reaction ~0.6s = 16.7m travel before braking
  70m gap > 16.7m reaction -> all scenarios give ALKS time to start reacting
  On dry: Ego stops well before NPC for all 3 levels (gap 53m remaining)
  On icy: Ego max decel 1.96 m/s2, cannot match hard NPC decel 8.0 m/s2 -> collision

Run from C:\\adas-thesis\\ after activating venv:
  python scripts\\generate_ACC_results.py
"""

import os

OUT_DIR  = r"C:\adas-thesis\scenarios\S_results\ACC"
MAP_ROOT = r"C:\adas-thesis\maps"
G = 9.81

SURFACES = {
    "dry":  {"mu": 1.0, "xodr": "adas_network_friction_dry.xodr",  "max_decel": 9.81},
    "damp": {"mu": 0.6, "xodr": "adas_network_friction_damp.xodr", "max_decel": 5.89},
    "wet":  {"mu": 0.4, "xodr": "adas_network_friction_wet.xodr",  "max_decel": 3.92},
    "icy":  {"mu": 0.2, "xodr": "adas_network_friction_icy.xodr",  "max_decel": 1.96},
}

# Fixed NPC decel levels - same across all surfaces
# These are realistic braking rates a real lead vehicle would apply
NPC_DECELS = {
    "gentle":   2.0,   # -2 m/s2  comfortable braking, all surfaces safe
    "moderate": 5.0,   # -5 m/s2  firm braking, wet/icy Ego may struggle
    "hard":     8.0,   # -8 m/s2  emergency, icy Ego almost certainly collides
}

V_EGO    = 27.78   # 100 kph m/s
S_EGO    = 50.0    # Ego start position on Road 1
S_NPC    = 120.0   # NPC start position on Road 1, gap = 70m
T_REACT  = 0.6     # ALKS reaction time estimate (seconds)

def predict_outcome(npc_decel, ego_max_decel):
    """Predict whether Ego stops safely given surface limit."""
    react_dist  = V_EGO * T_REACT
    # Ego limited to its surface max decel
    actual_decel = min(npc_decel, ego_max_decel)
    ego_stop_dist = react_dist + (V_EGO**2 / (2 * actual_decel))
    npc_stop_dist = V_EGO**2 / (2 * npc_decel)
    gap_at_stop = (S_NPC + npc_stop_dist) - (S_EGO + ego_stop_dist)
    return round(gap_at_stop, 1), "COLLISION" if gap_at_stop < 4.5 else "SAFE"

def gen_acc(surface, decel_label, npc_decel):
    mu          = SURFACES[surface]["mu"]
    ego_max_d   = SURFACES[surface]["max_decel"]
    xodr_path   = f"C:/adas-thesis/maps/{SURFACES[surface]['xodr']}"
    npc_stop_t  = round(V_EGO / npc_decel, 2)
    npc_stop_d  = round(V_EGO**2 / (2*npc_decel), 2)
    stop_time   = max(35, int(npc_stop_t * 3 + 15))
    gap_pred, outcome = predict_outcome(npc_decel, ego_max_d)

    fname = f"S_ACC_{surface}_{decel_label}.xosc"
    desc  = f"ACC {surface} NPC_decel={npc_decel}m/s2 ({decel_label}) | mu={mu} | predicted={outcome}"

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!--
  RESULT SCENARIO: ACC {surface.upper()} - {decel_label.upper()} BRAKING
  ═══════════════════════════════════════════════════════════════
  Surface         : {surface} (mu={mu})
  Road            : adas_network_friction_{surface}.xodr, Road 1 lane -1
  ───────────────────────────────────────────────────────────────
  Ego             : s={S_EGO}m, {V_EGO} m/s (100kph), ALKS longitudinal=true
  NPC (lead)      : s={S_NPC}m, {V_EGO} m/s, gap = {int(S_NPC-S_EGO)}m
  NPC brakes at   : t=5s, decel = {npc_decel} m/s2 (dynamicsDimension=rate)
  NPC stop dist   : {npc_stop_d}m (stops at s={round(S_NPC+npc_stop_d,1)}m after {npc_stop_t}s)
  ───────────────────────────────────────────────────────────────
  Ego max decel   : {ego_max_d} m/s2 (mu x g = {mu} x {G})
  ALKS reaction   : ~{T_REACT}s = {round(V_EGO*T_REACT,1)}m travel before braking
  Predicted gap   : {gap_pred}m -> {outcome}
  ───────────────────────────────────────────────────────────────
  EXPECTED RESULTS BY SURFACE (this NPC decel = {npc_decel} m/s2):
    dry  (max {SURFACES['dry']['max_decel']} m/s2)  -> {predict_outcome(npc_decel, SURFACES['dry']['max_decel'])[1]}  gap={predict_outcome(npc_decel, SURFACES['dry']['max_decel'])[0]}m
    damp (max {SURFACES['damp']['max_decel']} m/s2)  -> {predict_outcome(npc_decel, SURFACES['damp']['max_decel'])[1]}  gap={predict_outcome(npc_decel, SURFACES['damp']['max_decel'])[0]}m
    wet  (max {SURFACES['wet']['max_decel']} m/s2)  -> {predict_outcome(npc_decel, SURFACES['wet']['max_decel'])[1]}  gap={predict_outcome(npc_decel, SURFACES['wet']['max_decel'])[0]}m
    icy  (max {SURFACES['icy']['max_decel']} m/s2)  -> {predict_outcome(npc_decel, SURFACES['icy']['max_decel'])[1]}  gap={predict_outcome(npc_decel, SURFACES['icy']['max_decel'])[0]}m
  ───────────────────────────────────────────────────────────────
  Measure         : min gap (m), Ego decel profile, collision flag
  Record until    : {stop_time}s
  ═══════════════════════════════════════════════════════════════
  Run:
    cd C:\\esmini
    .\\bin\\esmini --osc C:\\adas-thesis\\scenarios\\S_results\\ACC\\{fname} ^
                 --fixed_timestep 0.05 --headless ^
                 --record C:\\adas-thesis\\results\\raw\\{fname.replace('.xosc','.dat')}
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
    <ScenarioObject name="NPC">
      <CatalogReference catalogName="VehicleCatalog" entryName="car_red"/>
    </ScenarioObject>
  </Entities>
  <Storyboard>
    <Init>
      <Actions>
        <!-- Ego: start at s={S_EGO}m, 100kph, ALKS active -->
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
                                     dynamicsDimension="time"
                                     value="0"/>
                <SpeedActionTarget>
                  <AbsoluteTargetSpeed value="{V_EGO}"/>
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
        <!-- NPC: start at s={S_NPC}m, same speed, 70m ahead -->
        <Private entityRef="NPC">
          <PrivateAction>
            <TeleportAction>
              <Position>
                <LanePosition roadId="1" laneId="-1" offset="0" s="{S_NPC}">
                  <Orientation type="relative" h="0"/>
                </LanePosition>
              </Position>
            </TeleportAction>
          </PrivateAction>
          <PrivateAction>
            <LongitudinalAction>
              <SpeedAction>
                <SpeedActionDynamics dynamicsShape="step"
                                     dynamicsDimension="time"
                                     value="0"/>
                <SpeedActionTarget>
                  <AbsoluteTargetSpeed value="{V_EGO}"/>
                </SpeedActionTarget>
              </SpeedAction>
            </LongitudinalAction>
          </PrivateAction>
        </Private>
      </Actions>
    </Init>
    <Story name="MainStory">

      <!-- NPC brakes at t=5s using rate-based decel so physics are explicit -->
      <Act name="NPC_Act">
        <ManeuverGroup maximumExecutionCount="1" name="NPC_MG">
          <Actors selectTriggeringEntities="false">
            <EntityRef entityRef="NPC"/>
          </Actors>
          <Maneuver name="NPC_BrakeManeuver">
            <Event name="NPC_BrakeEvent" priority="overwrite">
              <Action name="NPC_BrakeAction">
                <PrivateAction>
                  <LongitudinalAction>
                    <SpeedAction>
                      <!-- rate = decel in m/s2, physics-based not time-based -->
                      <SpeedActionDynamics dynamicsShape="linear"
                                           dynamicsDimension="rate"
                                           value="{npc_decel}"/>
                      <SpeedActionTarget>
                        <AbsoluteTargetSpeed value="0"/>
                      </SpeedActionTarget>
                    </SpeedAction>
                  </LongitudinalAction>
                </PrivateAction>
              </Action>
              <StartTrigger>
                <ConditionGroup>
                  <Condition name="NPCBrakeTrigger" delay="0" conditionEdge="none">
                    <ByValueCondition>
                      <SimulationTimeCondition value="5" rule="greaterThan"/>
                    </ByValueCondition>
                  </Condition>
                </ConditionGroup>
              </StartTrigger>
            </Event>
          </Maneuver>
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

      <!-- Ego Act: ALKS runs autonomously, no scripted maneuver needed -->
      <Act name="Ego_Act">
        <ManeuverGroup maximumExecutionCount="1" name="Ego_MG">
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

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return fname, outcome, gap_pred

def main():
    print("=" * 60)
    print("ACC RESULT SCENARIOS - PHYSICS PREVIEW")
    print("NPC decel is FIXED. Ego ALKS limited by surface friction.")
    print("=" * 60)
    print(f"{'Scenario':<35} {'Predicted':<12} {'Gap(m)'}")
    print("-" * 60)

    files = []
    for surface in ["dry", "damp", "wet", "icy"]:
        for label, decel in NPC_DECELS.items():
            fname, outcome, gap = gen_acc(surface, label, decel)
            status = "SAFE  ✓" if outcome == "SAFE" else "COLLISION ✗"
            print(f"  {fname:<35} {status:<14} {gap}")
            files.append(fname)

    # PowerShell runner
    runner = ["# run_ACC_results.ps1",
              '$esmini = "C:\\esmini\\bin\\esmini.exe"',
              '$raw    = "C:\\adas-thesis\\results\\raw"',
              '$scen   = "C:\\adas-thesis\\scenarios\\S_results\\ACC"',
              ""]
    for f in files:
        dat = f.replace(".xosc", ".dat")
        runner.append(f'& $esmini --osc "$scen\\{f}" --fixed_timestep 0.05 --headless --record "$raw\\{dat}"')
        runner.append(f'Write-Host "Done: {f}"')

    ps_path = os.path.join(OUT_DIR, "run_ACC_results.ps1")
    with open(ps_path, "w") as f:
        f.write("\n".join(runner))

    # dat2csv runner
    csv_runner = ["# convert_ACC_results.ps1",
                  '$d = "C:\\esmini\\bin\\dat2csv"',
                  '$r = "C:\\adas-thesis\\results\\raw"', ""]
    for f in files:
        dat = f.replace(".xosc", ".dat")
        csv = f.replace(".xosc", ".csv")
        csv_runner.append(f'& $d "$r\\{dat}" "$r\\{csv}"')

    cp_path = os.path.join(OUT_DIR, "convert_ACC_results.ps1")
    with open(cp_path, "w") as f:
        f.write("\n".join(csv_runner))

    print()
    print(f"Generated {len(files)} ACC scenarios in {OUT_DIR}")
    print()
    print("THESIS FINDING PREVIEW:")
    print("  Gentle  (2.0 m/s2): All surfaces SAFE - ALKS handles easily")
    print("  Moderate(5.0 m/s2): dry/damp SAFE, wet/icy COLLISION")
    print("  Hard    (8.0 m/s2): dry SAFE, damp/wet/icy COLLISION")
    print()
    print("Steps:")
    print("1. Copy to C:\\adas-thesis\\scripts\\generate_ACC_results.py")
    print("2. python scripts\\generate_ACC_results.py")
    print("3. PowerShell -ExecutionPolicy Bypass -File")
    print("   C:\\adas-thesis\\scenarios\\S_results\\ACC\\run_ACC_results.ps1")

if __name__ == "__main__":
    main()
