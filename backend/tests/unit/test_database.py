from app.core.config import Settings
from app.db.session import create_session_factory
from app.models import Conversation, Document, DocumentChunk, Message, User


def make(**env: str) -> Settings:
    return Settings(_env_file=None, **env)


def test_database_url_is_configurable_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://db.example/app")
    assert Settings(_env_file=None).database_url == "postgresql+psycopg://db.example/app"


def test_sqlalchemy_models_can_be_persisted_in_sqlite() -> None:
    session_factory = create_session_factory("sqlite:///:memory:")

    with session_factory() as session:
        user = User(email="alice@example.com", full_name="Alice Example", hashed_password="secret")
        document = Document(
            user=user,
            filename="hr-policy.pdf",
            file_type="pdf",
            file_size=2048,
            processing_status="UPLOADED",
        )
        chunk = DocumentChunk(
            document=document,
            chunk_text="employee leave is 21 days",
            chunk_index=0,
            page_number=14,
            chunk_metadata={"source": "hr-policy.pdf"},
        )
        conversation = Conversation(user=user, title="Leave policy")
        message = Message(conversation=conversation, role="user", content="How many leave days?")

        session.add_all([user, document, chunk, conversation, message])
        session.commit()

        saved = session.get(User, user.id)
        assert saved is not None
        assert saved.email == "alice@example.com"
        assert len(saved.documents) == 1
        assert saved.documents[0].chunks[0].chunk_text == "employee leave is 21 days"
        assert conversation.messages[0].content == "How many leave days?"
