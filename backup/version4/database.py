from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Import all your models individually
from models import User, UserInfo, Project, Task, Comment, Notification

session = None  # Global variable to store the session

def init_database(database_url):
    global session  # Access the global session variable
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    # Check if the session is already initialized
    if session is None:
        session = Session()

    return session
