from sqlalchemy import Column, ForeignKey, Integer, String, Date, Boolean, DateTime, Table, event
from sqlalchemy.orm import relationship, declarative_base, object_session
from sqlalchemy.orm.attributes import set_committed_value
from flask_login import UserMixin
from datetime import datetime, date
from helper import calculate_user_task_priority

"""import logging
import sys

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger('sqlalchemy.engine').addHandler(handler)
"""

Base = declarative_base()
today = date.today()

user_task_association = Table(
    'user_task_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('task_id', Integer, ForeignKey('tasks.id'), primary_key=True)
)

task_notification_association = Table(
    'task_notification_association',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id')),
    Column('notification_id', Integer, ForeignKey('notifications.id'))
)

user_notification_association = Table(
    'user_notification_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('notification_id', Integer, ForeignKey('notifications.id'))
)
project_task_association = Table(
    'project_task_association',
    Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True),
    Column('task_id', Integer, ForeignKey('tasks.id'), primary_key=True)
)
team_user_association = Table(
    'team_user_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('team_id', Integer, ForeignKey('teams.id')),
)
team_task_association = Table(
    'team_task_association',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id')),
    Column('team_id', Integer, ForeignKey('teams.id'))
)
project_team_association = Table(
    'project_team_association',
    Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True),
    Column('team_id', Integer, ForeignKey('teams.id'), primary_key=True)
)

class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    authority = Column(Integer)
    is_active = Column(Boolean, default=True)
    date_joined = Column(DateTime, default=datetime.utcnow)

    task_number = Column(Integer, default=0)
    task_priority = Column(Integer, default=0)
    completed_task_number = Column(Integer, default=0)
    completed_task_priority = Column(Integer, default=0)

    assigned_teams = relationship("Team", secondary=team_user_association, back_populates="team_members")
    assigned_tasks = relationship('Task', secondary=user_task_association, back_populates='assigned_users')
    user_info = relationship("UserInfo", uselist=False, back_populates="user")
    projects = relationship("Project", back_populates="user")
    received_notifications = relationship(
        'Notification',
        secondary=user_notification_association,
        backref='users_received'
    )

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.email}>'


class UserInfo(Base):
    __tablename__ = "user_info"
    id = Column(Integer, primary_key=True)
    user = relationship("User", back_populates="user_info")
    user_id = Column(Integer, ForeignKey("users.id"))

    full_name = Column(String(100))
    age = Column(Integer)
    address = Column(String(200))
    phone_number = Column(String(20))
    department = Column(String(50))


class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    user = relationship('User', back_populates='projects')
    tasks = relationship("Task", secondary=project_task_association,back_populates ="associated_project")
    assigned_teams = relationship('Team', secondary=project_team_association,back_populates="assigned_project")
    def __init__(self, name, user, description, tasks=None):
        self.name = name
        self.user = user
        self.description = description
        if tasks is not None:
            self.tasks = tasks


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    due_date = Column(Date)
    priority = Column(Integer)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    tags = Column(String)

    assigned_teams = relationship('Team', secondary=team_task_association, back_populates='assigned_tasks')
    assigned_users = relationship('User', secondary=user_task_association, back_populates='assigned_tasks')
    comments = relationship("Comment", backref="task")
    notifications = relationship('Notification', secondary=task_notification_association)
    attachments = relationship("Attachment", backref="task")
    associated_project = relationship("Project", secondary=project_task_association, back_populates="tasks")

    def __init__(self, title, description, due_date, priority, status, created_by, tags):
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority
        self.status = status
        self.created_by = created_by
        self.tags = tags

    def days_left(self):
        today = date.today()
        delta = self.due_date - today
        return delta.days



class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    timestamp = Column(String)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    author = Column(String, nullable=False)

    def __init__(self, content, author, task,timestamp=None):
        self.content = content
        self.author = author
        self.task = task
        if timestamp is not None:
            self.timestamp = timestamp


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    task_id = Column(Integer, ForeignKey('tasks.id'))

    def __init__(self, task, content):
        self.content = content
        self.task = task

class Attachment(Base):
    __tablename__ = 'attachments'

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    filepath = Column(String)
    task_id = Column(Integer, ForeignKey('tasks.id'))

    def __init__(self, filename, filepath):
        self.filename = filename
        self.filepath = filepath
class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)

    team_members = relationship("User", secondary=team_user_association, back_populates="assigned_teams")
    assigned_tasks = relationship("Task", secondary=team_task_association, back_populates="assigned_teams")
    roles = relationship("TeamMemberRole", backref="team", cascade="all, delete-orphan")
    assigned_project=relationship('Project', secondary=project_team_association,back_populates="assigned_teams")

    def __init__(self, name, description,team_members=None):
        self.name = name
        self.description = description
        if team_members is not None:
            self.team_members = team_members


class TeamMemberRole(Base):
    __tablename__ = 'team_member_roles'

    id = Column(Integer, primary_key=True)
    role = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey('users.id'))
    team_id = Column(Integer, ForeignKey('teams.id'))

