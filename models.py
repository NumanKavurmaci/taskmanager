from sqlalchemy import Column, ForeignKey, Integer, String, Date, Boolean, DateTime, Table
from sqlalchemy.orm import relationship, declarative_base
from flask_login import UserMixin
from datetime import datetime, date

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

class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    authority = Column(Integer)
    is_active = Column(Boolean, default=True)

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
    full_name = Column(String(100))
    age = Column(Integer)
    address = Column(String(200))
    phone_number = Column(String(20))
    department = Column(String(50))
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="user_info")


class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    user = relationship('User', back_populates='projects')
    tasks = relationship("Task", secondary=project_task_association,backref="associated_project")

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

    project_id = Column(Integer, ForeignKey('projects.id'))
    assigned_users = relationship('User', secondary=user_task_association, backref='tasks')
    comments = relationship("Comment", backref="task")
    notifications = relationship('Notification', secondary=task_notification_association)

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
