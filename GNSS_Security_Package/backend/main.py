from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
import json
import os
import io
from pydantic import BaseModel
from typing import List, Dict, Any

from utils import clean_gnss, engineer_features, ALL_MODEL_FEATURES

app = FastAPI(title="GNSS Security Shield API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the model
MODEL_PATH = os.path.join(os.path.dirname(__file__), '../GNSS_AntiSpoofing_Project_Bundle/gnss_anti_spoofing_model.pkl')
try:
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully.")
    expected_features = getattr(model, "feature_names_in_", None)
    if expected_features is not None:
        print("Expected features:", list(expected_features))
except Exception as e:
    print(f"Error loading model: {e}")
    model = None
    expected_features = None

class SignalData(BaseModel):
    data: List[Dict[str, Any]]

@app.post("/predict")
async def predict(payload: SignalData):
    if model is None:
        raise HTTPException(status_code=500, detail="Model failed to load.")
    
    try:
        df = pd.DataFrame(payload.data)
        
        # Preprocess
        df_clean = clean_gnss(df)
        if len(df_clean) == 0:
            return {"predictions": [], "features": []}

        df_feats = engineer_features(df_clean)
        
        # Feed only the 35 model features to the Isolation Forest
        X = df_feats[ALL_MODEL_FEATURES]
            
        preds = model.predict(X)
        scores = model.decision_function(X) 
        
        normalized_scores = []
        for s in scores:
            ns = 1.0 - ((s + 0.2) / 0.4) 
            ns = max(0.0, min(1.0, ns))
            normalized_scores.append(ns)
            
        results = []
        for i, (pred, score, ns) in enumerate(zip(preds, scores, normalized_scores)):
            is_spoofed = pred == -1
            results.append({
                "index": i,
                "is_spoofed": bool(is_spoofed),
                "anomaly_score": float(ns),
                "raw_decision_score": float(score)
            })
            
        # Attach metadata to features for the frontend
        df_feats['is_spoofed'] = [bool(p == -1) for p in preds]
        df_feats['anomaly_score'] = normalized_scores
        df_feats = df_feats.fillna(0)
            
        return {"predictions": results, "features": df_feats.to_dict(orient="records")}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/predict/file")
async def predict_file(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(status_code=500, detail="Model failed to load.")
    
    contents = await file.read()
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        elif file.filename.endswith('.json'):
            df = pd.read_json(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
            
        df_clean = clean_gnss(df)
        
        if len(df_clean) == 0:
             return {"summary": {"total_samples": 0}, "timeline": []}

        df_feats = engineer_features(df_clean)
        
        # Feed only the 35 model features to the Isolation Forest
        X = df_feats[ALL_MODEL_FEATURES]
            
        preds = model.predict(X)
        scores = model.decision_function(X)
        
        normalized_scores = []
        for s in scores:
            ns = 1.0 - ((s + 0.2) / 0.4)
            ns = max(0.0, min(1.0, ns))
            normalized_scores.append(ns)
            
        df_feats['is_spoofed'] = [bool(p == -1) for p in preds]
        df_feats['anomaly_score'] = normalized_scores
        df_feats = df_feats.fillna(0)
        
        # Build timeline safely — only select columns that exist
        timeline_cols = ['Carrier_Doppler_hz', 'range_residual', 'anomaly_score', 'is_spoofed']
        if 'time' in df_feats.columns:
            timeline_cols.append('time')
        if 'PRN' in df_feats.columns:
            timeline_cols.append('PRN')
        
        return {
            "summary": {
                "total_samples": len(preds),
                "spoofed_samples": int(sum(preds == -1)),
                "average_anomaly_score": float(sum(normalized_scores)/len(normalized_scores))
            },
            "timeline": df_feats[timeline_cols].head(200).to_dict(orient="records")
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/reset")
async def reset_history():
    from utils import history_manager
    history_manager.history = {}
    return {"status": "success", "message": "History cleared"}

@app.get("/scan")
async def scan_system():
    """Quick self-diagnostic endpoint for the Scan button."""
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "feature_count": len(ALL_MODEL_FEATURES),
        "message": "All subsystems operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
