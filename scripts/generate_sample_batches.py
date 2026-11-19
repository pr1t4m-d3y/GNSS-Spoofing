import pandas as pd
import numpy as np
import os

np.random.seed(42)

def generate_gnss_data(filename, num_rows, attack_type=None):
    """
    Generates a GNSS telemetry CSV following the exact project schema.
    All 15 columns: time, PRN, Carrier_Doppler_hz, Pseudorange_m, CN0,
    Carrier_phase, TOW, RX_time, EC, LC, PC, PIP, PQP, TCD, channel
    """
    
    # Training data medians (from train.xls analysis)
    base_doppler = 2761.0
    base_pseudo = 505867.0
    base_cn0 = 46.0
    base_phase = -109573.0
    base_tow = 491655
    
    data = []
    
    for i in range(num_rows):
        doppler = base_doppler + np.random.normal(0, 50)
        pseudo = base_pseudo + np.random.normal(0, 100)
        cn0 = base_cn0 + np.random.normal(0, 1)
        
        if attack_type == "sudden_drift" and i > num_rows // 2:
            doppler += 8000
            pseudo += 2000000
            cn0 -= 15
            
        elif attack_type == "slow_creeper" and i > num_rows // 3:
            drift_factor = (i - num_rows // 3) * 50
            doppler += drift_factor
            pseudo += drift_factor * 100
            cn0 -= (i - num_rows // 3) * 0.1
            
        elif attack_type == "mixed":
            if (i // 50) % 2 == 1:
                doppler += 12000
                pseudo += 5000000
                cn0 = 25

        row = {
            "time": i,
            "PRN": np.random.choice([1, 3, 8, 12, 14, 21, 24, 28, 31]),
            "Carrier_Doppler_hz": round(doppler, 2),
            "Pseudorange_m": round(pseudo, 2),
            "CN0": round(max(cn0, 10), 2),
            "Carrier_phase": round(base_phase + np.random.normal(0, 10), 2),
            "TOW": base_tow + i,
            "RX_time": base_tow + i,
            "EC": 119937 + np.random.randint(-100, 100),
            "LC": 119767 + np.random.randint(-100, 100),
            "PC": 133558 + np.random.randint(-100, 100),
            "PIP": -3701 + np.random.randint(-50, 50),
            "PQP": 196 + np.random.randint(-10, 10),
            "TCD": 2760 + np.random.randint(-5, 5),
            "channel": "manual_0"
        }
        data.append(row)
        
    df = pd.DataFrame(data)
    
    os.makedirs('examples', exist_ok=True)
    filepath = f'examples/{filename}'
    df.to_csv(filepath, index=False)
    print(f"✓ Generated {filepath} ({num_rows} rows)")

if __name__ == "__main__":
    # 1. Safe dataset — should result in green/healthy state  
    generate_gnss_data("safe_signals.csv", 200, attack_type=None)
    
    # 2. Unsafe dataset — sudden spoofing halfway through
    generate_gnss_data("unsafe_sudden_attack.csv", 200, attack_type="sudden_drift")
    
    # 3. Mixed — alternating normal/spoofed for stress testing
    generate_gnss_data("mixed_stress_test.csv", 500, attack_type="mixed")
    
    print("\n✅ All batch files generated in examples/")
