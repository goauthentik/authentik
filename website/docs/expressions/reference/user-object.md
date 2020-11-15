---
title: User Object
---

The User object has the following attributes:

-   `username`: User's username.
-   `email` User's email.
-   `name` User's display name.
-   `is_staff` Boolean field if user is staff.
-   `is_active` Boolean field if user is active.
-   `date_joined` Date user joined/was created.
-   `password_change_date` Date password was last changed.
-   `attributes` Dynamic attributes.
-   `group_attributes` Merged attributes of all groups the user is member of and the user's own attributes.
-   `pb_groups` This is a queryset of all the user's groups.

    You can do additional filtering like `user.pb_groups.filter(name__startswith='test')`, see [here](https://docs.djangoproject.com/en/3.1/ref/models/querysets/#id4)

    To get the name of all groups, you can do `[group.name for group in user.pb_groups.all()]`

## Examples

List all the User's group names:

```python
for group in user.pb_groups.all():
    yield group.name
```
