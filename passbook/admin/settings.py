"""passbook admin settings"""

MIDDLEWARE = [
    'passbook.admin.middleware.impersonate',
]
