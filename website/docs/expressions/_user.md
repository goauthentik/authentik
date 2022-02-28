- `user`: The current user. This may be `None` if there is no contextual user. See ([User](../user-group/user.md#object-attributes))

Example:

```python
if not 'custom_attribute' in request.user.attributes:
  return {'custom_attribute': 'default'}

return {"custom_attribute": request.user.attributes['custom_attribute']}
```