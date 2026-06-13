"""CI guard: no hardcoded candidate IDs outside calibration.py.

P0 Gap 1 in GAPS.md documents that CALIBRATION_PREFERENCES in
calibration.py is the *only* permitted location for candidate-ID strings
in the ranking source code. That module carries full evidence
documentation (three-source unanimous labels, held-out crossover
validation). Any other .py file under src/redrob_ranker/ containing
CAND_XXXXXXX would indicate undocumented candidate-specific tuning that
is not defensible to a technical judge.

This test fails the CI build if such strings appear anywhere else.
"""

import re
from pathlib import Path


# Pattern matches CAND_ followed by 7 digits — the exact format used in
# the dataset and in calibration.py.
_CAND_ID_PATTERN = re.compile(r"CAND_\d{7}")

# The only file allowed to reference candidate IDs directly.
_ALLOWED_FILE = "calibration.py"


def test_no_hardcoded_candidate_ids_outside_calibration():
    """Fail if any source file outside calibration.py contains CAND_NNNNNNN."""
    src_root = Path(__file__).parents[1] / "src" / "redrob_ranker"
    violations: list[str] = []

    for py_file in sorted(src_root.rglob("*.py")):
        if py_file.name == _ALLOWED_FILE:
            continue
        text = py_file.read_text(encoding="utf-8")
        matches = _CAND_ID_PATTERN.findall(text)
        if matches:
            rel = py_file.relative_to(src_root.parent.parent)
            violations.append(f"{rel}: {matches[:5]}")  # show at most 5 matches

    assert not violations, (
        "Candidate IDs found outside calibration.py.\n"
        "Add justification to calibration.py or remove the ID-specific code:\n"
        + "\n".join(violations)
    )
