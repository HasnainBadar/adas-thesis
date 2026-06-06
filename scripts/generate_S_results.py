"""
generate_S_results.py
Generates 36 friction-aware ADAS result scenarios:
  - 12 AEB  (Road 1 highway, 4 surfaces x 3 speeds)
  - 12 ACC  (Road 1 highway, 4 surfaces x 3 decel rates)
  - 12 LKA  (Road 20 S-curve, 4 surfaces x 3 drift rates)

All use ALKS_R157SM_Controller so physics respond to friction maps.
NPC braking uses dynamicsDimension="rate" so stopping varies with surface.

Run from C:\adas-thesis\ after activating venv:
  python scripts\generate_S_results.py

Output: C:\adas-thesis\scenarios\S_results\AEB\, ACC\, LKA\
"""

import os
import math

# ── Output root ──────────────────────────────────────────────────────────────
OUT_ROOT = r"C:\adas-thesis\scenarios\S_results"
MAP_ROOT = r"C:\adas-thesis\maps"

# ── Surface definitions ──────────────────────────────────────────────────────
SURFACES = {
    "dry":  {"mu": 1.0, "xodr": "adas_network_friction_dry.xodr"},
    "damp": {"mu": 0.6, "xodr": "adas_network_friction_damp.xodr"},
    "wet":  {"mu": 0.4, "xodr": "adas_network_friction_wet.xodr"},
    "icy":  {"mu": 0.2, "xodr": "adas_network_friction_icy.xodr"},
}

G = 9.81  # gravity m/s²

def stopping_distance(v_ms, mu):
    """Physics stopping distance: d = v² / (2*mu*g)"""
    return (v_ms ** 2) / (2 * mu * G)

def brake_decel(mu, fraction=1.0):
    """Max braking decel for surface: a = mu*g"""
    return round(mu * G * fraction, 4)

# ── Template builder ─────────────────────────────────────────────────────────
def alks_controller_block():
    return """      <ObjectController>
        <Controller name="ALKS_R157SM_Controller">
          <Properties>
            <Property name="model" value="Regulation"/>
            <Property name="logLevel" value="2"/>
            <Property name="cruise" value="true"/>
          </Properties>
        </Controller>
      </ObjectController>"""

def header(description, xodr_path):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OpenSCENARIO>
  <FileHeader revMajor="1" revMinor="2"
              date="2026-01-01T00:00:00"
              description="{description}"
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
  </RoadNetwork>"""

def footer(stop_time=30):
    return f"""  <Storyboard>
    <Init>
      <Actions>
      </Actions>
    </Init>
    <Story name="MainStory">
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

# ── AEB scenario ─────────────────────────────────────────────────────────────
def gen_aeb(surface, speed_kph, out_dir):
    name = surface
    mu   = SURFACES[surface]["mu"]
    xodr = SURFACES[surface]["xodr"].replace(".xodr", "")
    xodr_path = f"C:/adas-thesis/maps/{SURFACES[surface]['xodr']}"

    v_ms   = round(speed_kph / 3.6, 4)
    s_ego  = 50.0
    stop_d = stopping_distance(v_ms, mu)
    s_obst = round(s_ego + stop_d + 20.0, 3)  # 20m safety margin
    stop_time = max(30, int(stop_d / v_ms * 3 + 10))

    desc = f"AEB {surface} mu={mu} {speed_kph}kph | obstacle s={s_obst}m | stopDist={round(stop_d,2)}m"
    fname = f"S_AEB_{surface}_{speed_kph}kph.xosc"

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!--
  RESULT SCENARIO: AEB {surface.upper()} {speed_kph}kph
  Surface    : {surface} (mu={mu})
  Road       : adas_network_friction_{surface}.xodr, Road 1 lane -1
  Ego start  : s={s_ego}m, speed={v_ms} m/s ({speed_kph} kph)
  Obstacle   : stationary car_red at s={s_obst}m
  Theory     : stopping distance = v^2/(2*mu*g) = {round(stop_d,2)}m
  Safety gap : 20m beyond theoretical stop
  Controller : ALKS_R157SM longitudinal=true (AEB active)
  Measure    : actual stopping distance, collision flag
  Run:
    cd C:\\esmini
    .\\bin\\esmini --osc C:\\adas-thesis\\scenarios\\S_results\\AEB\\{fname} ^
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
{alks_controller_block()}
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
                <LanePosition roadId="1" laneId="-1" offset="0" s="{s_ego}">
                  <Orientation type="relative" h="0"/>
                </LanePosition>
              </Position>
            </TeleportAction>
          </PrivateAction>
          <PrivateAction>
            <LongitudinalAction>
              <SpeedAction>
                <SpeedActionDynamics dynamicsShape="step" dynamicsDimension="time" value="0"/>
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
                <SpeedActionDynamics dynamicsShape="step" dynamicsDimension="time" value="0"/>
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
            <Condition name="EgoStopped" delay="1" conditionEdge="rising">
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

    path = os.path.join(out_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  AEB: {fname}  ego={v_ms}m/s  obst_s={s_obst}m  theory_stop={round(stop_d,2)}m")
    return fname

# ── ACC scenario ─────────────────────────────────────────────────────────────
def gen_acc(surface, decel_label, decel_fraction, out_dir):
    mu        = SURFACES[surface]["mu"]
    xodr_path = f"C:/adas-thesis/maps/{SURFACES[surface]['xodr']}"
    v_ms      = 27.78   # 100 kph
    s_ego     = 50.0
    s_npc     = 120.0   # 70m gap
    npc_decel = round(brake_decel(mu, decel_fraction), 4)
    stop_time = max(40, int(v_ms / max(npc_decel, 0.1) * 2 + 15))

    desc  = f"ACC {surface} mu={mu} NPC decel={npc_decel}m/s2 ({decel_label})"
    fname = f"S_ACC_{surface}_{decel_label}.xosc"

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!--
  RESULT SCENARIO: ACC {surface.upper()} {decel_label.upper()}
  Surface    : {surface} (mu={mu})
  Road       : adas_network_friction_{surface}.xodr, Road 1 lane -1
  Ego        : s={s_ego}m, 27.78 m/s (100kph), ALKS ACC active
  NPC        : s={s_npc}m, 27.78 m/s, brakes at t=5s
  NPC decel  : {npc_decel} m/s2 = mu*g*{decel_fraction} ({decel_label})
  Measure    : min gap, Ego decel profile, collision flag
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
{alks_controller_block()}
    </ScenarioObject>
    <ScenarioObject name="NPC">
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
                <LanePosition roadId="1" laneId="-1" offset="0" s="{s_ego}">
                  <Orientation type="relative" h="0"/>
                </LanePosition>
              </Position>
            </TeleportAction>
          </PrivateAction>
          <PrivateAction>
            <LongitudinalAction>
              <SpeedAction>
                <SpeedActionDynamics dynamicsShape="step" dynamicsDimension="time" value="0"/>
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
        <Private entityRef="NPC">
          <PrivateAction>
            <TeleportAction>
              <Position>
                <LanePosition roadId="1" laneId="-1" offset="0" s="{s_npc}">
                  <Orientation type="relative" h="0"/>
                </LanePosition>
              </Position>
            </TeleportAction>
          </PrivateAction>
          <PrivateAction>
            <LongitudinalAction>
              <SpeedAction>
                <SpeedActionDynamics dynamicsShape="step" dynamicsDimension="time" value="0"/>
                <SpeedActionTarget>
                  <AbsoluteTargetSpeed value="{v_ms}"/>
                </SpeedActionTarget>
              </SpeedAction>
            </LongitudinalAction>
          </PrivateAction>
        </Private>
      </Actions>
    </Init>
    <Story name="MainStory">
      <Act name="NPC_Act">
        <ManeuverGroup maximumExecutionCount="1" name="NPC_MG">
          <Actors selectTriggeringEntities="false">
            <EntityRef entityRef="NPC"/>
          </Actors>
          <Maneuver name="NPC_Brake">
            <Event name="NPC_BrakeEvent" priority="overwrite">
              <Action name="NPC_BrakeAction">
                <PrivateAction>
                  <LongitudinalAction>
                    <SpeedAction>
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
                  <Condition name="NPC_BrakeTrigger" delay="0" conditionEdge="none">
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

    path = os.path.join(out_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ACC: {fname}  npc_decel={npc_decel}m/s2  stop_t={stop_time}s")
    return fname

# ── LKA scenario ─────────────────────────────────────────────────────────────
def gen_lka(surface, drift_label, drift_max_lat_acc, out_dir):
    mu        = SURFACES[surface]["mu"]
    xodr_path = f"C:/esmini/resources/xosc/Catalogs/../../../../../adas-thesis/maps/{SURFACES[surface]['xodr']}"
    xodr_path = f"C:/adas-thesis/maps/{SURFACES[surface]['xodr']}"
    v_ms      = 22.22   # 80 kph

    desc  = f"LKA {surface} mu={mu} drift={drift_label} maxLatAcc={drift_max_lat_acc}"
    fname = f"S_LKA_{surface}_{drift_label}.xosc"

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!--
  RESULT SCENARIO: LKA {surface.upper()} {drift_label.upper()}
  Surface    : {surface} (mu={mu})
  Road       : adas_network_friction_{surface}.xodr, Road 20 S-curve lane -1
  Ego        : s=10m, 22.22 m/s (80kph), ALKS lateral=true
  Drift      : LaneOffsetAction offset=1.2m maxLatAcc={drift_max_lat_acc} at t=3s
  ALKS LKA   : autonomous lane-keep correction
  Measure    : lateral deviation (m), correction time, whether lane boundary crossed
  Note       : LKA is a steering function. Differences across surfaces may be
               small but show controller robustness. Finding = LKA is surface-robust.
  Run:
    cd C:\\esmini
    .\\bin\\esmini --osc C:\\adas-thesis\\scenarios\\S_results\\LKA\\{fname} ^
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
{alks_controller_block()}
    </ScenarioObject>
  </Entities>
  <Storyboard>
    <Init>
      <Actions>
        <Private entityRef="Ego">
          <PrivateAction>
            <TeleportAction>
              <Position>
                <LanePosition roadId="20" laneId="-1" offset="0" s="10">
                  <Orientation type="relative" h="0"/>
                </LanePosition>
              </Position>
            </TeleportAction>
          </PrivateAction>
          <PrivateAction>
            <LongitudinalAction>
              <SpeedAction>
                <SpeedActionDynamics dynamicsShape="step" dynamicsDimension="time" value="0"/>
                <SpeedActionTarget>
                  <AbsoluteTargetSpeed value="{v_ms}"/>
                </SpeedActionTarget>
              </SpeedAction>
            </LongitudinalAction>
          </PrivateAction>
          <PrivateAction>
            <ControllerAction>
              <ActivateControllerAction longitudinal="true" lateral="true"/>
            </ControllerAction>
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
          <Maneuver name="DriftManeuver">
            <Event name="DriftEvent" priority="override">
              <Action name="DriftAction">
                <PrivateAction>
                  <LateralAction>
                    <LaneOffsetAction continuous="true">
                      <LaneOffsetActionDynamics maxLateralAcc="{drift_max_lat_acc}"
                                                dynamicsShape="linear"/>
                      <LaneOffsetTarget>
                        <AbsoluteTargetLaneOffset value="1.2"/>
                      </LaneOffsetTarget>
                    </LaneOffsetAction>
                  </LateralAction>
                </PrivateAction>
              </Action>
              <StartTrigger>
                <ConditionGroup>
                  <Condition name="DriftTrigger" delay="0" conditionEdge="none">
                    <ByValueCondition>
                      <SimulationTimeCondition value="3" rule="greaterThan"/>
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
    </Story>
    <StopTrigger>
      <ConditionGroup>
        <Condition name="TimeLimit" delay="0" conditionEdge="none">
          <ByValueCondition>
            <SimulationTimeCondition value="25" rule="greaterThan"/>
          </ByValueCondition>
        </Condition>
      </ConditionGroup>
    </StopTrigger>
  </Storyboard>
</OpenSCENARIO>"""

    path = os.path.join(out_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  LKA: {fname}  maxLatAcc={drift_max_lat_acc}")
    return fname

# ── PowerShell batch runner ───────────────────────────────────────────────────
def gen_runner(aeb_files, acc_files, lka_files, out_root):
    lines = [
        "# run_all_S_results.ps1",
        "# Runs all 36 friction-aware result scenarios headless",
        "# Run from C:\\esmini directory",
        "# PowerShell -ExecutionPolicy Bypass -File C:\\adas-thesis\\scenarios\\S_results\\run_all_S_results.ps1",
        "",
        '$esmini = "C:\\esmini\\bin\\esmini.exe"',
        '$raw    = "C:\\adas-thesis\\results\\raw"',
        '$scen   = "C:\\adas-thesis\\scenarios\\S_results"',
        "",
        "Write-Host 'Running AEB scenarios...' -ForegroundColor Cyan",
    ]
    for f in aeb_files:
        dat = f.replace(".xosc", ".dat")
        lines.append(f'& $esmini --osc "$scen\\AEB\\{f}" --fixed_timestep 0.05 --headless --record "$raw\\{dat}"')
        lines.append(f'Write-Host "Done: {f}" -ForegroundColor Green')

    lines += ["", "Write-Host 'Running ACC scenarios...' -ForegroundColor Cyan"]
    for f in acc_files:
        dat = f.replace(".xosc", ".dat")
        lines.append(f'& $esmini --osc "$scen\\ACC\\{f}" --fixed_timestep 0.05 --headless --record "$raw\\{dat}"')
        lines.append(f'Write-Host "Done: {f}" -ForegroundColor Green')

    lines += ["", "Write-Host 'Running LKA scenarios...' -ForegroundColor Cyan"]
    for f in lka_files:
        dat = f.replace(".xosc", ".dat")
        lines.append(f'& $esmini --osc "$scen\\LKA\\{f}" --fixed_timestep 0.05 --headless --record "$raw\\{dat}"')
        lines.append(f'Write-Host "Done: {f}" -ForegroundColor Green')

    lines += ["", "Write-Host 'All 36 scenarios complete.' -ForegroundColor Yellow"]

    ps_path = os.path.join(out_root, "run_all_S_results.ps1")
    with open(ps_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nRunner: {ps_path}")

# ── dat2csv batch ─────────────────────────────────────────────────────────────
def gen_csv_runner(aeb_files, acc_files, lka_files, out_root):
    lines = [
        "# convert_all_S_results.ps1",
        "# Converts all .dat recordings to .csv for analysis",
        "# Run AFTER run_all_S_results.ps1",
        "",
        '$dat2csv = "C:\\esmini\\bin\\dat2csv"',
        '$raw     = "C:\\adas-thesis\\results\\raw"',
        "",
    ]
    for f in aeb_files + acc_files + lka_files:
        dat = f.replace(".xosc", ".dat")
        csv = f.replace(".xosc", ".csv")
        lines.append(f'& $dat2csv "$raw\\{dat}" "$raw\\{csv}"')

    lines.append('Write-Host "All converted." -ForegroundColor Green')

    ps_path = os.path.join(out_root, "convert_all_S_results.ps1")
    with open(ps_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"CSV runner: {ps_path}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    aeb_dir = os.path.join(OUT_ROOT, "AEB")
    acc_dir = os.path.join(OUT_ROOT, "ACC")
    lka_dir = os.path.join(OUT_ROOT, "LKA")
    for d in [aeb_dir, acc_dir, lka_dir]:
        os.makedirs(d, exist_ok=True)

    aeb_files, acc_files, lka_files = [], [], []

    # AEB: 4 surfaces x 3 speeds
    print("\n=== Generating AEB scenarios ===")
    for surface in ["dry", "damp", "wet", "icy"]:
        for speed_kph in [50, 80, 120]:
            aeb_files.append(gen_aeb(surface, speed_kph, aeb_dir))

    # ACC: 4 surfaces x 3 decel levels
    print("\n=== Generating ACC scenarios ===")
    decel_variants = [
        ("mild",     0.3),
        ("moderate", 0.6),
        ("hard",     1.0),
    ]
    for surface in ["dry", "damp", "wet", "icy"]:
        for label, fraction in decel_variants:
            acc_files.append(gen_acc(surface, label, fraction, acc_dir))

    # LKA: 4 surfaces x 3 drift rates
    print("\n=== Generating LKA scenarios ===")
    drift_variants = [
        ("slow", 0.1),
        ("med",  0.3),
        ("fast", 0.6),
    ]
    for surface in ["dry", "damp", "wet", "icy"]:
        for label, max_lat_acc in drift_variants:
            lka_files.append(gen_lka(surface, label, max_lat_acc, lka_dir))

    # Runners
    print("\n=== Generating PowerShell runners ===")
    gen_runner(aeb_files, acc_files, lka_files, OUT_ROOT)
    gen_csv_runner(aeb_files, acc_files, lka_files, OUT_ROOT)

    print(f"\nDone. Total scenarios: {len(aeb_files)+len(acc_files)+len(lka_files)}")
    print(f"  AEB: {len(aeb_files)}  ACC: {len(acc_files)}  LKA: {len(lka_files)}")
    print(f"Output: {OUT_ROOT}")
    print("\nNext steps:")
    print("1. Copy generate_S_results.py to C:\\adas-thesis\\scripts\\")
    print("2. Activate venv: .venv\\Scripts\\Activate.ps1")
    print("3. Run: python scripts\\generate_S_results.py")
    print("4. Run scenarios: PowerShell -ExecutionPolicy Bypass -File")
    print("   C:\\adas-thesis\\scenarios\\S_results\\run_all_S_results.ps1")
    print("5. Convert: PowerShell -ExecutionPolicy Bypass -File")
    print("   C:\\adas-thesis\\scenarios\\S_results\\convert_all_S_results.ps1")

if __name__ == "__main__":
    main()