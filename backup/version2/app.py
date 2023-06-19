import re
import os

from datetime import datetime, timedelta

from sqlalchemy import or_ , and_
from sqlalchemy.orm import joinedload

from flask import Flask, render_template, redirect, request, flash, jsonify,g
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from flask_bcrypt import Bcrypt

from models import *
from database import init_database

# Configure Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_manager.db'
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Decorator to initialize the session before each request
@app.before_request
def before_request():
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
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Load the logged-in user
@login_manager.user_loader
def load_user(user_id):
    return session.query(User).get(int(user_id))
# Define the check_task_due_dates function

@app.route('/')
@login_required
def index():
    user = current_user

    tasks = session.query(Task).filter(Task.assigned_users.contains(user)).all()
    projects = user.projects
    comments = session.query(Comment).filter(Comment.task_id.in_(task.id for task in tasks)).all()
    notifications = user.received_notifications
    print(notifications)  # Print the notifications to the console for debugging

    return render_template('index.html', user=user, tasks=tasks, projects=projects, comments=comments, notifications=notifications)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Get username, password, confirmation, email, task, and authority from form
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()
        confirmation = request.form.get("confirmation").strip()
        email = request.form.get("email").strip()
        task = request.form.get("task").strip()
        authority = bool(request.form.get("authority"))

        # Store the input values in a dictionary to pass to the template
        input_values = {
            "username": username,
            "email": email,
            "task": task,
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
        new_user_info= UserInfo(full_name="Name ", age= None, address="address", phone_number="phone number", department=task,)
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

# Define the route for /show_tasks
@app.route('/show_tasks')
@login_required
def show_tasks():
    # Fetch all tasks from the database or any data source
    tasks = session.query(Task).all()

    # Render the show_tasks.html template and pass the tasks to it
    return render_template('show_tasks.html', tasks=tasks)

@app.route('/create_task', methods=['GET', 'POST'])
@login_required
def create_task():
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
            tags=tags  # Assign the tags to the new task
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
    print("function start:")
    print("User:", user)
    print("User Info:", user_info)
    if not user_info:
        # Create a new UserInfo record if it doesn't exist
        user_info = UserInfo()
        user_info.user_id = user.id
        session.add(user_info)
        session.commit()
        print("new user info created")
        print("function start:")
        print("User:", user)
        print("User Info:", user_info)

    if request.method == 'POST':
        # Update user_info details based on the form submission
        user_info.full_name = request.form.get('full_name')
        user_info.age = int(request.form.get('age'))
        user_info.address = request.form.get('address')
        user_info.phone_number = request.form.get('phone_number')
        user_info.department = request.form.get('department')

        session.commit()
        flash('User information updated successfully!', 'success')
        print("method=POST")
        print("User:", user)
        print("User Info:", user_info)
        return redirect('/user_info')
    print("method=GET")
    print("User:", user)
    print("User Info:", user_info)
    return render_template('user_info.html', user=user, user_info=user_info)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route("/show_workers")
@login_required
def show_workers():
    # Logic to retrieve worker information
    all_users = session.query(User).all()
    return render_template('show_workers.html', users=all_users)



@app.route('/manage_workers_user_info/<int:user_id>', methods=['GET', 'POST'])
@login_required
def manage_workers_user_info(user_id):
    if not current_user.authority == 1:
        return "Access Denied"

    user_info = session.query(UserInfo).get(user_id)
    if user_info is None:
        return "Worker not found"

    if request.method == 'POST':
        # Process the form data and update the worker's information
        user_info.full_name = request.form.get('full_name')
        user_info.age = int(request.form.get('age'))
        user_info.address = request.form.get('address')
        user_info.phone_number = request.form.get('phone_number')
        user_info.department = request.form.get('department')
        print("POST METHOD EXECUTED")
        print(f"full name={user_info.full_name}")
        print(f"age={user_info.age }")
        print(f"address={user_info.address}")
        print(f"phone_number={user_info.phone_number }")
        print(f"department={user_info.department}")

        session.commit()
        return redirect("/")
    print("GET METHOD EXECUTED")
    print("POST METHOD EXECUTED")
    print(f"full name={user_info.full_name}")
    print(f"age={user_info.age}")
    print(f"address={user_info.address}")
    print(f"phone_number={user_info.phone_number}")
    print(f"department={user_info.department}")

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
            # Append the user to the task's workers list
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


@app.route("/notifications")
@login_required
def notifications():
    user = current_user  # Assuming you have the current_user object from Flask-Login
    print("/notifications has happened")
    print(f"current user={user.id}")
    # Retrieve notifications associated with the current user
    notifications = user.received_notifications
    print(f"notificaitons={notifications}")
    notification_data = [{'content': n.content} for n in notifications]
    print(f"notification_data={notification_data}")
    return jsonify(notification_data)


@app.route('/create_notifications', methods=['POST'])
def create_notifications():
    data = request.get_json()
    print("create notification has happened")
    if 'user_id' in data and 'message' in data:
        user_id = data['user_id']
        content = data['message']

        print(f"Received data - user_id: {user_id}, message: {content}")  # Debugging line

        # Check if the user exists
        user = session.query(User).get(user_id)
        print(f"user={user}")
        if user:
            # Create a new notification
            notification = Notification(user=user, content=content)
            session.add(notification)
            session.commit()

            print("Notification created successfully")  # Debugging line

            return jsonify({'success': True, 'message': 'Notification created successfully.'})

    print("Invalid data")  # Debugging line
    return jsonify({'success': False, 'message': 'Invalid data.'})

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

        # Retrieve the task details based on the selected task ID
        selected_task = session.query(Task).options(joinedload(Task.assigned_users)).get(task_id)
        tasks = session.query(Task).all()

        # Access the authority value of the current user
        user_authority = current_user.authority

        return render_template('task.html', tasks=tasks, selected_task=selected_task, user_authority=user_authority)
    else:
        tasks = session.query(Task).all()
        return render_template('task.html', tasks=tasks, selected_task=None)
