import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "backend")
import pandas as pd, numpy as np, joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from utils import clean_gnss, engineer_features, ALL_MODEL_FEATURES, ROLLING_TARGETS

raw = pd.read_excel("train.xls", engine="xlrd", header=0, dtype=str)
raw = raw[~raw["Carrier_Doppler_hz"].astype(str).str.startswith("ch")]
df = clean_gnss(raw).reset_index(drop=True)
print("clean genuine rows:", len(df))

def rep(name, y, p):
    tn, fp, fn, tp = confusion_matrix(y, p, labels=[0,1]).ravel()
    print(f"{name}: P={precision_score(y,p):.4f} R={recall_score(y,p):.4f} F1={f1_score(y,p):.4f} | TP={tp} FP={fp} FN={fn} TN={tn} | n={len(y)}")

def inject(frame, idx, rng):
    for i in idx:
        frame.at[i,"Carrier_Doppler_hz"] += rng.uniform(350,600)
        frame.at[i,"Pseudorange_m"]      += rng.uniform(800,1200)
        frame.at[i,"CN0"]                += rng.uniform(2,5)

# ---------- A: notebook protocol, shipped model (trained on ALL of df => rows are in-sample) ----------
model = joblib.load("GNSS_AntiSpoofing_Project_Bundle/gnss_anti_spoofing_model.pkl")
for seed in (0,1,2):
    rng = np.random.default_rng(seed)
    val = df.sample(2000, random_state=42).reset_index(drop=True)
    inj = rng.choice(val.index, 200, replace=False)
    val["y"] = 0; val.loc[inj,"y"] = 1
    inject(val, inj, rng)
    f = engineer_features(val.drop(columns=["spoofed"]))   # sorts by channel,time
    X = f[ALL_MODEL_FEATURES].fillna(0)
    p = (model.predict(X) == -1).astype(int)
    rep(f"A notebook-protocol, shipped model, seed {seed}", f["y"].values, p)
    if seed == 0:
        print("   flagged rate:", p.mean().round(4), "| genuine-row flag rate (FPR):", p[f['y'].values==0].mean().round(4))

# ---------- B: honest temporal split: first 70% of each channel's timeline = train, last 30% = held-out ----------
df = df.sort_values(["channel","time"]).reset_index(drop=True)
df["rank"] = df.groupby("channel").cumcount() / df.groupby("channel")["time"].transform("size")
train, test = df[df["rank"]<0.7].copy(), df[df["rank"]>=0.7].copy().reset_index(drop=True)
print(f"B split: train {len(train)} | held-out {len(test)} (time-ordered per channel)")
ftr = engineer_features(train.drop(columns=["spoofed","rank"]))
pipe = Pipeline([("scaler",StandardScaler()),("model",IsolationForest(n_estimators=200,contamination=0.01,random_state=42,n_jobs=-1))])
pipe.fit(ftr[ALL_MODEL_FEATURES].replace([np.inf,-np.inf],np.nan).fillna(0))
for seed in (0,1,2):
    rng = np.random.default_rng(seed)
    t = test.copy()
    inj = rng.choice(t.index, int(0.10*len(t)), replace=False)
    t["y"] = 0; t.loc[inj,"y"] = 1
    inject(t, inj, rng)
    f = engineer_features(t.drop(columns=["spoofed","rank"]))
    X = f[ALL_MODEL_FEATURES].replace([np.inf,-np.inf],np.nan).fillna(0)
    p = (pipe.predict(X)==-1).astype(int)
    rep(f"B held-out, 10% injected, seed {seed}", f["y"].values, p)
# B2: no attacks at all -> false-positive rate on pure genuine held-out
f = engineer_features(test.drop(columns=["spoofed","rank"]))
X = f[ALL_MODEL_FEATURES].replace([np.inf,-np.inf],np.nan).fillna(0)
print("B2 pure-genuine held-out flag rate (FPR):", (pipe.predict(X)==-1).mean().round(4))
# B3: shipped model on same held-out genuine => in-sample vs not
print("B3 shipped model flag rate on same rows:", (model.predict(X)==-1).mean().round(4))
