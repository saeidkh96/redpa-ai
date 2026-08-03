from pathlib import Path


def test_finalize_workflow_status_is_explicitly_cast() -> None:
    repository = (
        Path(__file__).resolve().parents[1]
        / "backend"
        / "app"
        / "distributed_durable"
        / "repository.py"
    )

    text = repository.read_text(
        encoding="utf-8",
    )

    assert "status = $2::varchar," in text
    assert (
        "WHEN $2::varchar IN "
        "('completed', 'partial', 'failed')"
    ) in text
