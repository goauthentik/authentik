-   `user`: The current user. This may be `None` if there is no contextual user. See [User](../user-group/user/user_ref.md#object-properties).

Example:

```python
return {
  "custom_attribute": request.user.attributes.get("custom_attribute", "default"),
}
```
