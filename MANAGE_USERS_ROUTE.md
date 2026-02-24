# Manage Users Route Documentation

## Route: `/manage_users`

### Overview
The `/manage_users` route is an admin-only endpoint that provides a comprehensive view of all trainers and their assigned students in the NeuroLMS system.

### Access Requirements
- **Role Required**: `admin`
- **HTTP Method**: `GET`
- **Protected**: Yes - requires admin authentication

### Route Behavior

#### Admin Authorization
```python
if session.get("role") != "admin":
    return "Unauthorized Access"
```
Only users with `role = "admin"` can access this route.

#### Data Displayed

1. **All Trainers with Assigned Students**
   - Lists all users with `role = "trainer"`
   - Under each trainer, displays all users with:
     - `role = "user"` 
     - `trainer_id` matching that trainer's ID

2. **Unassigned Students**
   - Shows all users with `role = "user"`
   - Where `trainer_id` is NULL (not assigned to any trainer)

3. **Summary Statistics**
   - Total number of trainers
   - Total number of assigned students
   - Total number of unassigned students

### Template Structure

The route renders `manage_users.html` with the following data:

```python
trainer_data = [
    {
        'trainer': <User object with role="trainer">,
        'students': [<User objects with role="user" and trainer_id=trainer.id>]
    },
    ...
]

unassigned_users = [
    <User objects with role="user" and trainer_id=None>,
    ...
]
```

### Features

✅ **Responsive Design** - Mobile-friendly layout
✅ **Color-Coded Sections** - Trainers, assigned students, unassigned students
✅ **Statistical Summary** - Quick overview of assignments
✅ **Easy Management** - Instructions for using command-line tools to manage assignments

### Integration with Dashboard

The `/manage_users` link is available in the Admin Panel on the dashboard:
- Dashboard → Admin Panel → "Manage Users" button

### Related Commands

Users can manage trainers and students via `manage_users.py`:

```bash
# Assign a trainer to a user
python manage_users.py assign_trainer user@email.com trainer@email.com

# Remove trainer assignment
python manage_users.py unassign_trainer user@email.com

# View all students for a trainer
python manage_users.py get_students trainer@email.com

# List all users with relationships
python manage_users.py list
```

### Example Usage Flow

1. Admin logs in to the system
2. Navigates to Dashboard
3. Clicks "Manage Users" in the Admin Panel
4. Sees all trainers and their assigned students
5. Can use command-line tools to reassign trainers as needed

### Query Logic

The route queries:
1. All users with `role = "trainer"`:
   ```python
   trainers = User.query.filter_by(role="trainer").all()
   ```

2. For each trainer, get assigned students:
   ```python
   students = User.query.filter_by(trainer_id=trainer.id, role="user").all()
   ```

3. Get unassigned users:
   ```python
   unassigned_users = User.query.filter_by(trainer_id=None, role="user").all()
   ```

### Notes

- The route is read-only (GET only) for viewing purposes
- Trainer assignments are managed via the `manage_users.py` command-line tool
- Future enhancement: Could add inline assignment/reassignment functionality with POST routes
- The route supports unlimited trainers and students (scales well)

### Future Enhancements

Potential improvements for future versions:
- Inline trainer assignment (without CLI)
- Bulk trainer assignment
- Search/filter functionality
- Trainer performance metrics
- Student progress tracking per trainer