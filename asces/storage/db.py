from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

class Database:
    def __init__(self, db_path: str):
        self.db_url = f"sqlite:///{db_path}"
        self.engine = create_engine(self.db_url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def init_db(self):
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        return self.SessionLocal()
