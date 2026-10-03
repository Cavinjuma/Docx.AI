from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import create_access_token
from app.main import create_app
from app.models import Document, DocumentChunk, User


def test_conversation_api_tracks_questions_and_citations() -> None:
    settings = Settings(_env_file=None, database_url="sqlite:///:memory:")
    app = create_app(settings)

    with app.state.session_factory() as session:
        user = User(email="chat@example.com", full_name="Chat User", hashed_password="hashed")
        session.add(user)
        session.commit()
        session.refresh(user)

        document = Document(
            user_id=user.id,
            filename="policy.txt",
            file_type="txt",
            file_size=120,
            processing_status="UPLOADED",
        )
        session.add(document)
        session.commit()
        session.refresh(document)

        session.add(
            DocumentChunk(
                document_id=document.id,
                chunk_text="The employee leave policy allows 21 paid vacation days each year.",
                chunk_index=0,
                page_number=1,
                chunk_metadata={"source": "policy.txt"},
            )
        )
        session.commit()

    token = create_access_token(str(user.id))
    client = TestClient(app)

    create_response = client.post(
        "/api/conversations",
        json={"title": "Leave policy"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 201
    conversation_id = create_response.json()["id"]

    message_response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"question": "How many leave days does the policy allow?"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert message_response.status_code == 200
    payload = message_response.json()
    assert "21" in payload["assistant"]["content"]
    assert payload["assistant"]["citations"]
    assert any("21 paid vacation days" in citation["text"] for citation in payload["assistant"]["citations"])
