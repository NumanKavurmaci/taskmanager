def calculate_user_task_priority(priority):
    if priority == 'high':
        return 3
    elif priority == 'medium':
        return 2
    elif priority == 'low':
        return 1
    else:
        return 0  # Default value if priority is not recognized
