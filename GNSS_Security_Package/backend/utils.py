import pandas as pd
import numpy as np
from collections import deque

SPEED_OF_LIGHT = 299_792_458.0 # m/s
L1_FREQ        = 1_575_420_000.0 # Hz  (GPS L1 carrier)
L1_WAVELENGTH  = SPEED_OF_LIGHT / L1_FREQ  # ~0.1903 m

# Exact feature order expected by the trained model (35 features)
BASE_FEATURES = [
    'Carrier_Doppler_hz', 'Pseudorange_m', 'Carrier_phase',
    'EC', 'LC', 'PC', 'PIP', 'PQP', 'TCD', 'CN0'
]
ENG_FEATURES = [
    'range_rate', 'transit_time_s', 'computed_range', 'range_residual',
    'phase_range_bias', 'cn0_pc_ratio', 'cn0_ec_ratio', 'iq_imbalance',
    'lock_ratio', 'doppler_delta', 'tcd_cn0'
]
ROLLING_TARGETS = [
    'Carrier_Doppler_hz', 'CN0', 'range_residual', 'iq_imbalance',
    'doppler_delta', 'phase_range_bias', 'lock_ratio'
]

# Generate rolling feature list
ROLLING_FEATURES = []
for target in ROLLING_TARGETS:
    ROLLING_FEATURES.extend([f"{target}_roll_mean", f"{target}_roll_var"])

ALL_MODEL_FEATURES = BASE_FEATURES + ENG_FEATURES + ROLLING_FEATURES

class HistoryManager:
    """Manages rolling window history for GNSS telemetry per channel."""
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.history = {} # channel -> {target -> deque}

    def update(self, channel, data_dict):
        if channel not in self.history:
            self.history[channel] = {target: deque(maxlen=self.window_size) for target in ROLLING_TARGETS}
        
        for target in ROLLING_TARGETS:
            if target in data_dict:
                self.history[channel][target].append(data_dict[target])

    def get_stats(self, channel, target):
        if channel not in self.history or not self.history[channel][target]:
            return 0.0, 0.0
        
        vals = list(self.history[channel][target])
        mean = np.mean(vals)
        var = np.var(vals) if len(vals) > 1 else 0.0
        return mean, var

# Singleton instances for API usage
history_manager = HistoryManager(window_size=10)

def clean_gnss(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    NUMERIC_COLS = [
        'time', 'PRN', 'Carrier_Doppler_hz', 'Pseudorange_m',
        'RX_time', 'TOW', 'Carrier_phase',
        'EC', 'LC', 'PC', 'PIP', 'PQP', 'TCD', 'CN0'
    ]
    if 'spoofed' in df.columns:
        NUMERIC_COLS.append('spoofed')

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'PRN' in df.columns:
        df = df[df['PRN'] != 0].copy()

    # Ensure channel exists
    if 'channel' not in df.columns:
        df['channel'] = 'manual_0'
        
    # CRITICAL: Ensure 'time' exists for sorting and timeline display
    if 'time' not in df.columns:
        df['time'] = df.index
        
    # Ensure other mandatory model features exist (even if blank)
    for col in NUMERIC_COLS:
        if col not in df.columns:
            df[col] = 0.0

    return df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Computes exactly 35 features for the Isolation Forest model."""
    df = df.copy()
    eps = 1e-6

    # 1. Base Engineering
    df['range_rate'] = -L1_WAVELENGTH * df['Carrier_Doppler_hz']
    
    # Handle TOW/RX_time for transit time
    if 'TOW' in df.columns and 'RX_time' in df.columns:
        df['transit_time_s'] = df['TOW'] - df['RX_time']
    else:
        df['transit_time_s'] = 0.073 # Default 73ms
        
    df['computed_range'] = df['transit_time_s'] * SPEED_OF_LIGHT
    df['range_residual'] = df['Pseudorange_m'] - df['computed_range']
    df['phase_range_bias'] = df['Pseudorange_m'] - (df['Carrier_phase'] * L1_WAVELENGTH)
    
    df['cn0_pc_ratio'] = df['CN0'] / (df['PC'].abs() + eps)
    df['cn0_ec_ratio'] = df['CN0'] / (df['EC'].abs() + eps)
    
    df['iq_imbalance'] = (df['PIP'].abs() - df['PQP'].abs()) / (df['PIP'].abs() + df['PQP'].abs() + eps)
    df['lock_ratio'] = df['LC'] / (df['EC'].abs() + eps)
    
    # Doppler Delta (requires cross-row context, but for single sample we default)
    if len(df) > 1:
        df['doppler_delta'] = df.groupby('channel')['Carrier_Doppler_hz'].diff().fillna(0)
    else:
        df['doppler_delta'] = 0.0
        
    df['tcd_cn0'] = df['TCD'] / (df['CN0'] + eps)

    # 2. Rolling Features
    # If df has many rows (batch), compute rolling stats directly
    if len(df) > 1:
        df.sort_values(['channel', 'time'], inplace=True)
        for col in ROLLING_TARGETS:
            grp = df.groupby('channel')[col]
            df[f'{col}_roll_mean'] = grp.transform(lambda x: x.rolling(10, min_periods=1).mean())
            df[f'{col}_roll_var'] = grp.transform(lambda x: x.rolling(10, min_periods=1).var().fillna(0))
    else:
        # Single sample - use HistoryManager
        row = df.iloc[0]
        channel = row.get('channel', 'manual_0')
        history_manager.update(channel, row.to_dict())
        
        for col in ROLLING_TARGETS:
            mean, var = history_manager.get_stats(channel, col)
            df[f'{col}_roll_mean'] = mean
            df[f'{col}_roll_var'] = var

    # 3. Final Feature Selection & Ordering
    # Ensure all BASE_FEATURES exist
    for col in BASE_FEATURES:
        if col not in df.columns:
            df[col] = 0.0
            
    # Return the full DataFrame so metadata (like 'time') is preserved for the API
    return df
