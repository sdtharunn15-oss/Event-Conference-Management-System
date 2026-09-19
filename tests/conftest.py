import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Import ALL models before create_all().
from app.models.user import User
from app.models.event import Event
from app.models.venue import Venue
from app.models.hall import Hall
from app.models.speaker import Speaker
from app.models.registration import Registration
from app.models.ticket import Ticket
from app.models.ticket_purchase import TicketPurchase
from app.models.payment import Payment
from app.models.session import Session
from app.models.speaker import Speaker


TEST_DATABASE_URL = "sqlite:///./test_event_conference.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Make app.database.SessionLocal point to the SAME
# database used by the tests.
#
# Some tests directly import SessionLocal instead
# of using the get_db dependency override.
import app.database as database_module

database_module.SessionLocal = TestingSessionLocal


@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """
    Create all database tables once before the test session.
    """

    Base.metadata.create_all(
        bind=engine
    )

    yield

    Base.metadata.drop_all(
        bind=engine
    )

    if os.path.exists("test_event_conference.db"):
        try:
            os.remove("test_event_conference.db")
        except PermissionError:
            pass


@pytest.fixture()
def db():
    """
    Provide a fresh database session for each test.
    """

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    """
    FastAPI test client using the same test database.
    """

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()