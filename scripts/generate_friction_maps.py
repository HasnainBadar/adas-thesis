import xml.etree.ElementTree as ET
import os

# 1. Define our friction dictionary based on your thesis parameters
friction_levels = {
    'dry': 1.0,   # ISO 11283 baseline
    'damp': 0.6,  # Light rain
    'wet': 0.4,   # Heavy rain
    'icy': 0.2    # Extreme winter
}

# 2. File paths
base_map_path = r"C:\adas-thesis\maps\adas_network.xodr"
output_dir = r"C:\adas-thesis\maps"

print(f"Reading base map from: {base_map_path}")

# 3. Loop through each friction level and create a new map variant
for condition, mu in friction_levels.items():
    # Parse the base XML tree
    tree = ET.parse(base_map_path)
    root = tree.getroot()
    
    # Find Road 1 (the 800m highway straight)
    for road in root.findall('road'):
        if road.get('id') == '1':
            # Find all lanes within Road 1
            for lanes in road.iter('lane'):
                lane_id = lanes.get('id')
                
                # Apply the friction ONLY to the driving lanes (-1 for Ego, -2 for adjacent)
                if lane_id in ['-1', '-2']:
                    # Create the material element
                    # sOffset="0" means it applies from the very start of the road to the end
                    material = ET.Element('material', {
                        'sOffset': '0', 
                        'surface': 'asphalt', 
                        'friction': str(mu), 
                        'roughness': '0.02'
                    })
                    lanes.append(material)
    
    # 4. Save the new variant map
    output_filename = f"adas_network_friction_{condition}.xodr"
    output_path = os.path.join(output_dir, output_filename)
    
    # Write to file with the standard XML declaration needed by esmini
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"Successfully generated: {output_filename} (mu={mu})")

print("\nAll friction maps generated successfully!")