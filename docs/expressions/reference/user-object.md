# Passbook User Object

The User object has the following attributes:

 - `username`: User's username.
 - `email` User's email.
 - `name` User's display mame.
 - `is_staff` Boolean field if user is staff.
 - `is_active` Boolean field if user is active.
 - `date_joined` Date user joined/was created.
 - `password_change_date` Date password was last changed.
 - `attributes` Dynamic attributes.

## Examples

List all the User's group names:

```python
for group in user.groups.all():
    yield group.name
```
