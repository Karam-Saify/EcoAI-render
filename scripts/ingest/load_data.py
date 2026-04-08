import pandas as pd
import json
import os
import argparse
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
INTERIM_DIR = BASE_DIR / "data" / "interim"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

def load_json_to_df(filename: str) -> pd.DataFrame:
    filepath = RAW_DIR / filename
    if not filepath.exists():
        print(f"File {filepath} not found.")
        return pd.DataFrame()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Try to infer if it's a wrapper object (like some graph responses)
            if 'data' in data:
                df = pd.DataFrame(data['data'])
            else:
                df = pd.DataFrame([data])
        else:
            df = pd.DataFrame()
            print(f"Unknown JSON structure in {filename}")
        
        return df

def profile_df(df: pd.DataFrame, name: str):
    print(f"\n--- Profiling {name} ---")
    print(f"Total Rows: {len(df)}")
    if df.empty: return
    print(f"Total Columns: {len(df.columns)}")
    print("Null rates:")
    nulls = df.isnull().mean()
    print(nulls[nulls > 0].to_string() if not nulls[nulls > 0].empty else "No missing data.")
    print("-------------------------\n")

def ingest_all():
    files = {
        "projects": "projects.json",
        "investors": "investors.json",
        "volunteers": "volunteers.json",
        "grants": "grants_sustainability_enriched.json",
        "activities": "iati_ecowise_activities_fast.json"
    }

    raw_dfs = {}
    for key, filename in files.items():
        print(f"Loading {filename}...")
        df = load_json_to_df(filename)
        profile_df(df, key)
        raw_dfs[key] = df
        
        # Save to interim as parquet for faster retrieval downstream
        if not df.empty:
            out_path = INTERIM_DIR / f"{key}_interim.parquet"
            # Some columns might be dicts/lists, cast them to string for initial dumping 
            # or handle them. In interim, we accept raw format, but JSON/Parquet has strict types.
            # Using JSON dump to string for mixed type columns:
            df_safe = df.copy()
            for col in df_safe.columns:
                if df_safe[col].apply(lambda x: isinstance(x, (list, dict))).any():
                    df_safe[col] = df_safe[col].apply(json.dumps)
            df_safe.to_parquet(out_path, index=False)
            print(f"Saved {key} to interim parquet.")

if __name__ == "__main__":
    os.makedirs(INTERIM_DIR, exist_ok=True)
    ingest_all()
