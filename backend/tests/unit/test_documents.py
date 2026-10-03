from fastapi.testclient import TestClient

from app.models import DocumentChunk


def test_upload_document_persists_metadata_and_returns_response(client: TestClient) -> None:
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "documents@example.com",
            "full_name": "Document Owner",
            "password": "StrongPassword123!",
        },
    )
    token = register_response.json()["access_token"]

    response = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("policy.txt", b"hello world", "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "policy.txt"
    assert body["file_type"] == "txt"
    assert body["file_size"] == 11
    assert body["processing_status"] == "PROCESSED"
    assert body["id"] > 0


def test_uploaded_document_content_is_available_to_chat(client: TestClient) -> None:
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "document-chat@example.com",
            "full_name": "Document Chat User",
            "password": "StrongPassword123!",
        },
    )
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    document_text = (
        "The Northwind bridge project has an approved construction budget of 450000 dollars. "
        "The budget covers materials, labor, and inspection costs."
    )

    upload_response = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("northwind-budget.txt", document_text.encode(), "text/plain")},
    )
    assert upload_response.status_code == 201
    with client.app.state.session_factory() as session:
        stored_chunks = session.query(DocumentChunk).all()
    assert stored_chunks
    assert "450000" in stored_chunks[0].chunk_text

    conversation_response = client.post(
        "/api/conversations",
        headers=headers,
        json={"title": "Northwind budget"},
    )
    conversation_id = conversation_response.json()["id"]
    answer_response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        headers=headers,
        json={"question": "What is the approved budget for the Northwind bridge project?"},
    )

    assert answer_response.status_code == 200
    assistant = answer_response.json()["assistant"]
    assert "450000" in assistant["content"]
    assert assistant["citations"]
    assert assistant["citations"][0]["source"] == "northwind-budget.txt"
