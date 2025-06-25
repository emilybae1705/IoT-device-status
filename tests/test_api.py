import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
import os

from app.main import app
from app.database import get_session

load_dotenv()
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

def get_test_session():
  with Session(engine) as session:
    yield session
    
app.dependency_overrides[get_session] = get_test_session

@pytest.fixture
def client():
  SQLModel.metadata.create_all(engine)
  return TestClient(app)
