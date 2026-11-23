import argparse
from pathlib import Path

import numpy as np
import pandas as pd

patient = "2301"

input_dir = Path(r"C:\Users\20234676\OneDrive - TU Eindhoven\Courses Year 4\digital-twin-demo-main\Digital_Twin_Diabetes1\data\raw\T1D-UOM")
output_dir = Path(__file__).resolve().parents[1] / "data" / "processed" / "out"

DATE_FMT = "%d/%m/%Y %H:%M"            
mgdl_per_mmol = 18.0
max_glucose_interpolate = 3            # assuming that glucose changes linearly; maybe we should check the value of three, I just thought it would be a good baseline value    
max_basal_hold = pd.Timedelta("60min") # insulin pump might have fallen off or got broken. Again I just figured 60 min would be a nice baseline, but we should check literature for this
min_coverage = 0.90                    # min fraction of the day covered (glucose (missing = empty), basal (missing =value of neighbour), activity (missing = rest; 1 MET)) -> max of 2,4 hours can be missed. If the fitting quality is bad -> change this value!!

# MET -> CPM anchor points from Table 1 (rest/low/moderate/high boundaries)
MET_anchors = [1.0, 2.0, 3.0, 6.0]
CPM_anchors = [0.0, 1500.0, 2296.0, 5800.0]
PA_MET_threshold = 3.0                 # moderate intensity and up



def met_to_cpm(met):
    """Piecewise-linear MET -> CPM through the category boundaries; extrapolated above 6 MET."""
    met = np.asarray(met, dtype=float)
    cpm = np.interp(met, MET_anchors, CPM_anchors)
    slope = (CPM_anchors[-1] - CPM_anchors[-2]) / (MET_anchors[-1] - MET_anchors[-2])
    return np.where(met > MET_anchors[-1], CPM_anchors[-1] + (met - MET_anchors[-1]) * slope, cpm)


def find_file(root: Path, kind: str, pid: str) -> Path:
    hits = sorted(root.rglob(f"UoM{kind}{pid}.csv"))
    if not hits:
        raise FileNotFoundError(f"UoM{kind}{pid}.csv not found under {root}")
    print(f"{kind}: using {hits[0]}")
    if len(hits) > 1:
        print(f"   WARNING: {len(hits)} files found, ignoring: {[str(h) for h in hits[1:]]}")
    return hits[0]


def read(path: Path, ts_col: str, **kw) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", **kw)
    df["t"] = pd.to_datetime(df[ts_col], format=DATE_FMT)
    return df.sort_values("t").reset_index(drop=True)


def build_series(root: Path, pid: str):
    """Return (glucose on 5-min grid, inputs on 1-min grid)."""
    # glucose: several overlapping streams -> mean per 5-min bin
    g = read(find_file(root, "Glucose", pid), "bg_ts")
    glc = g.groupby(g.t.dt.floor("5min")).value.mean()

    # bolus: sum per minute (file has duplicate timestamps with 0.0 entries)
    bo = read(find_file(root, "Bolus", pid), "bolus_ts")
    u = bo.groupby(bo.t.dt.floor("min")).bolus_dose.sum()

    # basal: rate (U/h); step function -> hold last value
    ba = read(find_file(root, "Basal", pid), "basal_ts", usecols=[0, 1, 2])
    ba = ba.drop_duplicates("t", keep="last")[["t", "basal_dose"]]

    # meals: carbs per minute
    n = read(find_file(root, "Nutrition", pid), "meal_ts")
    meal = n.groupby(n.t.dt.floor("min")).carbs_g.sum()

    # activity: 2 rows per 15 min (e.g. WALKING + SEDENTARY) -> 1 value per slot
    a = read(find_file(root, "Activity", pid), "activity_ts")
    a["w"] = a.active_time_s.clip(lower=1)
    a["mw"] = a.met * a.w
    slot = a.groupby("t").agg(mw=("mw", "sum"), w=("w", "sum"))
    slot["met"] = slot.mw / slot.w                      # time-weighted mean MET of the 15-min slot

    start = min(glc.index.min(), ba.t.min()).floor("D")
    end = glc.index.max().ceil("D")

    g5 = pd.DataFrame(index=pd.date_range(start, end, freq="5min", inclusive="left"))
    
    s = glc.reindex(g5.index)
    filled = s.interpolate(limit_area="inside")          # vul alles tussen twee metingen
    gap_id = s.notna().cumsum()                          # nummer elke "meting + lege vakjes erachter"
    gap_len = s.isna().astype(int).groupby(gap_id).transform("sum")   # lengte van het gat
    g5["Glc"] = filled.where(~(s.isna() & (gap_len > max_glucose_interpolate)), np.nan)

    grid = pd.date_range(start, end, freq="min", inclusive="left")
    m1 = pd.DataFrame(index=grid)
    m1["u"] = u.reindex(grid)
    m1["meal"] = meal.reindex(grid)
    m1["has_meal_log"] = m1["meal"].notna()
    m1["ub"] = pd.merge_asof(pd.DataFrame({"t": grid}), ba, on="t",
                             direction="backward", tolerance=max_basal_hold).basal_dose.values
    m1["MET"] = slot.met.reindex(grid, method="ffill", limit=14)   # slot covers 15 minutes
    return g5, m1


def process(root: Path, pid: str, out: Path):
    g5, m1 = build_series(root, pid)
    bmi = pd.read_csv(sorted(root.rglob("UoMBMI.csv"))[0], encoding="utf-8-sig")
    w = bmi[bmi.participant_id.str.replace(" ", "") == f"UoM{pid}"].iloc[0].weight_kg

    (out / "data_patients").mkdir(parents=True, exist_ok=True)
    (out / "parameters").mkdir(parents=True, exist_ok=True)

    rows, m = [], 0
    for day, d in m1.groupby(m1.index.floor("D")):
        if len(d) != 1440:
            continue
        gd = g5.loc[day:day + pd.Timedelta("23h59min")]
        cov = dict(
            date=day.date(),
            glc_cov=gd.Glc.notna().mean(),
            basal_cov=d.ub.notna().mean(),
            act_cov=d.MET.notna().mean(),
            n_bolus=int((d.u.fillna(0) > 0).sum()),
            n_meals=int(d.has_meal_log.sum()),
            carbs_g=float(d.meal.fillna(0).sum()),
        )
        reasons = []
        if cov["glc_cov"] < min_coverage: reasons.append("glucose")
        if cov["basal_cov"] < min_coverage: reasons.append("basal")
        if cov["act_cov"] < min_coverage: reasons.append("activity")
        if cov["n_bolus"] == 0: reasons.append("no bolus")
        if cov["n_meals"] == 0 or cov["carbs_g"] == 0: reasons.append("no meals/carbs logged")
        cov["usable"] = not reasons
        cov["excluded_because"] = ", ".join(reasons)
        cov["G0_mgdl"] = round(gd.Glc.dropna().iloc[0] * mgdl_per_mmol, 1) if gd.Glc.notna().any() else np.nan
        cov["warning_few_meals"] = cov["usable"] and cov["n_meals"] < 3

        if cov["usable"]:
            m += 1
            data = pd.DataFrame({"time": np.arange(0, 1440, 5),
                                 "Glc": (gd.Glc * mgdl_per_mmol).round(1).values})
            met = d.MET.fillna(1.0)                      # remaining gaps (<10%) = rest
            ub = d.ub.ffill().bfill().fillna(0)
            inp = pd.DataFrame({
                "time": np.arange(1440),
                "u": (d.u.fillna(0) * 1e6).round(0).values,
                "ub": (ub * 1e6 / 60).round(3).values,
                "AC": met_to_cpm(met).round(1),
                "PA": (met >= PA_MET_threshold).astype(int).values,
                "meal": (d.meal.fillna(0) * 1000).values,
            })
            data.to_csv(out / "data_patients" / f"data_patient{pid}_day{m}.csv", index=False)
            inp.to_csv(out / "data_patients" / f"input_patient{pid}_day{m}.csv", index=False)
        cov["day_M"] = m if cov["usable"] else ""
        rows.append(cov)

    ov = pd.DataFrame(rows)
    ov.round(3).to_csv(out / f"day_overview_patient{pid}.csv", index=False)
    pd.DataFrame({"parameter": ["w", "Gb", "Ib"],
                  "value": [w, np.nan, np.nan]}      # Gb, Ib come from parameter fitting
                 ).to_csv(out / "parameters" / f"parameters_patient{pid}.csv", index=False)
    return ov


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--patient", default=patient, help="e.g. 2301")
    ap.add_argument("--input", default=input_dir, type=Path)
    ap.add_argument("--output", default=output_dir, type=Path)
    args = ap.parse_args()

    out = args.output / f"{args.patient}_processed"          # e.g. ...\processed\out\2301_processed
    ov = process(args.input, args.patient, out)
    print(f"Output saved in: {out}")
    print(f"{int(ov.usable.sum())} usable days of {len(ov)} calendar days")
    print(ov[~ov.usable].excluded_because.value_counts().to_string())
