# Passbook User Object

The User object has the following attributes:

 - `username`: User's Username
 - `email` User's E-Mail
 - `name` User's Display Name
 - `is_staff` Boolean field if user is staff
 - `is_active` Boolean field if user is active
 - `date_joined` Date User joined/was created
 - `password_change_date` Date Password was last changed
 - `attributes` Dynamic Attributes

## Examples

List all the User's Group Names

```python
for group in user.groups.all():
    yield group.name
```
