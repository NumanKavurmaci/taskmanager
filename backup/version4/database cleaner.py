from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, UserInfo, Base

# Create the database engine and session
database_url = "sqlite:///task_manager.db"
engine = create_engine(database_url)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

# Delete all users except for user id = 1 and username = numan
session.query(User).filter(User.id != 1, User.username != 'numan').delete()
session.commit()

# Delete all user_info except for user id = 1
session.query(UserInfo).filter(UserInfo.user_id != 1).delete()
session.commit()

session.close()
