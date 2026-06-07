"""HuggingFace Space demo for <=100 candidate samples."""

from __future__ import annotations

import tempfile
from pathlib import Path

import gradio as gr
import pandas as pd

from redrob_ranker.pipeline import RankerConfig, run_ranking


def rank_sample(file_obj):
    if file_obj is None:
        return None, "Upload sample_candidates.json or a small JSONL file."
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        in_path = base / Path(file_obj.name).name
        out_path = base / "ranked_candidates.csv"
        in_path.write_bytes(Path(file_obj.name).read_bytes())
        result = run_ranking(
            in_path,
            out_path,
            RankerConfig(top_k=100, candidate_pool_size=200, max_candidates=100),
        )
        df = pd.read_csv(out_path)
        return df, f"Ranked {len(df)} rows from {result.loaded_count} candidates."


with gr.Blocks(title="Redrob Candidate Ranker") as demo:
    gr.Markdown("# Redrob Candidate Ranker")
    gr.Markdown(
        "Upload a small candidate sample. The full challenge run is reproduced with "
        "`python rank.py --candidates ./candidates.jsonl --out ./submission.csv`."
    )
    upload = gr.File(label="Candidate JSON / JSONL sample", file_types=[".json", ".jsonl", ".gz"])
    run = gr.Button("Rank sample")
    table = gr.Dataframe(label="Ranked candidates")
    status = gr.Textbox(label="Status")
    run.click(rank_sample, inputs=upload, outputs=[table, status])


if __name__ == "__main__":
    demo.launch()

