# scripts/build_embeddings.py
import os
import pandas as pd
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.common.rag import RAG

# locate your CSV (same fallback logic as Dashboard_Cyber._load_data)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
csv_path = os.path.join(project_root, "DATA", "cyber_incidents.csv")
if not os.path.exists(csv_path):
    raise SystemExit("No DATA/cyber_incidents.csv found")

df = pd.read_csv(csv_path)
r = RAG()
r.build_from_dataframe(df, text_column="description" if "description" in df.columns else "type", id_column="incident_id")
print("Built embeddings and FAISS index at DATA/embeddings/")
