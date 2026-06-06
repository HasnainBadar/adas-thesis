import os

speeds = [50, 80, 120]
friction_conditions = {'dry': 1.0, 'damp': 0.6, 'wet': 0.4, 'icy': 0.2}

start_pos = 100.0
out_folder = r"C:\adas-thesis\scenarios\S_friction_final"

if not os.path.exists(out_folder):
    os.makedirs(out_folder)

# basic xml template
template = """<?xml version="1.0" encoding="UTF-8"?>
<OpenSCENARIO>
  <FileHeader revMajor="1" revMinor="1" date="2026-05-01T00:00:00" description="AEB friction test {cond} {spd}kph" author="HasnainBadar"/>
  <CatalogLocations>
    <VehicleCatalog><Directory path="C:/esmini/resources/xosc/Catalogs/Vehicles"/></VehicleCatalog>
    <ControllerCatalog><Directory path="C:/esmini/resources/xosc/Catalogs/Controllers"/></ControllerCatalog>
  </CatalogLocations>
  <RoadNetwork>
    <LogicFile filepath="C:/adas-thesis/maps/adas_network_friction_{cond}.xodr"/>
  </RoadNetwork>
  <Entities>
    <ScenarioObject name="Ego">
      <CatalogReference catalogName="VehicleCatalog" entryName="car_white"/>
      <ObjectController>
        <Controller name="ALKS_R157SM_Controller">
          <Properties>
            <Property name="model" value="Regulation"/>
            <Property name="logLevel" value="2"/>
            <Property name="cruise" value="true"/>
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
          <PrivateAction>
            <ControllerAction><ActivateControllerAction longitudinal="true" lateral="false"/></ControllerAction>
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
      <Act name="Act1">
        <ManeuverGroup maximumExecutionCount="1" name="MG1">
          <Actors selectTriggeringEntities="false"><EntityRef entityRef="Ego"/></Actors>
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
          <ByValueCondition><SimulationTimeCondition value="20" rule="greaterThan"/></ByValueCondition>
        </Condition>
      </ConditionGroup>
    </StopTrigger>
  </Storyboard>
</OpenSCENARIO>
"""

for speed in speeds:
    speed_ms = speed / 3.6
    
    # Give the ALKS controller a massive 8-second lead time to see the car and brake naturally
    obstacle_pos = start_pos + (speed_ms * 8.0)
    
    for cond, mu in friction_conditions.items():
        xml_data = template.format(
            cond=cond,
            spd=speed,
            ego_s=start_pos,
            spd_ms=round(speed_ms, 3),
            obs_s=round(obstacle_pos, 3)
        )
        
        filename = f"S1_AEB_{cond}_{speed}kph.xosc"
        path = os.path.join(out_folder, filename)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml_data)
            
        print(f"saved {filename} with obstacle at {round(obstacle_pos, 1)}m")
        
print("done generating all 12 scenarios.")