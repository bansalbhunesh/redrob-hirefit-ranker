# Second-Layer Gap Closure Pack

This lab branch adds a safe version of the proposed "universal hiring intelligence"
second layer.

The attached draft script had the right ambition, but it made one dangerous claim:
it called deterministic synthetic labels "blind." That would be an overclaim. This
repo version separates the artifacts cleanly:

- `blind_annotation_pack.jsonl`: label-free rows for independent human or LLM judging.
- `annotation_sampling_key.jsonl`: sampling metadata; keep away from judges.
- `proxy_labels.jsonl`: deterministic development labels only.
- `pairwise_proxy_labels.jsonl`: deterministic pairwise development labels only.
- `hard_negative_proxy.jsonl`: trap and weak-fit rows for stress testing.
- `role_family_rubrics.json`: AI, backend, DevOps, data/BI, and search rubrics.
- `no_peeking_eval_protocol.json`: frozen-eval rules.
- `external_dataset_inventory.json`: downloaded public dataset provenance.

The generator never writes `submission.csv`.

## Why This Exists

The previous gap was not "no extra data." The real gap was lack of a disciplined
second layer:

- role-specific evaluation beyond the original AI JD;
- hard-negative and keyword-stuffer stress rows;
- pairwise preference labels for ranking sanity checks;
- a clean protocol for future blind labels;
- public-data provenance without pretending public data is the hidden Redrob test.

This script creates that layer without corrupting the frozen submission artifact.

## Commands

Demo pack:

```powershell
python scripts\generate_second_layer_pack.py --candidates demo_sample.jsonl --out-dir artifacts\second_layer_pack_demo --sample-size 50 --pair-count 100
```

Full 100k candidate pack:

```powershell
python scripts\generate_second_layer_pack.py --candidates C:\Users\bhune\india-runs\candidates.jsonl --out-dir artifacts\second_layer_pack_100k --sample-size 1000 --pair-count 1500
```

The generated `artifacts/` directory is intentionally ignored by git. Commit the
generator, tests, and docs; do not commit the candidate pool or generated packs.

## Latest Local Result

On the full 100k candidate pool, the generator produced:

- 1000 label-free annotation rows;
- 1000 deterministic proxy-label rows;
- 1490 pairwise proxy rows;
- 32 hard-negative rows;
- 5 role families: AI/ML, backend, DevOps/cloud, data/BI, and search relevance;
- external inventory covering 20 downloaded public-data sources, about 1477.2 MB.

After optimization, the full 100k generation completed locally in 154.2 seconds.

## What This Closes

This closes the local tooling gap for multi-JD generalization and future blind
evaluation. It gives the repo a credible annotation pack and protocol instead of
hand-wavy claims.

It does not magically create official hidden labels. A real 95+ proof still needs
independent judges to annotate `blind_annotation_pack.jsonl`, then a frozen report
computed without tuning on those labels.
