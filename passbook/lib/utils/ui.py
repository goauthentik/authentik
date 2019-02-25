"""passbook UI utils"""

def human_list(_list) -> str:
    """Convert a list of items into 'a, b or c'"""
    last_item = _list.pop()
    result = ', '.join(_list)
    return '%s or %s' % (result, last_item)
