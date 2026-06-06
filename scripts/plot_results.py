import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 1. File Paths for BOTH sets of data
data_alks = r"C:\adas-thesis\results\thesis_summary_table.csv"       # Set A
data_scripted = r"C:\adas-thesis\results\thesis_summary_scripted.csv" # Set B
output_image = r"C:\adas-thesis\results\thesis_comparison_chart.png"

# 2. Load the data
try:
    df_alks = pd.read_csv(data_alks)
    df_scripted = pd.read_csv(data_scripted)
except FileNotFoundError as e:
    print(f"Error loading data: {e}")
    print("Make sure both CSV files exist in your results folder!")
    exit()

# 3. Helper function to extract Condition and Speed from the scenario names
def parse_scenario_name(df, prefix):
    # E.g., splitting "S1_AEB_damp_120kph" or "S2_Scripted_AEB_damp_120kph"
    # To make it robust, we look for the keywords rather than strict index splitting
    conditions = []
    speeds = []
    for name in df['Scenario']:
        cond = 'Dry'
        for c in ['dry', 'damp', 'wet', 'icy']:
            if c in name.lower(): cond = c.capitalize()
        spd = 0
        for s in [50, 80, 120]:
            if str(s) in name: spd = s
        conditions.append(cond)
        speeds.append(spd)
    
    df['Condition'] = conditions
    df['Ego_Speed'] = speeds
    return df

df_alks = parse_scenario_name(df_alks, "S1")
df_scripted = parse_scenario_name(df_scripted, "S2")

# 4. Set up a Side-by-Side Plot (1 row, 2 columns), sharing the Y-axis scale
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), sharey=True)
fig.suptitle('AEB Collision Impact Speeds: Regulation vs. Physical Limits', fontsize=16, fontweight='bold', y=1.02)

conditions = ['Dry', 'Damp', 'Wet', 'Icy']
speeds = [50, 80, 120]
x = np.arange(len(conditions))
width = 0.25
colors = {50: '#2ca02c', 80: '#ff7f0e', 120: '#d62728'}

# --- Plot Set A (ALKS) ---
for i, speed in enumerate(speeds):
    speed_data = df_alks[df_alks['Ego_Speed'] == speed].set_index('Condition').reindex(conditions)
    impact_speeds = speed_data['Impact_Speed_kph'].fillna(0).values
    offset = (i - 1) * width
    rects1 = ax1.bar(x + offset, impact_speeds, width, label=f'{speed} kph', color=colors[speed], edgecolor='black')
    ax1.bar_label(rects1, padding=3, fmt='%.1f')

ax1.set_title('Set A: ALKS Controller (UN R157)', fontsize=13, fontweight='bold')
ax1.set_ylabel('Impact Speed (kph)', fontsize=12, fontweight='bold')
ax1.set_xlabel('Road Surface Condition', fontsize=12, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(conditions, fontsize=11)
ax1.yaxis.grid(True, linestyle='--', alpha=0.7)
ax1.set_axisbelow(True)

# --- Plot Set B (Scripted Physics) ---
for i, speed in enumerate(speeds):
    speed_data = df_scripted[df_scripted['Ego_Speed'] == speed].set_index('Condition').reindex(conditions)
    impact_speeds = speed_data['Impact_Speed_kph'].fillna(0).values
    offset = (i - 1) * width
    rects2 = ax2.bar(x + offset, impact_speeds, width, label=f'{speed} kph', color=colors[speed], edgecolor='black')
    ax2.bar_label(rects2, padding=3, fmt='%.1f')

ax2.set_title('Set B: Pure Physics (Friction Limited)', fontsize=13, fontweight='bold')
ax2.set_xlabel('Road Surface Condition', fontsize=12, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(conditions, fontsize=11)
ax2.yaxis.grid(True, linestyle='--', alpha=0.7)
ax2.set_axisbelow(True)

# Add one shared legend
handles, labels = ax1.get_legend_handles_labels()
fig.legend(handles, labels, loc='upper right', title='Initial Speed', fontsize=11, title_fontsize=12, bbox_to_anchor=(0.98, 0.95))

fig.tight_layout()

# Save the high-resolution image
plt.savefig(output_image, dpi=300, bbox_inches='tight')
print(f"Comparison graph successfully saved to: {output_image}")