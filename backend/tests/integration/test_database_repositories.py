import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.models.identity import User
from app.database.models.trading import Strategy


@pytest.fixture(autouse=True)
def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(engine)


def test_user_repository_create_and_get(setup_db):
    from app.database.repositories.identity_repository import UserRepository

    user = User(username="repouser", email="repouser@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
    setup_db.add(user)
    setup_db.flush()

    repo = UserRepository(setup_db)
    fetched = repo.get(user.id)

    assert fetched is not None
    assert fetched.username == "repouser"


def test_strategy_repository_crud(setup_db):
    from app.database.repositories.trading_repository import StrategyRepository

    strategy = Strategy(name="TestStrategy", code="TEST_STRATEGY", version="1.0", strategy_type="trend_following", status="ACTIVE")
    setup_db.add(strategy)
    setup_db.flush()

    repo = StrategyRepository(setup_db)
    fetched = repo.get(strategy.id)
    assert fetched is not None
    assert fetched.name == "TestStrategy"

    strategy.status = "INACTIVE"
    updated = repo.update(strategy)
    assert updated is not None
    assert updated.status == "INACTIVE"
