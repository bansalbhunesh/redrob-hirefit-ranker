# VM Runtime Lab

Branch: `codex/100-score-gap-lab`  
Status: experimental branch evidence, not part of submitted `main`.

## Problem Found

On Docker Desktop with a constrained VM-style run, the main branch can
oversubscribe the process pool:

```bash
docker run --rm --cpus=2 --memory=16g ...
```

Inside the container, `os.cpu_count()` reports the host CPU count. The main
branch therefore auto-selects up to 8 scoring workers even when Docker grants
only 2 CPUs. On this machine, that made the full 100K VM-style run slow.

## Patch Tested

`src/redrob_ranker/pipeline.py` now detects Linux cgroup CPU quota from:

- `/sys/fs/cgroup/cpu.max` for cgroup v2
- `/sys/fs/cgroup/cpu/cpu.cfs_quota_us` and `cpu.cfs_period_us` for cgroup v1

Auto worker selection uses the smaller of `os.cpu_count()` and the detected
cgroup quota. Native runs without a quota still use the existing worker cap.

## Worker Detection Check

Constrained container:

```text
os_cpu_count 12
quota 2
workers 2
```

Unconstrained container:

```text
os_cpu_count 12
quota None
workers 8
```

## Benchmark Results

Same machine, same Docker Desktop setup, same mounted `candidates.jsonl`.

| Run | Main / before patch | Lab branch / after patch | Change |
|---|---:|---:|---:|
| Docker 20K, `--cpus=2 --memory=16g` | 36.5s pipeline | 29.7s pipeline | 18.6% faster |
| Docker 100K, `--cpus=2 --memory=16g` | 422.9s pipeline | 120.7s pipeline | 71.5% faster |

The patched full Docker output is byte-identical to `submission.csv`:

```text
SHA256 A2882CD2AE637DDE59244D9C5596BC529356C843281862CEEFA2F9DFB0DA9922
```

Validator with candidate membership passed:

```bash
python scripts/validate_submission.py artifacts/docker_lab_full_cgroup_patch.csv --candidates candidates.jsonl
```

## Interpretation

This branch is now materially better than `main` for constrained VM/container
execution. It keeps the golden output unchanged while making the clean
`--cpus=2` Docker path pass comfortably under 300 seconds on this machine.
