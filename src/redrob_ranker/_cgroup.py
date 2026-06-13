"""Shared cgroup CPU-quota helper.

Both ``pipeline.py`` and ``retrieval.py`` need to cap worker counts to the
cgroup-advertised CPU quota when running inside Docker Desktop or a CI
runner that reports more CPUs via ``os.cpu_count()`` than the container
is actually allowed to use.

This module is the single authoritative implementation so the two callers
stay in sync and the logic can be tested in one place.

Supported cgroup versions
--------------------------
v2: ``/sys/fs/cgroup/cpu.max``  (quota_us period_us on one line)
v1: ``/sys/fs/cgroup/cpu/cpu.cfs_quota_us`` + ``cpu.cfs_period_us``

Returns ``None`` on Windows / macOS / unconstrained Linux containers
(i.e. when the cgroup files are absent or the quota is "max").
"""

from __future__ import annotations

from pathlib import Path


def cgroup_cpu_quota_count() -> int | None:
    """Return the cgroup CPU quota as whole cores, or ``None`` if unconstrained.

    Result is ``max(1, quota_us // period_us)`` so a fractional quota
    (e.g. ``--cpus=1.5``) rounds down to 1 rather than 0.
    """
    # ── cgroupv2 (/sys/fs/cgroup/cpu.max) ─────────────────────────────────
    cpu_max = Path("/sys/fs/cgroup/cpu.max")
    try:
        parts = cpu_max.read_text(encoding="utf-8").strip().split()
    except OSError:
        parts = []
    if len(parts) >= 2 and parts[0] != "max":
        try:
            quota = int(parts[0])
            period = int(parts[1])
        except ValueError:
            quota = period = 0
        if quota > 0 and period > 0:
            return max(1, quota // period)

    # ── cgroupv1 (cpu.cfs_quota_us / cpu.cfs_period_us) ───────────────────
    quota_file = Path("/sys/fs/cgroup/cpu/cpu.cfs_quota_us")
    period_file = Path("/sys/fs/cgroup/cpu/cpu.cfs_period_us")
    try:
        quota = int(quota_file.read_text(encoding="utf-8").strip())
        period = int(period_file.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None
    if quota > 0 and period > 0:
        return max(1, quota // period)
    return None
