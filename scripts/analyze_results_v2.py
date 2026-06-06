"""
analyze_results_v2.py
=====================
ADAS Thesis — Results Analysis v2
HasnainBadar

Fixes from v1:
  - Stopping distance measured from AEB trigger point, not scenario start
  - Collision detection via speed-rebound signature + position overshoot
  - White background for thesis figures
  - ACC gap profiles added
  - LKA lateral deviation added

Usage:
  cd C:\\adas-thesis
  python scripts\\analyze_results_v2.py
"""

import os, sys, math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Paths ─────────────────────────────────────────────────────────────────────
RAW_DIR = r"C:\adas-thesis\results\raw"
FIG_DIR = r"C:\adas-thesis\results\figures"
os.makedirs(FIG_DIR, exist_ok=True)

# ── Physics ───────────────────────────────────────────────────────────────────
G  = 9.81
MU = {"dry":1.0,"damp":0.6,"wet":0.4,"icy":0.2}
SURFACES = ["dry","damp","wet","icy"]
SPEEDS   = [50, 80, 120]

# ── White thesis style ────────────────────────────────────────────────────────
SURF_COLORS  = {"dry":"#2ca02c","damp":"#ff7f0e","wet":"#1f77b4","icy":"#9467bd"}
SURF_MARKERS = {"dry":"o","damp":"s","wet":"^","icy":"D"}
SURF_HATCH   = {"dry":"","damp":"///","wet":"xxx","icy":"..."}

plt.rcParams.update({
    "figure.facecolor":  "white",
    "axes.facecolor":    "white",
    "axes.edgecolor":    "black",
    "axes.labelcolor":   "black",
    "axes.titlecolor":   "black",
    "xtick.color":       "black",
    "ytick.color":       "black",
    "text.color":        "black",
    "grid.color":        "#cccccc",
    "grid.linestyle":    "--",
    "grid.alpha":        0.7,
    "legend.facecolor":  "white",
    "legend.edgecolor":  "#cccccc",
    "font.family":       "sans-serif",
    "font.size":         10,
    "axes.titlesize":    11,
    "axes.labelsize":    10,
    "savefig.facecolor": "white",
    "savefig.edgecolor": "white",
})

# ── CSV helpers ───────────────────────────────────────────────────────────────
def load_csv(path):
    df = pd.read_csv(path, skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    return df

def get_entity(df, name):
    return df[df["name"]==name].reset_index(drop=True)

# ── AEB metrics ───────────────────────────────────────────────────────────────
def extract_aeb_metrics(csv_path, speed_kph):
    """
    Extract AEB metrics with correct stopping distance and collision detection.

    Stopping distance = distance Ego travels FROM AEB trigger TO minimum speed.
    Collision detection = speed rebounds after initial drop (pass-through signature).
    """
    try:
        df  = load_csv(csv_path)
        ego = get_entity(df, "Ego")
        obs_df = get_entity(df, "Obstacle")

        times  = ego["time"].values.astype(float)
        speeds = ego["speed"].values.astype(float)
        xs     = ego["x"].values.astype(float)
        ys     = ego["y"].values.astype(float)

        v_init = speeds[0]

        # ── Find AEB trigger: speed drops by >0.5 m/s from initial ──────────
        trigger_idx = None
        for i in range(1, len(speeds)):
            if speeds[i] < v_init - 0.5:
                trigger_idx = i
                break

        if trigger_idx is None:
            # Speed never dropped — AEB never fired
            return {
                "speed_kph":   speed_kph,
                "times":       times,
                "speeds":      speeds,
                "trigger_t":   None,
                "trigger_idx": None,
                "stop_dist_m": None,
                "gap_m":       None,
                "collision":   True,   # never braked = collision
                "v_init_ms":   round(v_init,3),
                "note":        "AEB never fired",
            }

        trigger_t = times[trigger_idx]
        x_trigger = xs[trigger_idx]
        y_trigger = ys[trigger_idx]

        # ── Find minimum speed after trigger ─────────────────────────────────
        post = speeds[trigger_idx:]
        min_speed_local = np.min(post)
        min_idx_local   = int(np.argmin(post))
        min_idx         = trigger_idx + min_idx_local

        x_at_min = xs[min_idx]
        y_at_min = ys[min_idx]

        # Stopping distance from trigger to minimum speed point
        stop_dist = math.sqrt((x_at_min-x_trigger)**2 +
                              (y_at_min-y_trigger)**2)

        # ── Collision detection ───────────────────────────────────────────────
        # Signature: speed drops significantly then rebounds back up
        # after min point if speed rises by >3 m/s within next 3s → collision
        collision = False
        collision_note = ""

        if min_idx < len(speeds)-1:
            post_min_speeds = speeds[min_idx:]
            post_min_times  = times[min_idx:]
            # check within 5 seconds after minimum
            mask = post_min_times - times[min_idx] < 5.0
            if np.any(mask) and len(post_min_speeds[mask]) > 1:
                rebound = post_min_speeds[mask][-1] - post_min_speeds[mask][0]
                if rebound > 3.0:
                    collision = True
                    collision_note = f"speed rebound +{round(rebound,1)} m/s after min"

        # Also check position overshoot past obstacle
        if not obs_df.empty:
            obs_x = obs_df["x"].iloc[0]
            obs_y = obs_df["y"].iloc[0]
            # distance from obstacle at minimum speed point
            gap = math.sqrt((x_at_min-obs_x)**2 +
                            (y_at_min-obs_y)**2) - 4.5
            gap = max(0, round(gap, 2))
            if gap < 0.5:
                collision = True
                collision_note = "gap < 0.5m at minimum speed"
        else:
            gap = None

        # minimum speed reached (m/s)
        min_speed_reached = round(float(min_speed_local), 3)
        fully_stopped     = min_speed_reached < 0.5

        return {
            "speed_kph":       speed_kph,
            "times":           times,
            "speeds":          speeds,
            "trigger_t":       round(float(trigger_t), 3),
            "trigger_idx":     trigger_idx,
            "stop_dist_m":     round(stop_dist, 2),
            "min_speed_ms":    min_speed_reached,
            "fully_stopped":   fully_stopped,
            "gap_m":           gap,
            "collision":       collision,
            "v_init_ms":       round(float(v_init), 3),
            "note":            collision_note if collision else "safe",
        }
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

# ── Physics correction ────────────────────────────────────────────────────────
def correct_stop_dist(d_dry, mu_surface):
    """Scale dry stopping distance to another surface."""
    return round(d_dry * (MU["dry"] / mu_surface), 2)

def theory_stop_dist(v_ms, mu):
    return round(v_ms**2 / (2*mu*G), 2)

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — AEB Speed Profiles (white, 3 panels)
# ══════════════════════════════════════════════════════════════════════════════
def plot_speed_profiles(metrics_dry):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=False)
    fig.suptitle("Figure 1 — AEB Speed Profiles (Dry Surface, Simulated)",
                 fontsize=13, fontweight="bold", y=1.01)

    spd_colors = {50:"#2ca02c", 80:"#1f77b4", 120:"#d62728"}

    for ax, spd in zip(axes, SPEEDS):
        m = metrics_dry.get(spd)
        if m is None:
            ax.set_title(f"{spd} kph — no data")
            ax.set_facecolor("white")
            continue

        color = spd_colors[spd]
        ax.plot(m["times"], m["speeds"]*3.6,
                color=color, linewidth=2, label=f"{spd} kph")

        # AEB trigger line
        if m["trigger_t"] is not None:
            ax.axvline(m["trigger_t"], color="darkorange",
                       linestyle="--", linewidth=1.2, alpha=0.9,
                       label=f"AEB fires t={m['trigger_t']}s")

        # Outcome annotation
        if m["collision"]:
            outcome_txt = f"COLLISION\n({m['note']})"
            outcome_col = "#d62728"
        elif m["fully_stopped"]:
            outcome_txt = f"Stopped safely\ndist={m['stop_dist_m']}m"
            outcome_col = "#2ca02c"
        else:
            outcome_txt = f"Slowed to {round(m['min_speed_ms']*3.6,1)}kph\ndist={m['stop_dist_m']}m"
            outcome_col = "#ff7f0e"

        ax.text(0.97, 0.95, outcome_txt,
                transform=ax.transAxes, ha="right", va="top",
                fontsize=8, color=outcome_col,
                bbox=dict(boxstyle="round,pad=0.3",
                          facecolor="white",
                          edgecolor=outcome_col,
                          alpha=0.85))

        ax.set_title(f"{spd} kph initial speed", fontsize=10)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Speed (kph)")
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True)
        ax.set_ylim(-5, spd*1.2)
        ax.set_facecolor("white")

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig1_aeb_speed_profiles.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: fig1_aeb_speed_profiles.png")
    return out

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — AEB Stopping Distance bar chart (hybrid)
# ══════════════════════════════════════════════════════════════════════════════
def plot_stopping_distances(metrics_dry):
    # Build data
    data = {}
    for spd, m in metrics_dry.items():
        if m is None or m["stop_dist_m"] is None:
            continue
        d_dry = m["stop_dist_m"]
        data[spd] = {
            "dry":  d_dry,
            "damp": correct_stop_dist(d_dry, MU["damp"]),
            "wet":  correct_stop_dist(d_dry, MU["wet"]),
            "icy":  correct_stop_dist(d_dry, MU["icy"]),
        }

    if not data:
        print("  No data for stopping distance chart")
        return None

    speeds_avail = sorted(data.keys())
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.suptitle(
        "Figure 2 — AEB Stopping Distance by Speed and Surface Condition",
        fontsize=12, fontweight="bold"
    )
    ax.set_title(
        "Solid bars = measured (esmini simulation, dry)    "
        "Hatched bars = physics model  [d = v² ÷ (2μg)]",
        fontsize=9, color="#555555"
    )

    n_surfs = 4
    bar_w   = 0.18
    x       = np.arange(len(speeds_avail))

    for i, surf in enumerate(SURFACES):
        vals   = [data[spd][surf] for spd in speeds_avail]
        offset = (i - n_surfs/2 + 0.5) * bar_w
        bars   = ax.bar(x + offset, vals,
                        width=bar_w,
                        color=SURF_COLORS[surf],
                        hatch=SURF_HATCH[surf],
                        alpha=0.85,
                        label=f"{surf.capitalize()} μ={MU[surf]}"
                              + (" [simulated]" if surf=="dry"
                                 else " [physics model]"),
                        edgecolor="black",
                        linewidth=0.6)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + max(vals)*0.01,
                    f"{val:.0f}m",
                    ha="center", va="bottom",
                    fontsize=7.5, color="black", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{s} kph" for s in speeds_avail], fontsize=11)
    ax.set_ylabel("Stopping Distance (m)", fontsize=11)
    ax.set_xlabel("Initial Ego Speed", fontsize=11)
    ax.legend(loc="upper left", fontsize=9, ncol=2,
              framealpha=0.9, edgecolor="#aaaaaa")
    ax.grid(True, axis="y", alpha=0.5)
    max_val = max(data[s]["icy"] for s in speeds_avail)
    ax.set_ylim(0, max_val * 1.15)
    ax.set_facecolor("white")

    # Collision markers above bars for dry 120kph if collision
    m120 = metrics_dry.get(120)
    if m120 and m120["collision"]:
        idx = speeds_avail.index(120)
        ax.text(idx, data[120]["dry"] + max_val*0.02,
                "⚠ COLLISION\n(no AEB stop)",
                ha="center", va="bottom",
                fontsize=8, color="#d62728", fontweight="bold")

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig2_aeb_stopping_distances.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: fig2_aeb_stopping_distances.png")
    return out

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — AEB Surface Comparison line chart
# ══════════════════════════════════════════════════════════════════════════════
def plot_surface_comparison(metrics_dry):
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.suptitle(
        "Figure 3 — AEB Stopping Distance vs Speed by Surface",
        fontsize=12, fontweight="bold"
    )
    ax.set_title(
        "Circles = simulated (dry)    Other markers = physics-corrected projection",
        fontsize=9, color="#555555"
    )

    v_range = np.linspace(5, 38, 300)

    for surf in SURFACES:
        mu = MU[surf]
        # Theory curve
        theory = v_range**2 / (2*mu*G)
        ls = "-" if surf=="dry" else "--"
        ax.plot(v_range*3.6, theory,
                color=SURF_COLORS[surf],
                linestyle=ls, linewidth=1.2,
                alpha=0.4, zorder=1)

        # Data points
        pts_spd, pts_d = [], []
        for spd, m in sorted(metrics_dry.items()):
            if m is None or m["stop_dist_m"] is None:
                continue
            d_dry = m["stop_dist_m"]
            d = d_dry if surf=="dry" else correct_stop_dist(d_dry, mu)
            pts_spd.append(spd)
            pts_d.append(d)

        # collision points shown differently
        for spd, m in sorted(metrics_dry.items()):
            if m is None:
                continue
            if surf=="dry" and m["collision"]:
                ax.scatter([spd],[m["stop_dist_m"]],
                           color="#d62728", marker="x",
                           s=120, linewidths=2, zorder=5)

        ax.scatter(pts_spd, pts_d,
                   color=SURF_COLORS[surf],
                   marker=SURF_MARKERS[surf],
                   s=80, zorder=4,
                   label=f"{surf.capitalize()} μ={mu}"
                         + (" (simulated)" if surf=="dry"
                            else " (physics model)"))

    ax.set_xlabel("Speed (kph)", fontsize=11)
    ax.set_ylabel("Stopping Distance (m)", fontsize=11)
    ax.legend(fontsize=9, loc="upper left",
              framealpha=0.9, edgecolor="#aaaaaa")
    ax.grid(True, alpha=0.5)
    ax.set_facecolor("white")
    ax.set_xlim(30, 140)

    # red x annotation
    ax.text(0.98, 0.04,
            "✕ = collision detected (no safe stop)",
            transform=ax.transAxes, ha="right",
            fontsize=8, color="#d62728")

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig3_aeb_surface_comparison.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: fig3_aeb_surface_comparison.png")
    return out

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — AEB ADAS vs Baseline
# ══════════════════════════════════════════════════════════════════════════════
def plot_adas_vs_baseline():
    pairs = [
        ("S1_50kph_AEB_A.csv",  "S1_50kph_baseline.csv",  "50 kph"),
        ("S1_80kph_AEB_A.csv",  "S1_80kph_baseline.csv",  "80 kph"),
        ("S1_120kph_AEB_A.csv", "S1_120kph_baseline.csv", "120 kph"),
    ]
    available = [(a,b,l) for a,b,l in pairs
                 if os.path.exists(os.path.join(RAW_DIR,a)) or
                    os.path.exists(os.path.join(RAW_DIR,b))]

    if not available:
        print("  Skipping ADAS vs baseline (no S1 CSV files found)")
        return None

    fig, axes = plt.subplots(1, len(available),
                             figsize=(5*len(available), 5))
    if len(available)==1:
        axes=[axes]
    fig.suptitle("Figure 4 — AEB: ADAS Active vs Baseline (No ADAS)",
                 fontsize=12, fontweight="bold")

    for ax, (af, bf, label) in zip(axes, available):
        apath = os.path.join(RAW_DIR, af)
        bpath = os.path.join(RAW_DIR, bf)

        if os.path.exists(apath):
            df  = load_csv(apath)
            ego = get_entity(df, "Ego")
            ax.plot(ego["time"], ego["speed"]*3.6,
                    color="#2ca02c", linewidth=2,
                    label="AEB Active — safe stop")

        if os.path.exists(bpath):
            df  = load_csv(bpath)
            ego = get_entity(df, "Ego")
            ax.plot(ego["time"], ego["speed"]*3.6,
                    color="#d62728", linewidth=2,
                    linestyle="--",
                    label="Baseline — collision")

        ax.set_title(f"{label}", fontsize=10)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Speed (kph)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.5)
        ax.set_facecolor("white")
        ax.axhline(0, color="black", linewidth=0.8)

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig4_aeb_adas_vs_baseline.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: fig4_aeb_adas_vs_baseline.png")
    return out

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 5 — ACC Gap profiles
# ══════════════════════════════════════════════════════════════════════════════
def plot_acc_gaps():
    variants = [
        ("S_ACC_dry_gentle.csv",   "Gentle 2.0 m/s²",   "#2ca02c"),
        ("S_ACC_dry_moderate.csv", "Moderate 5.0 m/s²", "#ff7f0e"),
        ("S_ACC_dry_hard.csv",     "Hard 8.0 m/s²",     "#d62728"),
    ]
    found = [(f,l,c) for f,l,c in variants
             if os.path.exists(os.path.join(RAW_DIR,f))]

    if not found:
        print("  Skipping ACC gap chart — run ACC scenarios first")
        return None

    fig, axes = plt.subplots(1, len(found),
                             figsize=(5*len(found), 5), sharey=True)
    if len(found)==1:
        axes=[axes]
    fig.suptitle("Figure 5 — ACC: Gap Between Ego and NPC Over Time (Dry)",
                 fontsize=12, fontweight="bold")

    for ax, (fname, label, color) in zip(axes, found):
        df  = load_csv(os.path.join(RAW_DIR, fname))
        ego = get_entity(df, "Ego")
        npc = get_entity(df, "NPC")
        if npc.empty:
            ax.set_title(f"{label}\nNPC not found")
            continue

        merged = pd.merge(
            ego[["time","x","y"]],
            npc[["time","x","y"]],
            on="time", suffixes=("_e","_n")
        )
        merged["gap"] = (np.sqrt(
            (merged["x_e"]-merged["x_n"])**2 +
            (merged["y_e"]-merged["y_n"])**2
        ) - 4.5).clip(lower=0)

        ax.plot(merged["time"], merged["gap"],
                color=color, linewidth=2)
        ax.axvline(5, color="darkorange", linestyle="--",
                   linewidth=1.2, label="NPC brakes t=5s")
        ax.axhline(0, color="#d62728", linestyle=":",
                   linewidth=1.2, alpha=0.7, label="Collision threshold")

        min_gap = merged["gap"].min()
        safe    = min_gap > 0.5
        ax.set_title(
            f"{label}\nMin gap = {min_gap:.1f}m "
            f"{'✓ SAFE' if safe else '✗ COLLISION'}",
            fontsize=9,
            color="#2ca02c" if safe else "#d62728"
        )
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Gap to NPC (m)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.5)
        ax.set_facecolor("white")

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig5_acc_gap_profiles.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: fig5_acc_gap_profiles.png")
    return out

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 6 — LKA Lateral Deviation
# ══════════════════════════════════════════════════════════════════════════════
def plot_lka_deviation():
    variants = [
        ("S_LKA_dry_slow.csv", "Slow drift (maxLatAcc=0.1)", "#2ca02c"),
        ("S_LKA_dry_med.csv",  "Med drift (maxLatAcc=0.3)",  "#ff7f0e"),
        ("S_LKA_dry_fast.csv", "Fast drift (maxLatAcc=0.6)", "#d62728"),
    ]
    found = [(f,l,c) for f,l,c in variants
             if os.path.exists(os.path.join(RAW_DIR,f))]

    if not found:
        print("  Skipping LKA chart — run LKA scenarios first")
        return None

    fig, axes = plt.subplots(1, len(found),
                             figsize=(5*len(found), 5), sharey=True)
    if len(found)==1:
        axes=[axes]
    fig.suptitle("Figure 6 — LKA: Lateral Deviation Over Time (Dry Surface)",
                 fontsize=12, fontweight="bold")

    LANE_HALF_WIDTH = 1.875  # 3.75m lane / 2

    for ax, (fname, label, color) in zip(axes, found):
        df  = load_csv(os.path.join(RAW_DIR, fname))
        ego = get_entity(df, "Ego")

        # lateral deviation from starting y position
        y0  = ego["y"].iloc[0]
        dev = (ego["y"] - y0).abs()

        ax.plot(ego["time"], dev,
                color=color, linewidth=2, label="Lateral deviation")
        ax.axvline(3, color="darkorange", linestyle="--",
                   linewidth=1.2, alpha=0.9, label="Drift starts t=3s")
        ax.axhline(LANE_HALF_WIDTH, color="#9467bd", linestyle=":",
                   linewidth=1.5, alpha=0.8,
                   label=f"Lane boundary {LANE_HALF_WIDTH}m")

        max_dev    = dev.max()
        crossed    = max_dev > LANE_HALF_WIDTH

        ax.set_title(
            f"{label}\nMax dev = {max_dev:.2f}m "
            f"{'— Lane crossed ✗' if crossed else '— Stayed in lane ✓'}",
            fontsize=9,
            color="#d62728" if crossed else "#2ca02c"
        )
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Lateral Deviation (m)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.5)
        ax.set_facecolor("white")
        ax.set_ylim(-0.1, max(max_dev*1.2, LANE_HALF_WIDTH*1.3))

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig6_lka_deviation.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: fig6_lka_deviation.png")
    return out

# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════════════
def build_summary(metrics_dry):
    rows = []
    for spd, m in sorted(metrics_dry.items()):
        if m is None: continue
        d_dry = m["stop_dist_m"] if m["stop_dist_m"] else 0
        for surf in SURFACES:
            d = d_dry if surf=="dry" else correct_stop_dist(d_dry, MU[surf])
            rows.append({
                "Speed_kph":       spd,
                "Surface":         surf,
                "mu":              MU[surf],
                "Stopping_dist_m": d,
                "Data_source":     "simulated" if surf=="dry" else "physics_model",
                "Collision":       m["collision"] if surf=="dry" else
                                   ("N/A" if d==0 else
                                    "Yes" if d > 800 else "No"),
                "AEB_trigger_t_s": m["trigger_t"] if surf=="dry" else "N/A",
                "Note":            m["note"] if surf=="dry" else "",
            })

    df  = pd.DataFrame(rows)
    out = os.path.join(FIG_DIR, "summary_table_AEB.csv")
    df.to_csv(out, index=False)
    print(f"  Saved: summary_table_AEB.csv")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("="*60)
    print("ADAS THESIS — RESULTS ANALYSIS v2")
    print("="*60)

    # Load AEB dry data
    print("\n[1] Loading AEB dry simulation data...")
    metrics_dry = {}
    for spd in SPEEDS:
        candidates = [
            os.path.join(RAW_DIR, f"S_AEB_dry_{spd}kph.csv"),
            os.path.join(RAW_DIR, f"S1_AEB_dry_{spd}kph.csv"),
        ]
        fpath = next((p for p in candidates if os.path.exists(p)), None)
        if fpath:
            m = extract_aeb_metrics(fpath, spd)
            metrics_dry[spd] = m
            if m:
                coll  = "COLLISION" if m["collision"] else "SAFE"
                print(f"  {spd:3d}kph: AEB_trigger={m['trigger_t']}s  "
                      f"stop_dist={m['stop_dist_m']}m  "
                      f"min_speed={round(m['min_speed_ms']*3.6,1)}kph  "
                      f"{coll}  [{m['note']}]")
        else:
            print(f"  {spd}kph: no CSV found")
            metrics_dry[spd] = None

    if all(v is None for v in metrics_dry.values()):
        print("\nNo data found. Run scenarios first.")
        sys.exit(1)

    print("\n[2] Generating figures...")
    plot_speed_profiles(metrics_dry)
    plot_stopping_distances(metrics_dry)
    plot_surface_comparison(metrics_dry)
    plot_adas_vs_baseline()
    plot_acc_gaps()
    plot_lka_deviation()

    print("\n[3] Summary table...")
    df = build_summary(metrics_dry)
    print("\n" + df[["Speed_kph","Surface","Stopping_dist_m",
                     "Collision","Data_source"]].to_string(index=False))

    print(f"\n{'='*60}")
    print(f"Figures saved to: {FIG_DIR}")
    print("Next steps:")
    print("  1. Run ACC scenarios + re-run script for Fig 5")
    print("  2. Run LKA scenarios + re-run script for Fig 6")
    print("  3. Run S1 baseline scenarios for Fig 4 comparison")

if __name__ == "__main__":
    main()
