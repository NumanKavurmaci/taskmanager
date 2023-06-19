Overall features
1.	User Registration and Authentication: Allow users to create an account and log in securely to access their tasks and settings. 
2.	Task Creation: Enable users to create new tasks by providing a title, description, due date, priority level, and any other relevant information. 
3.	Task Assignment: Allow users to assign tasks to themselves or other team members, providing a way to delegate responsibilities.
 4.	Task Tracking: Provide a way for users to track the progress of their tasks, such as marking tasks as "in progress," "completed," or "pending." 5.	Task Prioritization: Allow users to set priority levels for tasks, such as high, medium, or low, to help them focus on critical tasks. 
6.	Task Due Dates and Reminders: Enable users to set due dates for tasks and send reminders or notifications to ensure timely completion. 
7.	Task Categorization and Labels: Provide options to categorize tasks into different categories or projects, and allow users to add labels or tags to organize tasks effectively. 
8.	Task Comments and Discussions: Allow users to add comments or notes to tasks, facilitating collaboration and communication among team members. 
9.	Task Filtering and Sorting: Implement filters and sorting options to help users find specific tasks based on criteria such as due date, priority, or category. 
10.	Task Search: Provide a search functionality to allow users to search for specific tasks using keywords or filters. 
11.	Notifications and Alerts: Send notifications or alerts to users for upcoming due dates, task assignments, or important updates. 
Libraries
1.	Flask: Flask is a lightweight web framework for Python that provides the basic infrastructure and tools for building web applications. It handles routing, request handling, and templating.
2.	SQLAlchemy: SQLAlchemy is a powerful SQL toolkit and Object-Relational Mapping (ORM) library. It provides a high-level, Pythonic interface for interacting with databases. SQLAlchemy makes it easier to work with databases, define database models, and perform database operations.
3.	Flask-WTF: Flask-WTF is an extension for Flask that integrates with WTForms, a flexible form handling library. It simplifies form validation, rendering, and submission handling in Flask applications.
4.	Passlib: Passlib is a password hashing library for Python. It provides secure password hashing algorithms and utilities for password hashing, verification, and other password-related operations.
5.	Flask-Login: Flask-Login is an extension that manages user authentication and session management in Flask applications. It provides functionality for handling user logins, sessions, and user authentication management.
6.	Flask-Bcrypt: Flask-Bcrypt is an extension that integrates the bcrypt password hashing algorithm with Flask. It simplifies the process of securely hashing and verifying passwords using bcrypt.

Database tables:
Databases listed below are in same database file and they are stored as tables.
1.	User Database: This database would store information about the users of the tool, including their usernames, passwords, email addresses, and other relevant user details.
2.	Task Database: This database would store information about the tasks in the system, such as task titles, descriptions, due dates, priorities, statuses, assigned users, and any other relevant task-related data.
3.	Project Database: If your task management tool supports multiple projects, you may need a separate database to store project-specific information, such as project names, descriptions, start dates, end dates, and other project-related data.
4.	Comment Database: If your task management tool allows users to comment on tasks or have discussions related to tasks, you may need a separate database to store comments, including the comment content, timestamps, and the associated task or project.
5.	Notification Database: If your task management tool has a notification system, you may need a database to store notification data, such as notifications sent to users, timestamps, notification types, and any other relevant notification information.
