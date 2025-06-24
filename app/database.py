from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./status.db")
engine = create_engine(DATABASE_URL)

def get_session():
  with Session(engine) as session:
    yield session

def create_DB():
  SQLModel.metadata.create_all(engine)
