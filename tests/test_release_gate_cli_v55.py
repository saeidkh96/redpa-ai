from pathlib import Path


def test_release_gate_cli_has_ci_exit_codes():
    source = Path("scripts/quality/release_gate.py").read_text(encoding="utf-8")
    assert 'if exc.code == 409' in source
    assert "return 1" in source
    assert "return 2" in source
    assert "/api/v1/evaluations/release-gates/ci-check" in source
