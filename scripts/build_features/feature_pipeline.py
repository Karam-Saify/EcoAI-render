import os
import pandas as pd
import numpy as np
from pathlib import Path
import logging

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.ml.features.text_composer import TextComposer
from app.ml.embeddings.vector_store import SemanticVectorStore
from scripts.normalize.taxonomy import build_entity_canonical

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
BASE_DIR = Path(__file__).resolve().parent.parent.parent
INTERIM_DIR = BASE_DIR / "data" / "interim"
FEATURE_DIR = BASE_DIR / "data" / "feature_store"
VECTOR_DIR = BASE_DIR / "data" / "vectors"

def run_pipeline():
    os.makedirs(FEATURE_DIR, exist_ok=True)
    os.makedirs(VECTOR_DIR, exist_ok=True)

    composer = TextComposer()
    logging.info("Initializing vector store...")
    vector_store = SemanticVectorStore('all-MiniLM-L6-v2')
    
    entities = ['projects', 'investors', 'volunteers', 'grants', 'activities']
    
    for entity in entities:
        path = INTERIM_DIR / f"{entity}_interim.parquet"
        if not path.exists():
            logging.warning(f"Skipping {entity}, interim path does not exist.")
            continue
            
        logging.info(f"Processing text & embeddings for {entity}...")
        try:
            df = pd.read_parquet(path)
            df = build_entity_canonical(entity, df)
            # Compose rich text fields
            df_rich = composer.build_embeddings_corpus(df, 'project' if entity == 'projects' else entity.rstrip('s'))
            
            # Generate dense vectors
            texts = df_rich['text_full'].tolist()
            embeddings = vector_store.generate_embeddings(texts)
            
            # Save final structure and local index
            df_rich.to_parquet(FEATURE_DIR / f"{entity}_features.parquet", index=False)
            if embeddings.size > 0:
                np.save(VECTOR_DIR / f"{entity}_vectors.npy", embeddings)
                logging.info(f"Generated {len(embeddings)} vectors for {entity}.")
            
        except Exception as e:
            logging.error(f"Failed to process {entity}: {e}")

if __name__ == "__main__":
    run_pipeline()
