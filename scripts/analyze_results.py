"""
analyze_results.py
==================
ADAS Thesis — Complete Results Analysis
HasnainBadar

Reads existing CSV files from C:\\adas-thesis\\results\\raw\\
Extracts real simulation metrics from dry runs.
Applies physics correction for wet/damp/icy surfaces.
Produces publication-quality figures for thesis.

Usage:
  cd C:\\adas-thesis
  python scripts\\analyze_results.py

Outputs (saved to C:\\adas-thesis\\results\\figures\\):
  aeb_stopping_distances.png
  aeb_speed_profiles.png
  aeb_surface_comparison.png
  acc_gap_profiles.png       (when ACC CSVs available)
  lka_deviation_profiles.png (when LKA CSVs available)
  summary_table.csv
"""

import os
import sys
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

# ── Paths ────────────────────────────────────────────────────────────────────
RAW_DIR = r"C:\adas-thesis\results\raw"
FIG_DIR = r"C:\adas-thesis\results\figures"
os.makedirs(FIG_DIR, exist_ok=True)

# ── Physics constants ─────────────────────────────────────────────────────────
G        = 9.81
MU       = {"dry": 1.0, "damp": 0.6, "wet": 0.4, "icy": 0.2}
SURFACES = ["dry", "damp", "wet", "icy"]
SPEEDS   = [50, 80, 120]

# ── Plot style ────────────────────────────────────────────────────────────────
SURF_COLORS = {
    "dry":  "#3ecf8e",
    "damp": "#f5a623",
    "wet":  "#4f9cf9",
    "icy":  "#a78bfa",
}
SURF_MARKERS = {"dry": "o", "damp": "s", "wet": "^", "icy": "D"}

plt.rcParams.update({
    "figure.facecolor":  "#0d0f12",
    "axes.facecolor":    "#13161b",
    "axes.edgecolor":    "#2a3040",
    "axes.labelcolor":   "#e8ecf2",
    "axes.titlecolor":   "#e8ecf2",
    "xtick.color":       "#8fa0b8",
    "ytick.color":       "#8fa0b8",
    "text.color":        "#e8ecf2",
    "grid.color":        "#2a3040",
    "grid.linestyle":    "--",
    "grid.alpha":        0.6,
    "legend.facecolor":  "#1a1e25",
    "legend.edgecolor":  "#2a3040",
    "font.family":       "monospace",
    "font.size":         9,
})

# ── CSV loader ────────────────────────────────────────────────────────────────
def load_csv(filepath):
    """Load a dat2csv file. Returns DataFrame with clean column names."""
    df = pd.read_csv(filepath, skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    return df

def get_entity(df, name):
    """Extract rows for a single entity by name."""
    return df[df["name"] == name].reset_index(drop=True)

def euclidean_dist(row1, row2):
    return math.sqrt((row1["x"]-row2["x"])**2 + (row1["y"]-row2["y"])**2)

# ── AEB metric extraction ─────────────────────────────────────────────────────
def extract_aeb_metrics(csv_path, speed_kph):
    """
    From an AEB scenario CSV extract:
      - speed profile over time
      - moment AEB fires (speed starts dropping)
      - actual stopping distance (Ego start pos to final pos)
      - gap to obstacle when stopped
      - collision flag
    """
    try:
        df  = load_csv(csv_path)
        ego = get_entity(df, "Ego")
        obs = get_entity(df, "Obstacle")

        if ego.empty:
            print(f"  WARNING: No Ego entity in {os.path.basename(csv_path)}")
            return None

        # Speed profile
        times  = ego["time"].values
        speeds = ego["speed"].values

        # AEB trigger: first timestep where speed drops below initial
        v_init      = speeds[0]
        trigger_idx = next((i for i in range(1, len(speeds))
                           if speeds[i] < v_init - 0.5), None)
        trigger_t   = times[trigger_idx] if trigger_idx else None

        # Stopping: first timestep where speed < 0.3 m/s
        stop_idx    = next((i for i in range(len(speeds))
                           if speeds[i] < 0.3), len(speeds)-1)
        stop_t      = times[stop_idx]

        # Positions
        x0, y0      = ego["x"].iloc[0], ego["y"].iloc[0]
        x_stop      = ego["x"].iloc[stop_idx]
        y_stop      = ego["y"].iloc[stop_idx]
        stop_dist   = math.sqrt((x_stop-x0)**2 + (y_stop-y0)**2)

        # Gap to obstacle at stop
        if not obs.empty:
            # match obs row closest to stop time
            obs_at_stop = obs.iloc[
                (obs["time"] - stop_t).abs().argsort().iloc[0]
            ]
            ego_at_stop = {"x": x_stop, "y": y_stop}
            gap = math.sqrt((x_stop - obs_at_stop["x"])**2 +
                            (y_stop - obs_at_stop["y"])**2)
            # subtract half car lengths (~2.25m each side)
            gap = max(0, gap - 4.5)
        else:
            gap = None

        collision = (gap is not None and gap < 1.0)

        return {
            "speed_kph":    speed_kph,
            "times":        times,
            "speeds":       speeds,
            "trigger_t":    trigger_t,
            "stop_t":       stop_t,
            "stop_dist_m":  round(stop_dist, 2),
            "gap_m":        round(gap, 2) if gap is not None else None,
            "collision":    collision,
            "v_init_ms":    round(v_init, 3),
        }
    except Exception as e:
        print(f"  ERROR reading {csv_path}: {e}")
        return None

# ── Physics correction ─────────────────────────────────────────────────────────
def physics_stopping_dist(v_ms, mu):
    """Theoretical stopping distance."""
    return round(v_ms**2 / (2 * mu * G), 2)

def correct_for_surface(dry_stop_dist, mu_surface):
    """
    Scale dry measured stopping distance to another surface.
    d = v²/(2μg) → d ∝ 1/μ
    d_surface = d_dry × (mu_dry / mu_surface)
    """
    return round(dry_stop_dist * (MU["dry"] / mu_surface), 2)

# ════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — AEB Speed Profiles (dry) — 3 speeds on one plot
# ════════════════════════════════════════════════════════════════════════════
def plot_aeb_speed_profiles(metrics_dry):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=False)
    fig.suptitle("AEB Speed Profiles — Dry Surface (Simulated)",
                 fontsize=12, fontweight="bold", y=1.02)

    speed_colors = {50: "#3ecf8e", 80: "#4f9cf9", 120: "#e84040"}

    for ax, (spd, m) in zip(axes, sorted(metrics_dry.items())):
        if m is None:
            ax.set_title(f"{spd} kph — no data")
            continue

        color = speed_colors.get(spd, "#e8ecf2")
        ax.plot(m["times"], m["speeds"] * 3.6,
                color=color, linewidth=1.8, label=f"{spd} kph")

        # AEB trigger marker
        if m["trigger_t"] is not None:
            ax.axvline(m["trigger_t"], color="#f5a623",
                       linestyle="--", linewidth=1, alpha=0.8)
            ax.text(m["trigger_t"] + 0.1,
                    m["speeds"][0] * 3.6 * 0.6,
                    "AEB", color="#f5a623", fontsize=8)

        ax.axhline(0, color="#2a3040", linewidth=0.8)
        ax.set_title(f"{spd} kph → stops in {m['stop_dist_m']}m",
                     fontsize=9)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Speed (kph)")
        ax.grid(True)
        ax.set_ylim(-5, spd * 1.15)
        ax.legend(fontsize=8)

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "aeb_speed_profiles.png")
    plt.savefig(out, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved: aeb_speed_profiles.png")
    return out

# ════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — AEB Stopping Distances — all surfaces (hybrid chart)
# ════════════════════════════════════════════════════════════════════════════
def plot_aeb_stopping_distances(metrics_dry):
    """
    Bar chart: stopping distance per speed per surface.
    Dry = measured from simulation.
    Damp/Wet/Icy = physics correction applied to dry measured value.
    """
    # Build data table
    data = {}
    for spd, m in metrics_dry.items():
        if m is None:
            continue
        d_dry = m["stop_dist_m"]
        data[spd] = {
            "dry":  d_dry,
            "damp": correct_for_surface(d_dry, MU["damp"]),
            "wet":  correct_for_surface(d_dry, MU["wet"]),
            "icy":  correct_for_surface(d_dry, MU["icy"]),
        }

    speeds_avail = sorted(data.keys())
    if not speeds_avail:
        print("  No dry data available for stopping distance chart.")
        return None

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.suptitle(
        "AEB Stopping Distance by Speed and Surface Condition\n"
        "Dry = Simulated (esmini)  |  Damp/Wet/Icy = Physics Model [d = v²÷(2μg)]",
        fontsize=10, fontweight="bold"
    )

    n_speeds  = len(speeds_avail)
    n_surfs   = 4
    bar_w     = 0.18
    x         = np.arange(n_speeds)

    for i, surf in enumerate(SURFACES):
        vals     = [data[spd][surf] for spd in speeds_avail]
        offset   = (i - n_surfs/2 + 0.5) * bar_w
        hatch    = "" if surf == "dry" else "///"
        alpha    = 1.0 if surf == "dry" else 0.75
        bars = ax.bar(x + offset, vals,
                      width=bar_w,
                      color=SURF_COLORS[surf],
                      alpha=alpha,
                      hatch=hatch,
                      label=f"{surf.capitalize()} (μ={MU[surf]})"
                            + (" ← simulated" if surf=="dry" else " ← physics model"),
                      edgecolor="#0d0f12",
                      linewidth=0.5)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + 1.5,
                    f"{val:.0f}m",
                    ha="center", va="bottom",
                    fontsize=7, color="#e8ecf2")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{s} kph" for s in speeds_avail], fontsize=10)
    ax.set_ylabel("Stopping Distance (m)", fontsize=10)
    ax.set_xlabel("Initial Ego Speed", fontsize=10)
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    ax.grid(True, axis="y")
    ax.set_ylim(0, max(
        data[spd]["icy"] for spd in speeds_avail
    ) * 1.18)

    # Annotation box
    ax.text(0.98, 0.97,
            "Hatched bars = physics-corrected projection\n"
            "Solid bars    = measured from esmini simulation\n"
            "Formula: d_surface = d_dry × (μ_dry ÷ μ_surface)",
            transform=ax.transAxes,
            ha="right", va="top", fontsize=7.5,
            bbox=dict(boxstyle="round,pad=0.4",
                      facecolor="#1a1e25",
                      edgecolor="#3a4558",
                      alpha=0.9))

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "aeb_stopping_distances.png")
    plt.savefig(out, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved: aeb_stopping_distances.png")
    return out

# ════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — AEB Surface Comparison Line Chart
# ════════════════════════════════════════════════════════════════════════════
def plot_aeb_surface_comparison(metrics_dry):
    """
    Line chart: stopping distance vs speed for each surface.
    Shows the scaling effect clearly.
    """
    speeds_ms = {50: 50/3.6, 80: 80/3.6, 120: 120/3.6}

    # Theoretical lines (smooth)
    v_range = np.linspace(10, 40, 200)
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.suptitle(
        "AEB Stopping Distance vs Speed — Surface Comparison\n"
        "Points = Simulated (dry) or Physics-Corrected (other surfaces)",
        fontsize=10, fontweight="bold"
    )

    for surf in SURFACES:
        mu = MU[surf]
        # Theoretical curve
        theory = v_range**2 / (2 * mu * G)
        ax.plot(v_range * 3.6, theory,
                color=SURF_COLORS[surf],
                linewidth=1.2,
                linestyle="--" if surf != "dry" else "-",
                alpha=0.5)

        # Measured/corrected points
        points_spd, points_d = [], []
        for spd, m in sorted(metrics_dry.items()):
            if m is None:
                continue
            d_dry = m["stop_dist_m"]
            if surf == "dry":
                d = d_dry
            else:
                d = correct_for_surface(d_dry, mu)
            points_spd.append(spd)
            points_d.append(d)

        marker = "o" if surf == "dry" else SURF_MARKERS[surf]
        ax.scatter(points_spd, points_d,
                   color=SURF_COLORS[surf],
                   marker=marker,
                   s=80,
                   zorder=5,
                   label=f"{surf.capitalize()} μ={mu}"
                         + (" (simulated)" if surf=="dry"
                            else " (physics model)"))

    ax.set_xlabel("Speed (kph)", fontsize=10)
    ax.set_ylabel("Stopping Distance (m)", fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(True)

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "aeb_surface_comparison.png")
    plt.savefig(out, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved: aeb_surface_comparison.png")
    return out

# ════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — AEB ADAS vs Baseline Comparison
# reads both S1_*_AEB_A and S1_*_baseline CSVs if available
# ════════════════════════════════════════════════════════════════════════════
def plot_aeb_adas_vs_baseline():
    """
    Compares Ego speed profile with and without AEB active.
    Uses S1_80kph_AEB_A.csv and S1_80kph_baseline.csv if present.
    """
    adas_path     = os.path.join(RAW_DIR, "S1_80kph_AEB_A.csv")
    baseline_path = os.path.join(RAW_DIR, "S1_80kph_baseline.csv")

    found_any = os.path.exists(adas_path) or os.path.exists(baseline_path)
    if not found_any:
        print("  Skipping ADAS vs baseline chart (no S1_80kph files found)")
        return None

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle("S1 AEB — ADAS Active vs Baseline (80 kph)",
                 fontsize=11, fontweight="bold")

    if os.path.exists(adas_path):
        df   = load_csv(adas_path)
        ego  = get_entity(df, "Ego")
        ax.plot(ego["time"], ego["speed"] * 3.6,
                color="#3ecf8e", linewidth=2,
                label="AEB Active — Ego stops safely")

    if os.path.exists(baseline_path):
        df   = load_csv(baseline_path)
        ego  = get_entity(df, "Ego")
        ax.plot(ego["time"], ego["speed"] * 3.6,
                color="#e84040", linewidth=2,
                linestyle="--",
                label="Baseline (no AEB) — constant speed → collision")

    ax.axhline(0, color="#2a3040", linewidth=0.8)
    ax.set_xlabel("Time (s)", fontsize=10)
    ax.set_ylabel("Speed (kph)", fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(True)
    ax.set_ylim(-5, 110)

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "aeb_adas_vs_baseline.png")
    plt.savefig(out, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved: aeb_adas_vs_baseline.png")
    return out

# ════════════════════════════════════════════════════════════════════════════
# FIGURE 5 — ACC Gap Profiles (when CSV available)
# ════════════════════════════════════════════════════════════════════════════
def plot_acc_gap_profiles():
    """
    For each ACC dry CSV: plot distance between Ego and NPC over time.
    Shows how ALKS maintains or fails to maintain gap.
    """
    acc_files = {
        "gentle":   "S_ACC_dry_gentle.csv",
        "moderate": "S_ACC_dry_moderate.csv",
        "hard":     "S_ACC_dry_hard.csv",
    }

    found = {k: os.path.join(RAW_DIR, v)
             for k, v in acc_files.items()
             if os.path.exists(os.path.join(RAW_DIR, v))}

    if not found:
        print("  Skipping ACC gap chart (no ACC CSV files found yet)")
        print("  Run S_results/ACC scenarios first")
        return None

    fig, axes = plt.subplots(1, len(found), figsize=(5*len(found), 5),
                             sharey=True)
    if len(found) == 1:
        axes = [axes]
    fig.suptitle("ACC Gap to NPC Over Time — Dry Surface (Simulated)",
                 fontsize=11, fontweight="bold")

    decel_labels = {"gentle":"2.0 m/s²","moderate":"5.0 m/s²","hard":"8.0 m/s²"}
    colors       = {"gentle":"#3ecf8e","moderate":"#f5a623","hard":"#e84040"}

    for ax, (label, path) in zip(axes, found.items()):
        df  = load_csv(path)
        ego = get_entity(df, "Ego")
        npc = get_entity(df, "NPC")

        if npc.empty:
            ax.set_title(f"{label} — NPC entity not found")
            continue

        # Merge on time
        merged = pd.merge(
            ego[["time","x","y","speed"]],
            npc[["time","x","y","speed"]],
            on="time", suffixes=("_ego","_npc")
        )
        merged["gap"] = np.sqrt(
            (merged["x_ego"]-merged["x_npc"])**2 +
            (merged["y_ego"]-merged["y_npc"])**2
        ) - 4.5  # subtract car length
        merged["gap"] = merged["gap"].clip(lower=0)

        ax.plot(merged["time"], merged["gap"],
                color=colors[label], linewidth=1.8)
        ax.axvline(5, color="#f5a623", linestyle="--",
                   linewidth=1, alpha=0.7, label="NPC brakes at t=5s")
        ax.axhline(0, color="#e84040", linewidth=1,
                   linestyle=":", alpha=0.6, label="Collision threshold")

        min_gap = merged["gap"].min()
        ax.set_title(
            f"{label.capitalize()} NPC decel {decel_labels[label]}\n"
            f"Min gap = {min_gap:.1f}m "
            f"({'SAFE ✓' if min_gap > 0.5 else 'COLLISION ✗'})",
            fontsize=9
        )
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Gap to NPC (m)")
        ax.legend(fontsize=7)
        ax.grid(True)

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "acc_gap_profiles.png")
    plt.savefig(out, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved: acc_gap_profiles.png")
    return out

# ════════════════════════════════════════════════════════════════════════════
# FIGURE 6 — LKA Lateral Deviation (when CSV available)
# ════════════════════════════════════════════════════════════════════════════
def plot_lka_deviation():
    """
    For each LKA dry CSV: plot lateral offset over time.
    Shows drift and correction.
    """
    lka_files = {
        "slow": "S_LKA_dry_slow.csv",
        "med":  "S_LKA_dry_med.csv",
        "fast": "S_LKA_dry_fast.csv",
    }

    found = {k: os.path.join(RAW_DIR, v)
             for k, v in lka_files.items()
             if os.path.exists(os.path.join(RAW_DIR, v))}

    if not found:
        print("  Skipping LKA chart (no LKA CSV files found yet)")
        print("  Run S_results/LKA scenarios first")
        return None

    fig, axes = plt.subplots(1, len(found), figsize=(5*len(found), 5),
                             sharey=True)
    if len(found) == 1:
        axes = [axes]
    fig.suptitle("LKA Lateral Deviation Over Time — Dry Surface (Simulated)",
                 fontsize=11, fontweight="bold")

    drift_colors = {"slow":"#3ecf8e","med":"#f5a623","fast":"#e84040"}

    for ax, (label, path) in zip(axes, found.items()):
        df  = load_csv(path)
        ego = get_entity(df, "Ego")

        # Lateral deviation = perpendicular distance from initial y
        y0  = ego["y"].iloc[0]
        dev = (ego["y"] - y0).abs()

        ax.plot(ego["time"], dev,
                color=drift_colors[label], linewidth=1.8)
        ax.axvline(3, color="#f5a623", linestyle="--",
                   linewidth=1, alpha=0.7, label="Drift starts t=3s")
        ax.axhline(1.875, color="#a78bfa", linestyle=":",
                   linewidth=1, alpha=0.7, label="Lane boundary (1.875m)")

        max_dev = dev.max()
        ax.set_title(
            f"Drift rate: {label}\n"
            f"Max deviation = {max_dev:.2f}m "
            f"({'Lane crossed!' if max_dev > 1.875 else 'Stayed in lane ✓'})",
            fontsize=9
        )
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Lateral Deviation (m)")
        ax.legend(fontsize=7)
        ax.grid(True)

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "lka_deviation_profiles.png")
    plt.savefig(out, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved: lka_deviation_profiles.png")
    return out

# ════════════════════════════════════════════════════════════════════════════
# SUMMARY TABLE — CSV export for thesis
# ════════════════════════════════════════════════════════════════════════════
def build_summary_table(metrics_dry):
    rows = []
    for spd, m in sorted(metrics_dry.items()):
        if m is None:
            continue
        d_dry = m["stop_dist_m"]
        rows.append({
            "Scenario":         f"AEB {spd}kph",
            "Speed_kph":        spd,
            "Surface":          "dry",
            "Data_source":      "simulated",
            "Stopping_dist_m":  d_dry,
            "Gap_at_stop_m":    m["gap_m"],
            "Collision":        m["collision"],
            "AEB_trigger_t_s":  round(m["trigger_t"], 3) if m["trigger_t"] else None,
            "Ego_stop_t_s":     round(m["stop_t"], 3),
        })
        for surf in ["damp","wet","icy"]:
            d_surf = correct_for_surface(d_dry, MU[surf])
            rows.append({
                "Scenario":         f"AEB {spd}kph",
                "Speed_kph":        spd,
                "Surface":          surf,
                "Data_source":      "physics_model",
                "Stopping_dist_m":  d_surf,
                "Gap_at_stop_m":    None,
                "Collision":        None,
                "AEB_trigger_t_s":  None,
                "Ego_stop_t_s":     None,
            })

    df = pd.DataFrame(rows)
    out = os.path.join(FIG_DIR, "summary_table.csv")
    df.to_csv(out, index=False)
    print(f"  Saved: summary_table.csv")
    return df

# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("ADAS THESIS — RESULTS ANALYSIS")
    print("=" * 60)

    # ── Load AEB dry CSVs ──────────────────────────────────────────────────
    print("\n[1] Loading AEB dry simulation data...")
    metrics_dry = {}
    for spd in SPEEDS:
        # Try S_results naming first, fall back to S_friction naming
        candidates = [
            os.path.join(RAW_DIR, f"S_AEB_dry_{spd}kph.csv"),
            os.path.join(RAW_DIR, f"S1_AEB_dry_{spd}kph.csv"),
        ]
        found = next((p for p in candidates if os.path.exists(p)), None)
        if found:
            m = extract_aeb_metrics(found, spd)
            metrics_dry[spd] = m
            if m:
                print(f"  {spd}kph: stop_dist={m['stop_dist_m']}m  "
                      f"gap={m['gap_m']}m  "
                      f"trigger_t={m['trigger_t']}s  "
                      f"{'COLLISION' if m['collision'] else 'SAFE'}")
        else:
            print(f"  {spd}kph: no CSV found — skipping")
            metrics_dry[spd] = None

    if all(v is None for v in metrics_dry.values()):
        print("\nNo AEB CSV data found. Please run scenarios first.")
        print("Run: PowerShell -ExecutionPolicy Bypass -File")
        print("     C:\\adas-thesis\\scenarios\\S_results\\run_all_S_results.ps1")
        sys.exit(1)

    # ── Figures ───────────────────────────────────────────────────────────
    print("\n[2] Generating figures...")
    plot_aeb_speed_profiles(metrics_dry)
    plot_aeb_stopping_distances(metrics_dry)
    plot_aeb_surface_comparison(metrics_dry)
    plot_aeb_adas_vs_baseline()
    plot_acc_gap_profiles()
    plot_lka_deviation()

    # ── Summary table ─────────────────────────────────────────────────────
    print("\n[3] Building summary table...")
    df = build_summary_table(metrics_dry)
    print("\nSUMMARY:")
    print(df[["Scenario","Surface","Stopping_dist_m","Data_source"]].to_string(index=False))

    print(f"\n{'='*60}")
    print(f"All outputs saved to: {FIG_DIR}")
    print(f"{'='*60}")
    print("\nFigures produced:")
    print("  aeb_speed_profiles.png      — speed vs time, 3 speeds")
    print("  aeb_stopping_distances.png  — bar chart all surfaces (HYBRID)")
    print("  aeb_surface_comparison.png  — line chart speed vs stop dist")
    print("  aeb_adas_vs_baseline.png    — AEB on/off comparison")
    print("  acc_gap_profiles.png        — when ACC CSVs available")
    print("  lka_deviation_profiles.png  — when LKA CSVs available")
    print("  summary_table.csv           — all numbers for thesis tables")
    print("\nNext: run ACC and LKA scenarios then re-run this script")

if __name__ == "__main__":
    main()
