import re
import os

from datetime import datetime, timedelta
from helper import calculate_user_task_priority
from sqlalchemy.orm import joinedload,object_session
from sqlalchemy.orm.exc import StaleDataError

from flask import Flask, render_template, redirect, request, flash, jsonify, g, abort
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from flask_bcrypt import Bcrypt

from models import *
from database import init_database
import config

import matplotlib
matplotlib.use('agg')  # Use the "agg" backend
import matplotlib.pyplot as plt


import logging

logger = logging.getLogger(__name__)

# Configure Flask
app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config["TEMPLATES_AUTO_RELOAD"] = config.TEMPLATES_AUTO_RELOAD
app.use_static_for = True
app.static_folder = 'static'

app.add_url_rule('/charts/<path:filename>', endpoint='charts', view_func=app.send_static_file)


# Decorator to initialize the session before each request
@app.before_request
def before_request():
    """
    Initialize the database session before each request.
    """
    if not hasattr(g, 'session') or not g.session:
        session = init_database(app.config['SQLALCHEMY_DATABASE_URI'])
        g.session = session
        # Assign session to a global variable
        globals()['session'] = session

# Configure Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Configure Flask-Bcrypt
bcrypt = Bcrypt(app)


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    """
    Set response headers to ensure they are not cached.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Load the logged-in user
@login_manager.user_loader
def load_user(user_id):
    """
    Load the user object based on the given user ID.
    """

    return session.query(User).get(int(user_id))


@app.route('/')
@login_required
def index():
    """
    Render the index page with user-specific data.
    """

    user = current_user

    tasks = session.query(Task).filter(Task.assigned_users.contains(user)).all()
    projects = user.projects

    # Query the comments related to the user's tasks
    comments = session.query(Comment).filter(Comment.task_id.in_(task.id for task in tasks)).all()

    # Retrieve the user's received notifications
    notifications = user.received_notifications

    # Get the current time
    current_time = datetime.now()

    # Query the tasks with upcoming due dates
    upcoming_tasks = session.query(Task).filter(Task.due_date > current_time).all()

    # Generate new notifications for upcoming tasks
    new_notifications = []
    for task in upcoming_tasks:
        # Calculate the time remaining until the task's due date
        time_remaining = task.due_date - current_time.date()

        if time_remaining == timedelta(days=1):
            notification_content = f"Task '{task.title}' is due tomorrow!"
        elif time_remaining == timedelta(days=3):
            notification_content = f"Task '{task.title}' is due in 3 days."
        elif time_remaining == timedelta(days=7):
            notification_content = f"Task '{task.title}' is due in 7 days."
        else:
            notification_content = f"Task '{task.title}' is due on {task.due_date}."

        # Create a new notification object
        notification = Notification(task=task, content=notification_content)
        new_notifications.append(notification)

    # Add the new notifications to the user's existing notifications
    notifications.extend(new_notifications)

    # Persist the new notifications to the database
    session.add_all(new_notifications)
    session.commit()

    return render_template('index.html', tasks=tasks, projects=projects, comments=comments, notifications=notifications)

@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Handle user registration.
    """

    if request.method == "POST":
        # Get username, password, confirmation, email, task, and authority from form
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()
        confirmation = request.form.get("confirmation").strip()
        email = request.form.get("email").strip()
        authority = bool(request.form.get("authority"))

        # Store the input values in a dictionary to pass to the template
        input_values = {
            "username": username,
            "email": email,
            "authority": authority
        }

        # Ensure username, email, password, and confirmation were submitted
        if not username:
            flash("Username is required")
            return render_template("register.html", **input_values)

        if not email:
            flash("E-Mail is required")
            return render_template("register.html", **input_values)

        if not password or not confirmation:
            flash("Password and confirmation are required")
            return render_template("register.html", **input_values)

        # Ensure passwords match
        if password != confirmation:
            flash("Passwords do not match")
            return render_template("register.html", **input_values)

        # Check if the username already exists
        existing_user = session.query(User).filter(User.username == username).first()
        if existing_user:
            flash("Username already exists")
            return render_template("register.html", **input_values)

        # Ensure password meets complexity criteria
        if not re.search(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", password):
            flash("Password must be at least 8 characters long and contain at least one letter, one number, and one special character (@$!%*#?&).")
            return render_template("register.html", **input_values)

        # Hash the password using bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # Create a new user object
        new_user = User(username=username, password=hashed_password, email=email, authority=authority)
        new_user_info= UserInfo(full_name="Name ", age=None, address="address", phone_number="phone number", department=None)
        # Add the new user to the session
        session.add(new_user)
        session.commit()

        # Log in the new user
        login_user(new_user)

        # Clean the input values
        input_values = {}

        # Render a template or perform any desired action
        # (e.g., display a success message)
        return redirect("/login")

    # Render the registration form
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login.
    """

    if request.method == "POST":
        # Get username and password from form
        username = request.form.get("username")
        password = request.form.get("password")

        # Find user by username
        user = session.query(User).filter_by(username=username).first()

        if user and user.is_active:
            # Check if password is correct
            if bcrypt.check_password_hash(user.password, password):
                remember = request.form.get("remember")
                # Log in the user
                login_user(user, remember=remember)
                # Redirect to the dashboard or any desired page
                return redirect("/")
            else:
                flash("Invalid username or password")
        else:
            flash("Invalid username or password")

    return render_template("login.html")


@app.route('/show_tasks')
@login_required
def show_tasks():
    # Get the search parameters from the query string
    search_name = request.args.get('name')
    search_tags = request.args.get('tags')
    search_due_date = request.args.get('due_date')
    search_created_by = request.args.get('created_by')
    search_created_at = request.args.get('created_at')

    # Sort parameters from the query string
    sort_by = request.args.get('sort_by')

    # Fetch tasks based on search parameters from the database or any data source
    tasks = session.query(Task)
    if search_name:
        tasks = tasks.filter(Task.title.ilike(f"%{search_name}%"))

    if search_tags:
        tasks = tasks.filter(Task.tags.ilike(f"%{search_tags}%"))

    if search_due_date:
        tasks = tasks.filter(Task.due_date == search_due_date)

    if search_created_by:
        try:
            created_by_id = int(search_created_by)
            tasks = tasks.filter(Task.created_by == created_by_id)
        except ValueError:
            # Search for the user ID based on the provided name
            user = session.query(User).filter(User.username.ilike(f"%{search_created_by}%")).first()
            if user:
                tasks = tasks.filter(Task.created_by == user.id)
            else:
                flash("Invalid user ID or name")
                return redirect("/show_tasks")

    if search_created_at:
        tasks = tasks.filter(Task.created_at == search_created_at)

    # Apply sorting
    if sort_by:
        tasks = tasks.order_by(sort_by)

    tasks = tasks.all()
    # Create a dictionary to map user IDs to usernames
    creator_dict = {}
    users = session.query(User).all()
    for user in users:
        creator_dict[user.id] = user.username
    teams = {}
    for task in tasks:
        teams[task.id] = [team.name for team in task.assigned_teams]
    for task in tasks:
        print(f"{task.assigned_teams}")
    # Render the show_tasks.html template and pass the tasks to it
    return render_template('show_tasks.html', tasks=tasks, teams=teams, creator_dict=creator_dict)


@app.route('/create_task', methods=['GET', 'POST'])
@login_required
def create_task():
    """
    Handle task creation.
    """

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date_str = request.form['due_date']  # Get the date string from the form input

        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()  # Convert string to date object
        except ValueError:
            flash('Invalid due date format. Please use YYYY-MM-DD format.', 'error')
            return redirect('/create_task')  # Redirect back to the create task page to re-enter the date

        priority = request.form['priority']
        status = request.form['status']
        tags = request.form['tags']  # Get the tags from the form input

        # Debug print statements
        print("Current User:", current_user)
        print("Tags:", tags)

        # Ensure the user object has the 'id' attribute
        if hasattr(current_user, 'id'):
            user_id = current_user.id
            # Debug print statement
            print("Current User ID:", user_id)
        else:
            # If 'id' attribute is missing, handle the error appropriately
            return "User ID not found"

        new_task = Task(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            status=status,
            created_by=user_id,
            tags=tags,  # Assign the tags to the new task
        )

        session.add(new_task)
        session.commit()

        flash('Task created successfully!', 'success')
        return redirect('/show_tasks')
    else:
        return render_template('create_task.html')

# Route: Change Password
@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        # Find the current user
        user = session.query(User).get(current_user.id)

        # Check if the current password is correct
        if bcrypt.check_password_hash(user.password, current_password):
            # Ensure new password and confirmation are provided
            if new_password and confirmation:
                # Ensure new password and confirmation match
                if new_password == confirmation:
                    # Ensure password meets complexity criteria
                    if re.search(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", new_password):
                        # Update the user's password
                        user.password = bcrypt.generate_password_hash(new_password).decode("utf-8")
                        session.commit()
                        flash("Password changed successfully!", "success")
                        return redirect("/")
                    else:
                        flash("New password must be at least 8 characters long and contain at least one letter, one number, and one special character (@$!%*#?&).")
                else:
                    flash("New password and confirmation do not match")
            else:
                flash("New password and confirmation are required")
        else:
            flash("Current password is incorrect")

    return render_template("changepassword.html")

@app.route("/deactivate_account", methods=["GET", "POST"])
@login_required
def deactivate_user():
    if request.method == "POST":
        # Get current password from form
        current_password = request.form.get("current_password")

        # Verify the current password
        if bcrypt.check_password_hash(current_user.password, current_password):
            # Deactivate the user account
            current_user.is_active = False
            session.commit()
            flash("User account deactivated successfully! Please contact the administrator for reactivation.", "success")
            # Log out the user after deactivating the account
            logout_user()
            return redirect("/")
        else:
            flash("Incorrect current password")
            return redirect("/deactivate_account")

    return render_template("deactivate_account.html")

@app.route('/user_info', methods=['GET', 'POST'])
@login_required
def user_info():
    user = current_user
    user_info = session.query(UserInfo).filter_by(id=user.id).first()
    if not user_info:
        # Create a new UserInfo record if it doesn't exist
        user_info = UserInfo()
        user_info.user_id = user.id
        session.add(user_info)
        session.commit()

    if request.method == 'POST':
        # Get the form data
        full_name = request.form.get('full_name')
        age = request.form.get('age')
        address = request.form.get('address')
        phone_number = request.form.get('phone_number')
        department = request.form.get('department')

        # Check if any required field is empty
        if not all([full_name, age, address, phone_number, department]):
            flash('Please fill in all required fields.', 'error')
        else:
            try:
                # Update user_info details based on the form submission
                user_info.full_name = full_name
                user_info.age = int(age)
                user_info.address = address
                user_info.phone_number = phone_number
                user_info.department = department

                session.commit()
                flash('User information updated successfully!', 'success')
            except Exception as e:
                session.rollback()
                flash('An error occurred while updating user information.', 'error')
                # Log the error for debugging purposes
                print(f'Error: {str(e)}')

    return render_template('user_info.html', user=user, user_info=user_info)

@app.route('/logout')
@login_required
def logout():
    """
    Handle user logout.
    """
    logout_user()
    return redirect('/login')

@app.route("/show_workers")
@login_required
def show_workers():
    # Logic to retrieve worker information
    all_users = session.query(User).all()
    return render_template('show_workers.html', users=all_users)

@app.route('/manage_workers')
@login_required
def manage_workers():
    workers = session.query(User).all()
    return render_template('manage_workers.html', workers=workers)

@app.route('/manage_workers_user_info/<int:user_id>', methods=['GET', 'POST'])
@login_required
def manage_workers_user_info(user_id):
    if not current_user.authority == 1:
        return "Access Denied"

    user_info = session.query(UserInfo).get(user_id)
    if user_info is None:
        user_info = UserInfo(full_name=None, age=None, address=None, phone_number=None, department=None, user_id=user_id)
        session.add(user_info)
        session.commit()

    if request.method == 'POST':
        # Process the form data and update the worker's information
        user_info.full_name = request.form.get('full_name')
        user_info.age = int(request.form.get('age'))
        user_info.address = request.form.get('address')
        user_info.phone_number = request.form.get('phone_number')
        user_info.department = request.form.get('department')

        session.commit()
        return redirect("/")

    return render_template('manage_workers_user_info.html', user_info=user_info)

# Route for displaying the forgot password form and handling form submission
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        # Perform your logic to retrieve the user's account based on the provided email
        user = session.query(User).filter_by(email=email).first()

        if user:
            hashed_password=bcrypt.generate_password_hash("password").decode("utf-8")
            # Update the user's password in memory
            user.password = hashed_password

            # Redirect the user to a confirmation or success page
            return redirect('/login')
        else:
            # Handle the case where the email is not found or the user doesn't exist
            flash('email_not_found.html')

    # Render the forgot password form for GET requests
    return render_template('forgot_password.html')

@app.route('/append_workers', methods=['GET', 'POST'])
@login_required
def append_workers():
    if request.method == 'POST':
        # Get the form data
        task_id = request.form.get('task_id')
        user_id = request.form.get('worker_id')

        # Retrieve the task and user objects
        task = session.query(Task).get(task_id)
        user = session.query(User).get(user_id)

        if task and user:
            # Check if the user is already associated with the task
            if user in task.assigned_users:
                flash('User is already assigned to the task.')
                return redirect('/append_workers')

            # Append the user to the task's workers list
            user.task_number += 1
            user.task_priority += calculate_user_task_priority(task.priority)

            task.assigned_users.append(user)

            # Commit the changes to the database
            session.commit()

            flash('Worker appended to task successfully.', 'success')
            return redirect('/append_workers')
        else:
            flash('Invalid task or worker.', 'danger')
            return redirect('/append_workers')

    # Retrieve the list of tasks and users
    tasks = session.query(Task).all()
    users = session.query(User).all()

    for user in users:
        print(user.id)

    for task in tasks:
        if task is not None:  # Check if task is not None
            print(task.title)

    return render_template('append_workers.html', tasks=tasks, users=users)

@app.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        name = request.form['title']
        description = request.form['description']
        selected_task_ids = request.form.getlist('tasks')

        # Retrieve tasks based on the selected task IDs
        tasks = session.query(Task).filter(Task.id.in_(selected_task_ids)).all()

        # Create the project with the selected tasks
        project = Project(name=name, user=current_user, description=description)
        project.tasks = tasks

        session.add(project)
        session.commit()

        flash('Project created successfully.', 'success')
        return redirect('/projects')

    # Retrieve all tasks to display in the form
    tasks = session.query(Task).all()

    return render_template('create_project.html', tasks=tasks)


@app.route('/projects')
@login_required
def projects():
    projects = session.query(Project).all()
    return render_template('projects.html', projects=projects)


@app.route('/append_task_to_project', methods=['GET', 'POST'])
@login_required
def append_task_to_project():
    if request.method == 'POST':
        project_id = request.form['project_id']
        task_ids = request.form.getlist('task_ids')

        project = session.query(Project).get(project_id)

        if not project:
            flash('Project not found.', 'danger')
            return redirect('/projects')

        tasks = session.query(Task).filter(Task.id.in_(task_ids)).all()

        project.tasks.extend(tasks)
        session.commit()

        flash('Tasks appended to the project successfully.', 'success')
        return redirect('/projects')

    projects = session.query(Project).all()
    tasks = session.query(Task).all()

    return render_template('append_task_to_project.html', projects=projects, tasks=tasks)

@app.route('/show_task', methods=['GET', 'POST'])
@login_required
def show_task():
    if request.method == 'POST':
        task_id = request.form.get('task_id')
        comment_content = request.form.get('comment_content')

        # Retrieve the task details based on the selected task ID
        selected_task = session.query(Task).options(joinedload(Task.assigned_users)).get(task_id)
        tasks = session.query(Task).all()

        # Access the authority value of the current user
        user_authority = current_user.authority

        # Create a dictionary to store the creator details
        creator_dict = {}

        if selected_task and selected_task.created_by:
            creator_id = selected_task.created_by
            creator_user = session.query(User).get(creator_id)
            creator_dict = {
                'id': creator_user.id,
                'username': creator_user.username,
                'email': creator_user.email
            }

        # Update the task with the provided values
        if request.form.get('edit_title'):
            selected_task.title = request.form.get('edit_title')
            selected_task.description = request.form.get('edit_description')

            selected_due_date_str = request.form.get('edit_due_date')  # Get the due date string
            try:
                selected_due_date = datetime.strptime(selected_due_date_str, '%Y-%m-%d').date()  # Convert string to date object
                selected_task.due_date = selected_due_date
            except ValueError:
                flash('Invalid due date format. Please use YYYY-MM-DD format.', 'error')
                return redirect('/show_task')

            selected_task.priority = request.form.get('edit_priority')
            # Check if the status is being changed
            if request.form.get('edit_status') != selected_task.status:
                selected_task.status = request.form.get('edit_status')
                if selected_task.status == 'Completed':
                    current_user.completed_task_number += 1
                    print(f"priority= {selected_task.priority}")
                    print(f"calculate_user_task_priority(selected_task.status)={calculate_user_task_priority(selected_task.priority)}")
                    current_user.completed_task_priority += calculate_user_task_priority(selected_task.priority)
                    flash('Task completed successfully!', 'success')
                flash('Task Status Updated!')
                session.commit()

        # Add the new comment to the selected task
        if comment_content:
            author = current_user.username  # Set the author as the current user's username
            timestamp = datetime.utcnow()  # Get the current timestamp
            new_comment = Comment(content=comment_content, timestamp=timestamp, author=author, task=selected_task)
            session.add(new_comment)
            session.commit()

        return render_template('task.html', tasks=tasks, selected_task=selected_task, user_authority=user_authority, creator_dict=creator_dict)
    else:
        tasks = session.query(Task).all()
        return render_template('task.html', tasks=tasks, selected_task=None)

@app.route('/create_team', methods=['GET', 'POST'])
@login_required
def create_team():
    if request.method == 'POST':
        team_name = request.form.get('team_name')
        user_ids = request.form.getlist('users')
        description = request.form.get('team_description')  # Retrieve a single value
        print("user input:")
        print(f"team_name={team_name}")
        print(f"user_ids={user_ids}")
        print(f"description={description}")
        team_members = session.query(User).filter(User.id.in_(user_ids)).all()

        team = Team(name=team_name, description=description, team_members=team_members)

        # Retrieve roles for each team member
        roles = request.form.getlist('roles')
        for i, user_id in enumerate(user_ids):
            role = roles[i]
            user = session.query(User).get(user_id)
            if user:
                team_member_role = TeamMemberRole(role=role)
                team_member_role.user = user
                team_member_role.team = team
                session.add(team_member_role)

        session.add(team)
        session.commit()

        flash("Team successfully created!")
        return redirect('/teams')

    users = session.query(User).all()
    return render_template('create_team.html', users=users)

    users = session.query(User).all()
    return render_template('create_team.html', users=users)

@app.route('/teams')
@login_required
def teams():
    teams = session.query(Team).all()
    print(teams)

    for team in teams:
        print("Team Name:", team.name)
        print("Team Members:")
        for member in team.team_members:
            print(member.username)

    return render_template('teams.html', teams=teams)


@app.route('/edit_team/<int:team_id>', methods=['GET', 'POST'])
@login_required
def edit_team(team_id):
    if request.method == 'GET':
        team = session.query(Team).get(team_id)
        if team:
            print("Team:", team.name)
            return render_template('edit_team.html', team=team)
        else:
            flash('Team not found!')
            return redirect('/teams')

    if request.method == 'POST':
        member_id = request.form.get('member_id')
        new_role = request.form.get('role')

        team = session.query(Team).get(team_id)
        if team:
            print("Team:", team.name)
            member_role = None
            for user in team.team_members:
                if user.id == int(member_id):
                    member_role = user
                    break
            if member_role:
                member_role.role = new_role
                session.commit()
                flash('Member role updated successfully!')
            else:
                flash('Member not found in the team!')
        else:
            flash('Team not found!')

        # Update the team in the database
        team.name = request.form.get('team_name')
        team.description = request.form.get('team_description')
        session.commit()

        team = session.query(Team).get(team_id)  # Retrieve the updated team from the database
        if team:
            print("Updated Team:", team.name)
            return render_template('edit_team.html', team=team)
        else:
            flash('Team not found!')
            return redirect('/teams')

@app.route('/delete_team/<int:team_id>', methods=['POST'])
@login_required
def delete_team(team_id):
    team = session.query(Team).get(team_id)

    if team:
        try:
            session.refresh(team)  # Refresh the team object to synchronize it with the database
            session.delete(team)
            session.commit()
            flash("Team successfully deleted!")
        except StaleDataError:
            session.rollback()  # Roll back the transaction
            flash("Failed to delete team. Please try again.")

    else:
        flash("Team not found!")

    return redirect('/teams')

@app.route('/assign_tasks_to_teams', methods=['GET', 'POST'])
@login_required
def assign_tasks():
    if request.method == 'POST':
        # Retrieve the selected team ID and task ID from the form submission
        team_id = request.form.get('team_id')
        task_id = request.form.get('task_id')

        # Retrieve the team and task objects from the database
        team = session.query(Team).get(team_id)
        task = session.query(Task).get(task_id)
        # Validate the team and task IDs
        if not team or not task:
            flash('Invalid team or task selection.')
            return redirect('/assign_tasks_to_teams')

        if team and task:
            # Append the task to the team's assigned_tasks list
            team.assigned_tasks.append(task)
            for user in team.team_members:
                # Check if the user is already assigned to the task
                if task in user.assigned_tasks:
                    continue  # Skip this user

                task.assigned_users.append(user)
                # Update the task tracking attributes
                user.task_number += 1
                user.task_priority += calculate_user_task_priority(task.priority)

            session.commit()
            flash('Task assigned to the team successfully!')

        # Redirect to the task listing page or display a success message
        return redirect('/show_tasks')

    # If the request method is GET, render the assign_tasks.html template
    teams = session.query(Team).all()
    tasks = session.query(Task).all()

    return render_template('assign_tasks_to_teams.html', teams=teams, tasks=tasks)

@app.route('/assign_teams_to_projects', methods=['GET', 'POST'])
@login_required
def assign_teams_to_projects():
    if current_user.authority != 1:
        flash('You don\'t have the authority to access this page.')
        return redirect('/')

    if request.method == 'POST':
        # Get the form data
        # Get the form data
        # Get the form data
        team_id = request.form.get('team_id')
        project_id = request.form.get('project_id')

        # Retrieve the team and project objects
        team = session.query(Team).get(team_id)
        project = session.query(Project).get(project_id)
        print(f"choosen team={team.id}")
        print(f"choosen project={project.id}")
        if team and project:
            print(f"if team and project happened")
            # Get all tasks in the project
            tasks = session.query(Task).filter(Task.associated_project.any(id=project.id)).all()
            print(f"tasks={tasks}")

            # Check if the team is already assigned to the project
            if team in project.assigned_teams:
                flash('The team is already assigned to the project.')
                return redirect('/assign_teams_to_projects')

            # Assign users in the team to each task in the project
            for task in tasks:
                task.assigned_teams.append(team)
                for user in team.team_members:
                    # Check if the user is already assigned to the task
                    if user not in task.assigned_users:
                        # Append the user to the task's assigned users
                        task.assigned_users.append(user)
                        print(f"user={user.user_info.full_name} appended to task={task.title}")
                        print(f"current situation; task.assigned_users={task.assigned_users}")
                        # Update the user's task tracking attributes
                        user.task_number += 1
                        user.task_priority += calculate_user_task_priority(task.priority)
            # Append the team to the project's assigned teams
            project.assigned_teams.append(team)

            session.commit()
            flash('Teams assigned to the project successfully!')

        # Redirect to the appropriate page or display a success message
        return redirect('/assign_teams_to_projects')

    # If the request method is GET, render the assign_teams_to_projects.html template
    teams = session.query(Team).all()
    projects = session.query(Project).all()

    return render_template('assign_teams_to_projects.html', teams=teams, projects=projects)

@app.route("/worker_performance", methods=["GET", "POST"])
@login_required
def worker_performance():
    # Handle the form submission
    if request.method == "POST":
        sort_by = request.form.get("sort-by")
        filter_by = request.form.get("filter-by")

        users = session.query(User).join(User.user_info)

        if sort_by == "name":
            users = users.order_by(UserInfo.full_name)
        elif sort_by == "department":
            users = users.order_by(UserInfo.department)
        elif sort_by == "completion-rate":
            users = users.filter(User.task_number != 0).order_by(User.completed_task_number / User.task_number)
        else:
            # Handle the case when no valid sorting option is selected
            flash("Invalid sorting option.")
            return redirect("/worker_performance")

        if filter_by == "active":
            users = users.filter(User.is_active)
        elif filter_by == "inactive":
            users = users.filter(~User.is_active)
        elif filter_by != "all":
            users = users.filter(UserInfo.department == filter_by)

        # Get the unique departments of current users
        departments = session.query(UserInfo.department.distinct()).join(User).filter(User.is_active).all()
        department_options = [dept[0] for dept in departments]
        print(f"department_options={department_options}")

        # Pass the sorted and filtered users to the template for rendering
        return render_template("worker_performance.html", users=users, department_options=department_options)

    # Render the initial page with unsorted/unfiltered data
    users = session.query(User).all()
    departments = session.query(UserInfo.department.distinct()).join(User).filter(User.is_active).all()

    department_options = []
    department_options = [dept[0] for dept in departments]

    print(f"department_options={department_options}")

    # Pass the users and department options to the template for rendering
    return render_template("worker_performance.html", users=users, department_options=department_options)

@app.route("/worker_performance/graphs")
@login_required
def worker_performance_graphs():
    # Check if the current user has authority value 1
    if current_user.authority != 1:
        # Redirect or abort here if the user doesn't have the required authority
        # For example, you can redirect them to a different page or display an error message
        return "You do not have permission to access this page."
    # Retrieve the user data from the database
    users = session.query(User).all()

    # Prepare data for the chart
    departments = []
    completion_rates = []

    for user in users:
        departments.append(user.user_info.department)
        if user.task_number != 0:
            completion_rate = user.completed_task_number / user.task_number
        else:
            completion_rate = 0
        completion_rates.append(completion_rate)

    # Create the bar chart
    plt.bar(departments, completion_rates)
    plt.xlabel('Department')
    plt.ylabel('Completion Rate')
    plt.title('Worker Performance')

    # Create the charts directory if it doesn't exist
    chart_directory = os.path.join(app.static_folder, 'charts')
    if not os.path.exists(chart_directory):
        os.makedirs(chart_directory)

    # Save the chart to the charts directory
    chart_file = os.path.join(chart_directory, 'worker_performance_chart.png')
    plt.savefig(chart_file)

    # Pass the relative file path to the template for rendering
    chart_filename = 'charts/worker_performance_chart.png'

    # Render the template and pass the chart filename
    return render_template('worker_performance_graphs.html', chart_filename=chart_filename)

@app.route('/charts/<path:filename>')
def serve_chart(filename):
    return send_from_directory('static', filename)
