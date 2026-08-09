from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_secret_scan_script_exists() -> None:
    assert (
        ROOT / "scripts/security/secret_scan.py"
    ).is_file()


def test_threat_model_exists() -> None:
    assert (
        ROOT / "docs/security/THREAT_MODEL_V3.md"
    ).is_file()


def test_network_policy_exists() -> None:
    assert (
        ROOT / "deploy/kubernetes/network-policy-phase18.yaml"
    ).is_file()
