import sys, warnings, time, os, resource; warnings.filterwarnings("ignore")
sys.path.insert(0, "backend")
import pandas as pd, numpy as np, joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from utils import clean_gnss, engineer_features, ALL_MODEL_FEATURES

raw = pd.read_excel("train.xls", engine="xlrd", header=0, dtype=str)
raw = raw[~raw["Carrier_Doppler_hz"].astype(str).str.startswith("ch")]
df = clean_gnss(raw).reset_index(drop=True).sort_values(["channel","time"]).reset_index(drop=True)
df["rank"] = df.groupby("channel").cumcount()/df.groupby("channel")["time"].transform("size")
train, test = df[df["rank"]<0.7], df[df["rank"]>=0.7].reset_index(drop=True)
clean = lambda f: f[ALL_MODEL_FEATURES].replace([np.inf,-np.inf],np.nan).fillna(0)
ftr = engineer_features(train.drop(columns=["spoofed","rank"]))
pipe = Pipeline([("s",StandardScaler()),("model",IsolationForest(n_estimators=200,contamination=0.01,random_state=42,n_jobs=-1))]).fit(clean(ftr))

def rep(name,y,p):
    tn,fp,fn,tp = confusion_matrix(y,p,labels=[0,1]).ravel()
    print(f"{name}: P={precision_score(y,p,zero_division=0):.4f} R={recall_score(y,p):.4f} F1={f1_score(y,p):.4f} | TP={tp} FP={fp} FN={fn} TN={tn} n={len(y)}")

# B4: sustained attacks - 5 contiguous 100-row blocks per run (same notebook perturbation per row)
for seed in (0,1,2):
    rng = np.random.default_rng(seed); t = test.copy(); t["y"]=0
    starts = rng.choice(np.arange(0,len(t)-100,100), 5, replace=False)
    for s in starts:
        ix = range(s, s+100)
        for i in ix:
            t.at[i,"Carrier_Doppler_hz"] += rng.uniform(350,600); t.at[i,"Pseudorange_m"] += rng.uniform(800,1200); t.at[i,"CN0"] += rng.uniform(2,5); t.at[i,"y"]=1
    f = engineer_features(t.drop(columns=["spoofed","rank"]))
    rep(f"B4 sustained (5x100 rows) seed {seed}", f["y"].values, (pipe.predict(clean(f))==-1).astype(int))

# magnitude context: how big is the injected shift vs natural spread of the genuine data
g = df
print("natural std: Doppler %.0f Hz | Pseudorange %.0f m | CN0 %.2f dB-Hz  vs injected +350..600 Hz, +800..1200 m, +2..5 dB" % (g.Carrier_Doppler_hz.std(), g.Pseudorange_m.std(), g.CN0.std()))

# ---------- G5 measurements on shipped model ----------
p = "GNSS_AntiSpoofing_Project_Bundle/gnss_anti_spoofing_model.pkl"
print("model file size bytes:", os.path.getsize(p))
model = joblib.load(p)
fall = engineer_features(df.drop(columns=["spoofed","rank"]))
X = clean(fall)
model.set_params(model__n_jobs=1)
for n in (1, 100, 1000, 10000):
    xs = X.iloc[:n]; ts=[]
    for _ in range(20 if n<=1000 else 5):
        t0=time.perf_counter(); model.decision_function(xs); ts.append((time.perf_counter()-t0)*1000)
    print(f"model-only latency batch={n:>5}: p50={np.percentile(ts,50):.2f} ms p95={np.percentile(ts,95):.2f} ms -> {n/np.percentile(ts,50)*1000:,.0f} rows/s")
print("peak RSS of this process (MB, includes pandas/xlrd load of train.xls): %.0f" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e6))
