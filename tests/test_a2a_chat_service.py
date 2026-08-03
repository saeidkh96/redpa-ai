from app.services.a2a_chat_service import A2AChatService


def test_extracts_artifact_text() -> None:
    task = {
        "artifacts": [
            {
                "parts": [
                    {
                        "text": "{\"status\":\"healthy\"}",
                    }
                ]
            }
        ]
    }

    result = A2AChatService._extract_artifact_text(task)

    assert '"status": "healthy"' in result


def test_extracts_nested_task_payload() -> None:
    result = A2AChatService._extract_task_payload(
        {
            "task": {
                "id": "task-1",
            }
        }
    )

    assert result["id"] == "task-1"
