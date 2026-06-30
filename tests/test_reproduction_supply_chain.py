from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_production_dependencies_are_version_and_hash_pinned():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    logical_lines = requirements.replace("\\\n", " ").splitlines()
    dependencies = [
        line.strip()
        for line in logical_lines
        if line.strip() and not line.lstrip().startswith("#")
    ]

    assert len(dependencies) == 4
    for dependency in dependencies:
        assert "==" in dependency
        assert "--hash=sha256:" in dependency

    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "pip install --no-cache-dir --require-hashes -r requirements.txt" in dockerfile
