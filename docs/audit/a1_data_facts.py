import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "backend")
import pandas as pd, numpy as np
from utils import clean_gnss, engineer_features, ALL_MODEL_FEATURES, BASE_FEATURES, ENG_FEATURES, ROLLING_FEATURES
raw = pd.read_excel("train.xls", engine="xlrd", header=0, dtype=str)
print("raw shape", raw.shape, "cols", list(raw.columns))
print("chX placeholder rows:", raw["Carrier_Doppler_hz"].astype(str).str.startswith("ch").sum())
c = clean_gnss(raw)   # the BACKEND's clean_gnss (not the notebook's)
print("backend clean shape", c.shape, "| NaN PRN rows:", c["PRN"].isna().sum())
print("spoofed value counts", c["spoofed"].value_counts(dropna=False).to_dict())
print("channels", sorted(c["channel"].dropna().unique()), "n =", c["channel"].nunique())
print("unique PRNs", sorted(c["PRN"].dropna().unique().astype(int)))
print("time range", c["time"].min(), c["time"].max(), "unique epochs", c["time"].nunique())
print("features: base", len(BASE_FEATURES), "eng", len(ENG_FEATURES), "roll", len(ROLLING_FEATURES), "total", len(ALL_MODEL_FEATURES), "unique", len(set(ALL_MODEL_FEATURES)))
print("raw input columns the model needs:", [x for x in ["time","channel","PRN","Carrier_Doppler_hz","Pseudorange_m","RX_time","TOW","Carrier_phase","EC","LC","PC","PIP","PQP","TCD","CN0"]])
# rows per channel
print(c.groupby("channel").size().to_dict())
# are the first rows time-sorted / chronological blocks per channel?
print("per-channel time monotonic:", {k: bool(g["time"].is_monotonic_increasing) for k,g in c.groupby("channel")})
