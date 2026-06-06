import os

speeds = [50, 80, 120]
friction_conditions = {'dry': 1.0, 'damp': 0.6, 'wet': 0.4, 'icy': 0.2}
gravity = 9.81

start_pos = 100.0
out_folder = r"C:\adas-thesis\scenarios\S_friction_scripted"

if not os.path.exists(out_folder):
    os.makedirs(out_folder)

template = """<?xml version="1.0" encoding="UTF-8"?>
<OpenSCENARIO>
  <FileHeader revMajor="1" revMinor="1" date="2026-05-01T00:00:00" description="Scripted AEB friction test {cond} {spd}kph" author="HasnainBadar"/>
  <CatalogLocations>
    <VehicleCatalog><Directory path="C:/esmini/resources/xosc/Catalogs/Vehicles"/></VehicleCatalog>
  </CatalogLocations>
  <RoadNetwork>
    <LogicFile filepath="C:/adas-thesis/maps/adas_network_friction_{cond}.xodr"/>
  </RoadNetwork>
  <Entities>
    <ScenarioObject name="Ego">
      <CatalogReference catalogName="VehicleCatalog" entryName="car_white"/>
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
            <TeleportAction><Position><LanePosition roadId="1" laneId="-1" offset="0" s="{ego_s}"/></Position></TeleportAction>
          </PrivateAction>
          <PrivateAction>
            <LongitudinalAction>
              <SpeedAction>
                <SpeedActionDynamics dynamicsShape="step" dynamicsDimension="time" value="0"/>
                <SpeedActionTarget><AbsoluteTargetSpeed value="{spd_ms}"/></SpeedActionTarget>
              </SpeedAction>
            </LongitudinalAction>
          </PrivateAction>
        </Private>
        <Private entityRef="Obstacle">
          <PrivateAction>
            <TeleportAction><Position><LanePosition roadId="1" laneId="-1" offset="0" s="{obs_s}"/></Position></TeleportAction>
          </PrivateAction>
          <PrivateAction>
            <LongitudinalAction>
              <SpeedAction>
                <SpeedActionDynamics dynamicsShape="step" dynamicsDimension="time" value="0"/>
                <SpeedActionTarget><AbsoluteTargetSpeed value="0"/></SpeedActionTarget>
              </SpeedAction>
            </LongitudinalAction>
          </PrivateAction>
        </Private>
      </Actions>
    </Init>
    <Story name="MainStory">
      <Act name="AEB_Act">
        <ManeuverGroup maximumExecutionCount="1" name="AEB_MG">
          <Actors selectTriggeringEntities="false"><EntityRef entityRef="Ego"/></Actors>
          
          <Maneuver name="AEB_Maneuver">
            <Event name="AEB_Trigger_Event" priority="overwrite" maximumExecutionCount="1">
              <Action name="EmergencyBrake">
                <PrivateAction>
                  <LongitudinalAction>
                    <SpeedAction>
                      <SpeedActionDynamics dynamicsShape="linear" dynamicsDimension="rate" value="{decel_rate}"/>
                      <SpeedActionTarget><AbsoluteTargetSpeed value="0"/></SpeedActionTarget>
                    </SpeedAction>
                  </LongitudinalAction>
                </PrivateAction>
              </Action>
              <StartTrigger>
                <ConditionGroup>
                  <Condition name="RadarDetection" delay="0" conditionEdge="rising">
                    <ByEntityCondition>
                      <TriggeringEntities triggeringEntitiesRule="any"><EntityRef entityRef="Ego"/></TriggeringEntities>
                      <EntityCondition>
                        <RelativeDistanceCondition entityRef="Obstacle" relativeDistanceType="longitudinal" value="{trigger_dist}" freespace="false" rule="lessThan"/>
                      </EntityCondition>
                    </ByEntityCondition>
                  </Condition>
                </ConditionGroup>
              </StartTrigger>
            </Event>
          </Maneuver>

        </ManeuverGroup>
        <StartTrigger>
          <ConditionGroup>
            <Condition name="Start" delay="0" conditionEdge="none">
              <ByValueCondition><SimulationTimeCondition value="0" rule="greaterThan"/></ByValueCondition>
            </Condition>
          </ConditionGroup>
        </StartTrigger>
      </Act>
    </Story>
    <StopTrigger>
      <ConditionGroup>
        <Condition name="Stop" delay="0" conditionEdge="none">
          <ByValueCondition><SimulationTimeCondition value="15" rule="greaterThan"/></ByValueCondition>
        </Condition>
      </ConditionGroup>
    </StopTrigger>
  </Storyboard>
</OpenSCENARIO>
"""

for speed in speeds:
    speed_ms = speed / 3.6
    
    obstacle_pos = start_pos + (speed_ms * 8.0)
    ttc_trigger_distance = speed_ms * 2.5
    
    for cond, mu in friction_conditions.items():
        
        # THIS IS THE MAGIC: We explicitly limit the car's braking power based on the road physics!
        max_physical_deceleration = mu * gravity
        
        xml_data = template.format(
            cond=cond,
            spd=speed,
            ego_s=start_pos,
            spd_ms=round(speed_ms, 3),
            obs_s=round(obstacle_pos, 3),
            trigger_dist=round(ttc_trigger_distance, 3),
            decel_rate=round(max_physical_deceleration, 3)  # Injecting the physical limit
        )
        
        filename = f"S2_Scripted_AEB_{cond}_{speed}kph.xosc"
        path = os.path.join(out_folder, filename)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml_data)
            
        print(f"Saved {filename} | AEB Trigger: {round(ttc_trigger_distance, 1)}m | Max Decel: {round(max_physical_deceleration, 2)} m/s²")
        
print("Done generating V2 scenarios with explicit physics limits.")