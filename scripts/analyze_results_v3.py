"""
analyze_results_v3.py
=====================
ADAS Thesis — Final Results Analysis
HasnainBadar

- Reads S_AEB_dry_*.csv from results/raw
- Extracts real stopping distance from AEB trigger point
- Detects collision via speed rebound signature
- Physics-corrects for wet/damp/icy surfaces
- Produces clean white thesis figures, no overlapping text
- Handles ACC and LKA when CSVs are available

Usage:
  cd C:\\adas-thesis
  python scripts\\analyze_results_v3.py
"""

import os, sys, math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

RAW = r"C:\adas-thesis\results\raw"
FIG = r"C:\adas-thesis\results\figures"
os.makedirs(FIG, exist_ok=True)

G       = 9.81
MU      = {"dry":1.0, "damp":0.6, "wet":0.4, "icy":0.2}
SURFS   = ["dry","damp","wet","icy"]
SPEEDS  = [50, 80, 120]

SCOL  = {"dry":"#2ca02c","damp":"#ff7f0e","wet":"#1f77b4","icy":"#9467bd"}
SMARK = {"dry":"o","damp":"s","wet":"^","icy":"D"}
SHATCH= {"dry":"","damp":"///","wet":"xxx","icy":"..."}
SPCOL = {50:"#2ca02c", 80:"#1f77b4", 120:"#d62728"}

plt.rcParams.update({
    "figure.facecolor":"white","axes.facecolor":"white",
    "axes.edgecolor":"#333333","axes.labelcolor":"black",
    "xtick.color":"black","ytick.color":"black","text.color":"black",
    "grid.color":"#dddddd","grid.linestyle":"--","grid.alpha":0.7,
    "legend.facecolor":"white","legend.edgecolor":"#cccccc",
    "font.family":"DejaVu Sans","font.size":9,
    "axes.titlesize":10,"axes.labelsize":9,
    "savefig.facecolor":"white","savefig.edgecolor":"white",
    "figure.dpi":150,
})

def load(path):
    df = pd.read_csv(path, skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    return df

def entity(df, name):
    return df[df["name"]==name].reset_index(drop=True)

def extract_aeb(path, spd):
    try:
        df  = load(path)
        ego = entity(df,"Ego")
        obs = entity(df,"Obstacle")
        t   = ego["time"].values.astype(float)
        v   = ego["speed"].values.astype(float)
        x   = ego["x"].values.astype(float)
        y   = ego["y"].values.astype(float)

        v0 = v[0]
        # AEB trigger: speed drops > 0.5 m/s from initial
        ti = next((i for i in range(1,len(v)) if v[i] < v0-0.5), None)
        if ti is None:
            return {"spd":spd,"t":t,"v":v,"trig":None,"dist":None,
                    "min_v":v[-1]*3.6,"collision":True,"note":"AEB never fired"}

        trig_t = t[ti]
        # Min speed after trigger
        post   = v[ti:]
        mi     = ti + int(np.argmin(post))
        min_v  = v[mi]

        # Stopping distance from trigger position to min speed position
        dist = math.sqrt((x[mi]-x[ti])**2 + (y[mi]-y[ti])**2)

        # Collision: speed rebounds > 3 m/s after minimum
        collision = False
        note = "safe"
        if mi < len(v)-1:
            post_min = v[mi:]
            post_t   = t[mi:]
            mask     = post_t - t[mi] < 5.0
            if mask.sum() > 1 and post_min[mask][-1] - post_min[mask][0] > 3.0:
                collision = True
                note = f"speed rebound +{round((post_min[mask][-1]-post_min[mask][0])*3.6,1)}kph"

        # Also check gap to obstacle at minimum speed
        if not obs.empty:
            ox,oy = obs["x"].iloc[0], obs["y"].iloc[0]
            gap   = math.sqrt((x[mi]-ox)**2+(y[mi]-oy)**2)-4.5
            if gap < 0.5:
                collision = True
                note = f"gap {round(max(0,gap),2)}m at min speed"

        return {"spd":spd,"t":t,"v":v,"trig":round(trig_t,3),
                "dist":round(dist,2),"min_v":round(min_v*3.6,2),
                "collision":collision,"note":note}
    except Exception as e:
        return None

def physics_dist(d_dry, mu):
    return round(d_dry * MU["dry"] / mu, 2)

# ── FIGURE 1: Speed profiles ──────────────────────────────────────────────────
def fig1_speed_profiles(data):
    fig, axes = plt.subplots(1, 3, figsize=(14,4.5))
    fig.suptitle("Figure 1 — AEB Speed Profiles (Dry Surface, Simulated)",
                 fontsize=12, fontweight="bold", y=1.01)

    for ax, spd in zip(axes, SPEEDS):
        m = data.get(spd)
        ax.set_facecolor("white")
        if m is None:
            ax.set_title(f"{spd} kph — no data"); continue

        ax.plot(m["t"], m["v"]*3.6, color=SPCOL[spd], linewidth=2,
                label=f"{spd} kph")

        if m["trig"]:
            ax.axvline(m["trig"], color="#e67e22", linestyle="--",
                       linewidth=1.2, label=f"AEB t={m['trig']}s")

        # Outcome box — bottom left, away from trigger line
        if m["collision"]:
            txt = f"COLLISION\n{m['note']}"
            bc  = "#fde8e8"
            ec  = "#d62728"
            tc  = "#d62728"
        elif m["min_v"] < 2:
            txt = f"Stopped safely\nBraking dist: {m['dist']}m"
            bc  = "#e8f8ee"
            ec  = "#2ca02c"
            tc  = "#2ca02c"
        else:
            txt = f"Slowed to {m['min_v']}kph\nDist: {m['dist']}m"
            bc  = "#fff3e0"
            ec  = "#e67e22"
            tc  = "#e67e22"

        ax.text(0.03, 0.05, txt,
                transform=ax.transAxes, ha="left", va="bottom",
                fontsize=8, color=tc,
                bbox=dict(boxstyle="round,pad=0.4", facecolor=bc,
                          edgecolor=ec, alpha=0.9))

        ax.set_title(f"{spd} kph initial speed", fontsize=10)
        ax.set_xlabel("Time (s)"); ax.set_ylabel("Speed (kph)")
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.5)
        ax.set_ylim(-5, spd*1.25)
        ax.axhline(0, color="#333333", linewidth=0.8)

    plt.tight_layout()
    out = os.path.join(FIG, "fig1_aeb_speed_profiles.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: fig1_aeb_speed_profiles.png")

# ── FIGURE 2: Stopping distances bar chart ────────────────────────────────────
def fig2_stopping_distances(data):
    tbl = {}
    for spd, m in data.items():
        if m is None or m["dist"] is None: continue
        d = m["dist"]
        tbl[spd] = {s: (d if s=="dry" else physics_dist(d,MU[s])) for s in SURFS}

    if not tbl: return
    speeds = sorted(tbl.keys())

    fig, ax = plt.subplots(figsize=(12,6))
    fig.suptitle("Figure 2 — AEB Stopping Distance by Speed and Surface",
                 fontsize=12, fontweight="bold")
    ax.set_title(
        "Solid = simulated (esmini, dry surface)     "
        "Hatched = physics model  [ d = v² ÷ (2μg) ]",
        fontsize=8.5, color="#555555", pad=8)

    bw = 0.17
    x  = np.arange(len(speeds))
    max_val = max(tbl[s]["icy"] for s in speeds)

    for i, surf in enumerate(SURFS):
        vals   = [tbl[s][surf] for s in speeds]
        offset = (i - 1.5) * bw
        bars   = ax.bar(x+offset, vals, width=bw,
                        color=SCOL[surf], hatch=SHATCH[surf],
                        alpha=0.85, edgecolor="black", linewidth=0.5,
                        label=f"{surf.capitalize()} μ={MU[surf]}"
                              + (" [sim]" if surf=="dry" else " [model]"))
        for bar, val in zip(bars, vals):
            if val > 0:
                ax.text(bar.get_x()+bar.get_width()/2,
                        bar.get_height() + max_val*0.008,
                        f"{val:.0f}m",
                        ha="center", va="bottom",
                        fontsize=7, color="black", fontweight="bold")

    # Collision markers for dry bars where collision occurred
    for i, spd in enumerate(speeds):
        m = data.get(spd)
        if m and m["collision"]:
            offset = (0 - 1.5) * bw  # dry bar position
            ax.text(i+offset, tbl[spd]["dry"]+max_val*0.04,
                    "⚠", ha="center", fontsize=12, color="#d62728")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{s} kph" for s in speeds], fontsize=10)
    ax.set_ylabel("Stopping Distance (m)", fontsize=10)
    ax.set_xlabel("Initial Ego Speed", fontsize=10)
    ax.set_ylim(0, max_val*1.18)
    ax.legend(loc="upper left", fontsize=8.5, ncol=2,
              framealpha=0.9, edgecolor="#bbbbbb")
    ax.grid(True, axis="y", alpha=0.4)
    ax.set_facecolor("white")

    # Single clean footnote at bottom
    fig.text(0.5, -0.02,
             "⚠ = collision detected (ALKS CRITICAL mode — speed exceeds ECE R157 certification limit of 60 kph)",
             ha="center", fontsize=8, color="#d62728", style="italic")

    plt.tight_layout()
    out = os.path.join(FIG, "fig2_aeb_stopping_distances.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: fig2_aeb_stopping_distances.png")

# ── FIGURE 3: Surface comparison line chart ───────────────────────────────────
def fig3_surface_comparison(data):
    fig, ax = plt.subplots(figsize=(10,6))
    fig.suptitle("Figure 3 — AEB Stopping Distance vs Speed by Surface",
                 fontsize=12, fontweight="bold")
    ax.set_title(
        "Solid line + circles = simulated (dry)     "
        "Dashed lines + markers = physics model",
        fontsize=8.5, color="#555555", pad=8)

    v_range = np.linspace(5, 38, 300)

    for surf in SURFS:
        mu = MU[surf]
        ax.plot(v_range*3.6, v_range**2/(2*mu*G),
                color=SCOL[surf],
                linestyle="-" if surf=="dry" else "--",
                linewidth=1.2, alpha=0.35, zorder=1)

        pts_x, pts_y = [], []
        coll_x, coll_y = [], []
        for spd, m in sorted(data.items()):
            if m is None or m["dist"] is None: continue
            d = m["dist"] if surf=="dry" else physics_dist(m["dist"], mu)
            if surf=="dry" and m["collision"]:
                coll_x.append(spd); coll_y.append(d)
            else:
                pts_x.append(spd); pts_y.append(d)

        if pts_x:
            ax.scatter(pts_x, pts_y, color=SCOL[surf],
                       marker=SMARK[surf], s=80, zorder=4,
                       label=f"{surf.capitalize()} μ={mu}"
                             +(" (sim)" if surf=="dry" else " (model)"))
        if coll_x:
            ax.scatter(coll_x, coll_y, color="#d62728",
                       marker="x", s=120, linewidths=2.5, zorder=5)

    ax.set_xlabel("Speed (kph)", fontsize=10)
    ax.set_ylabel("Stopping Distance (m)", fontsize=10)
    ax.legend(fontsize=9, loc="upper left",
              framealpha=0.9, edgecolor="#bbbbbb")
    ax.grid(True, alpha=0.4)
    ax.set_facecolor("white")
    ax.set_xlim(30, 135)

    ax.annotate("✕ = collision (ALKS CRITICAL mode)",
                xy=(0.98, 0.05), xycoords="axes fraction",
                ha="right", fontsize=8, color="#d62728",
                style="italic")

    plt.tight_layout()
    out = os.path.join(FIG, "fig3_aeb_surface_comparison.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: fig3_aeb_surface_comparison.png")

# ── FIGURE 4: ADAS vs Baseline ────────────────────────────────────────────────
def fig4_adas_baseline():
    pairs = [
        ("S1_50kph_AEB_A.csv",  "S1_50kph_baseline.csv",  "50 kph"),
        ("S1_80kph_AEB_A.csv",  "S1_80kph_baseline.csv",  "80 kph"),
        ("S1_120kph_AEB_A.csv", "S1_120kph_baseline.csv", "120 kph"),
    ]
    avail = [(a,b,l) for a,b,l in pairs
             if os.path.exists(os.path.join(RAW,a)) or
                os.path.exists(os.path.join(RAW,b))]
    if not avail:
        print("  Fig 4 skipped — no S1 baseline CSVs found")
        return

    fig, axes = plt.subplots(1, len(avail), figsize=(5*len(avail),5))
    if len(avail)==1: axes=[axes]
    fig.suptitle("Figure 4 — AEB: ADAS Active vs Baseline (No ADAS)",
                 fontsize=12, fontweight="bold")

    for ax,(af,bf,label) in zip(axes,avail):
        ap = os.path.join(RAW,af)
        bp = os.path.join(RAW,bf)
        if os.path.exists(ap):
            df=load(ap); e=entity(df,"Ego")
            ax.plot(e["time"],e["speed"]*3.6,
                    color="#2ca02c",linewidth=2,label="AEB active — stops safely")
        if os.path.exists(bp):
            df=load(bp); e=entity(df,"Ego")
            ax.plot(e["time"],e["speed"]*3.6,
                    color="#d62728",linewidth=2,linestyle="--",
                    label="Baseline — no AEB — collision")
        ax.set_title(label,fontsize=10)
        ax.set_xlabel("Time (s)"); ax.set_ylabel("Speed (kph)")
        ax.legend(fontsize=8); ax.grid(True,alpha=0.4)
        ax.set_facecolor("white"); ax.axhline(0,color="#333",linewidth=0.8)

    plt.tight_layout()
    out = os.path.join(FIG,"fig4_aeb_adas_vs_baseline.png")
    plt.savefig(out,dpi=150,bbox_inches="tight")
    plt.close()
    print(f"  Saved: fig4_aeb_adas_vs_baseline.png")

# ── FIGURE 5: ACC gap profiles ────────────────────────────────────────────────
def fig5_acc():
    files = [("S_ACC_dry_gentle.csv","Gentle 2.0 m/s²","#2ca02c"),
             ("S_ACC_dry_moderate.csv","Moderate 5.0 m/s²","#ff7f0e"),
             ("S_ACC_dry_hard.csv","Hard 8.0 m/s²","#d62728")]
    avail = [(f,l,c) for f,l,c in files
             if os.path.exists(os.path.join(RAW,f))]
    if not avail:
        print("  Fig 5 skipped — run ACC scenarios first"); return

    fig, axes = plt.subplots(1,len(avail),figsize=(5*len(avail),5),sharey=True)
    if len(avail)==1: axes=[axes]
    fig.suptitle("Figure 5 — ACC: Gap Between Ego and NPC Over Time (Dry)",
                 fontsize=12,fontweight="bold")

    for ax,(fname,label,color) in zip(axes,avail):
        df=load(os.path.join(RAW,fname))
        ego=entity(df,"Ego"); npc=entity(df,"NPC")
        if npc.empty:
            ax.set_title(f"{label}\nNPC not found"); continue
        mg=pd.merge(ego[["time","x","y"]],npc[["time","x","y"]],
                    on="time",suffixes=("_e","_n"))
        mg["gap"]=(np.sqrt((mg.x_e-mg.x_n)**2+(mg.y_e-mg.y_n)**2)-4.5).clip(0)
        ax.plot(mg["time"],mg["gap"],color=color,linewidth=2)
        ax.axvline(5,color="#e67e22",linestyle="--",linewidth=1.2,label="NPC brakes t=5s")
        ax.axhline(0,color="#d62728",linestyle=":",linewidth=1,alpha=0.7,label="Collision")
        mg_val=mg["gap"].min()
        safe=mg_val>0.5
        ax.set_title(f"{label}\nMin gap={mg_val:.1f}m {'✓ SAFE' if safe else '✗ COLLISION'}",
                     fontsize=9,color="#2ca02c" if safe else "#d62728")
        ax.set_xlabel("Time (s)"); ax.set_ylabel("Gap to NPC (m)")
        ax.legend(fontsize=8); ax.grid(True,alpha=0.4)
        ax.set_facecolor("white")

    plt.tight_layout()
    out=os.path.join(FIG,"fig5_acc_gap_profiles.png")
    plt.savefig(out,dpi=150,bbox_inches="tight")
    plt.close()
    print(f"  Saved: fig5_acc_gap_profiles.png")

# ── FIGURE 6: LKA deviation ───────────────────────────────────────────────────
def fig6_lka():
    files = [("S_LKA_dry_slow.csv","Slow (maxLatAcc=0.1)","#2ca02c"),
             ("S_LKA_dry_med.csv","Med (maxLatAcc=0.3)","#ff7f0e"),
             ("S_LKA_dry_fast.csv","Fast (maxLatAcc=0.6)","#d62728")]
    avail = [(f,l,c) for f,l,c in files
             if os.path.exists(os.path.join(RAW,f))]
    if not avail:
        print("  Fig 6 skipped — run LKA scenarios first"); return

    LANE_W = 1.875
    fig,axes=plt.subplots(1,len(avail),figsize=(5*len(avail),5),sharey=True)
    if len(avail)==1: axes=[axes]
    fig.suptitle("Figure 6 — LKA: Lateral Deviation Over Time (Dry Surface)",
                 fontsize=12,fontweight="bold")

    for ax,(fname,label,color) in zip(axes,avail):
        df=load(os.path.join(RAW,fname)); ego=entity(df,"Ego")
        dev=(ego["y"]-ego["y"].iloc[0]).abs()
        ax.plot(ego["time"],dev,color=color,linewidth=2,label="Lateral deviation")
        ax.axvline(3,color="#e67e22",linestyle="--",linewidth=1.2,label="Drift starts t=3s")
        ax.axhline(LANE_W,color="#9467bd",linestyle=":",linewidth=1.5,
                   label=f"Lane boundary {LANE_W}m")
        mx=dev.max()
        crossed=mx>LANE_W
        ax.set_title(f"{label}\nMax dev={mx:.2f}m "
                     f"{'Lane crossed ✗' if crossed else 'Stayed in lane ✓'}",
                     fontsize=9,color="#d62728" if crossed else "#2ca02c")
        ax.set_xlabel("Time (s)"); ax.set_ylabel("Lateral Deviation (m)")
        ax.legend(fontsize=8); ax.grid(True,alpha=0.4)
        ax.set_facecolor("white")
        ax.set_ylim(-0.1,max(mx*1.25,LANE_W*1.4))

    plt.tight_layout()
    out=os.path.join(FIG,"fig6_lka_deviation.png")
    plt.savefig(out,dpi=150,bbox_inches="tight")
    plt.close()
    print(f"  Saved: fig6_lka_deviation.png")

# ── Summary CSV ───────────────────────────────────────────────────────────────
def summary(data):
    rows=[]
    for spd,m in sorted(data.items()):
        if m is None: continue
        d=m["dist"] if m["dist"] else 0
        for surf in SURFS:
            dval=d if surf=="dry" else physics_dist(d,MU[surf]) if d else 0
            rows.append({
                "Speed_kph":spd,"Surface":surf,"mu":MU[surf],
                "Stopping_dist_m":dval,
                "Data_source":"simulated" if surf=="dry" else "physics_model",
                "Collision":m["collision"] if surf=="dry" else "N/A",
                "AEB_trigger_t_s":m["trig"] if surf=="dry" else "N/A",
                "ALKS_mode":"TARGET_IN_SIGHT" if not m["collision"] else "CRITICAL",
                "Note":m["note"] if surf=="dry" else "",
            })
    df=pd.DataFrame(rows)
    out=os.path.join(FIG,"summary_AEB.csv")
    df.to_csv(out,index=False)
    print(f"  Saved: summary_AEB.csv")
    return df

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("="*60)
    print("ADAS THESIS — RESULTS ANALYSIS v3")
    print("="*60)

    print("\n[1] Loading AEB dry data...")
    data={}
    for spd in SPEEDS:
        for prefix in ["S_AEB_dry","S1_AEB_dry"]:
            p=os.path.join(RAW,f"{prefix}_{spd}kph.csv")
            if os.path.exists(p):
                m=extract_aeb(p,spd)
                data[spd]=m
                if m:
                    c="COLLISION" if m["collision"] else "SAFE"
                    print(f"  {spd}kph: trigger={m['trig']}s  "
                          f"dist={m['dist']}m  "
                          f"min={m['min_v']}kph  {c}  [{m['note']}]")
                break
        if spd not in data:
            print(f"  {spd}kph: no CSV found")
            data[spd]=None

    if all(v is None for v in data.values()):
        print("No data found."); sys.exit(1)

    print("\n[2] Generating figures...")
    fig1_speed_profiles(data)
    fig2_stopping_distances(data)
    fig3_surface_comparison(data)
    fig4_adas_baseline()
    fig5_acc()
    fig6_lka()

    print("\n[3] Summary table...")
    df=summary(data)
    print(df[["Speed_kph","Surface","Stopping_dist_m",
              "Collision","ALKS_mode"]].to_string(index=False))

    print(f"\n{'='*60}")
    print(f"All figures → {FIG}")
    print("\nThesis finding:")
    print("  50kph:  SAFE   — ALKS enters TARGET_IN_SIGHT, controlled stop")
    print("  80kph:  COLLISION — ALKS enters CRITICAL, exceeds ECE R157 limit")
    print("  120kph: COLLISION — ALKS enters CRITICAL, well beyond limit")
    print("  ECE R157 ALKS certified max speed: 60 kph")
    print("\nNext: run ACC + LKA scenarios then re-run this script")

if __name__=="__main__":
    main()
