import os

esmini_dir = r"C:\esmini"
esmini_exe = r".\bin\esmini.exe"
dat2csv_exe = r".\bin\dat2csv.exe"

# Pointing to the new V2 scripted scenarios
scenario_folder = r"C:\adas-thesis\scenarios\S_friction_scripted"
results_folder = r"C:\adas-thesis\results\raw_scripted"

# This is the line that will fix your error by creating the folder!
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

# Tell Python to pretend it is inside the esmini folder
os.chdir(esmini_dir)

files = [f for f in os.listdir(scenario_folder) if f.endswith('.xosc')]

for f in files:
    xosc_path = os.path.join(scenario_folder, f)
    name = f.split('.xosc')[0]
    dat_path = os.path.join(results_folder, name + '.dat')
    csv_path = os.path.join(results_folder, name + '.csv')
    
    print(f"Running {name}...")
    
    run_cmd = f'{esmini_exe} --osc "{xosc_path}" --headless --fixed_timestep 0.05 --record "{dat_path}"'
    os.system(run_cmd)
    
    print(f"Converting {name} to CSV...")
    csv_cmd = f'{dat2csv_exe} "{dat_path}" "{csv_path}"'
    os.system(csv_cmd)

print("\nData collection complete. All CSVs are in C:\\adas-thesis\\results\\raw_scripted")