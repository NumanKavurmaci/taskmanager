import random
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, UserInfo

# Helper function to generate random usernames
def generate_username():
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(8))

# Helper function to generate random emails
def generate_email():
    letters = string.ascii_lowercase
    username = ''.join(random.choice(letters) for _ in range(8))
    domain = ''.join(random.choice(letters) for _ in range(5))
    return f"{username}@{domain}.com"

# Create the database engine
database_url = "sqlite:///task_manager.db"
engine = create_engine(database_url)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

# Append users with authority value 0
for _ in range(47):
    username = generate_username()
    email = generate_email()
    user = User(username=username, password='password', email=email, authority=0, is_active=True)
    session.add(user)

# Append users with authority value 1
for _ in range(2):
    username = generate_username()
    email = generate_email()
    user = User(username=username, password='password', email=email, authority=1, is_active=True)
    session.add(user)

# Commit the changes
session.commit()

# Retrieve the IDs of the newly created users
users = session.query(User).all()
user_ids = [user.id for user in users]

# Create rows in the user_info table for the new users with random values
for user_id in user_ids:
    full_name = "John Doe"  # Replace with random full names
    age = random.randint(18, 60)
    address = "123 Main Street"  # Replace with random addresses
    phone_number = "123-456-7890"  # Replace with random phone numbers
    department = "IT"  # Replace with random departments
    user_info = UserInfo(
        full_name=full_name,
        age=age,
        address=address,
        phone_number=phone_number,
        department=department,
        user_id=user_id
    )
    session.add(user_info)

# Commit the changes to the user_info table
session.commit()
